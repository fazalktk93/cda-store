from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.template.loader import get_template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.dateparse import parse_date
import json
import io
from xhtml2pdf import pisa
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Vendor, StockItem, Issue, Receipt, Office
from .forms import VendorForm, StockItemForm, IssueForm, OfficeForm
from .forms import ReportSearchForm
from datetime import datetime


# Dashboard
@login_required
def dashboard(request):
    vendor_count = Vendor.objects.count()
    stock_count = StockItem.objects.count()
    issue_count = Issue.objects.count()

    low_stock_items = StockItem.objects.filter(quantity__lt=40)

    return render(request, 'store/dashboard.html', {
        'vendor_count': vendor_count,
        'stock_count': stock_count,
        'issue_count': issue_count,
        'low_stock_items': low_stock_items,
    })


# Vendor CRUD
@login_required
def vendor_list(request):
    vendors = Vendor.objects.all()
    return render(request, 'store/vendor_list.html', {'vendors': vendors})

@login_required
def vendor_create(request):
    form = VendorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('vendor_list')
    return render(request, 'store/vendor_form.html', {'form': form})

@login_required
def vendor_list(request):
    query = request.GET.get('q', '')
    vendors = Vendor.objects.all()
    if query:
        vendors = vendors.filter(Q(name__icontains=query) | Q(contact__icontains=query))
    return render(request, 'store/vendor_list.html', {'vendors': vendors})


def safe_parse_date(value):
    return parse_date(value) if isinstance(value, str) and value else None

@login_required
def vendor_detail(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    stock_items = StockItem.objects.filter(vendor=vendor)

    # Safe date parsing
    def safe_parse_date(value):
        return parse_date(value) if isinstance(value, str) and value else None

    start_date = safe_parse_date(request.GET.get('start'))
    end_date = safe_parse_date(request.GET.get('end'))

    if start_date and end_date:
        receipts = Receipt.objects.filter(
            stock_item__in=stock_items,
            date_received__range=(start_date, end_date)
        )
    else:
        receipts = Receipt.objects.filter(stock_item__in=stock_items)

    return render(request, 'store/vendor_detail.html', {
        'vendor': vendor,
        'receipts': receipts,
        'start': request.GET.get('start', ''),
        'end': request.GET.get('end', ''),
    })

# Stock CRUD
@login_required
def stock_list(request):
    grouped_receipts = (
        Receipt.objects
        .values('stock_item__name', 'voucher_number')  # Grouping keys
        .annotate(
            total_quantity=Sum('quantity_received'),
            unit_price=Avg('unit_price'),  # Assumes price is the same
            total_price=Sum(F('quantity_received') * F('unit_price'))
        )
        .order_by('-voucher_number')
    )

    return render(request, 'store/stock_list.html', {
        'grouped_receipts': grouped_receipts
    })

@login_required
def stock_create(request):
    form = StockItemForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        stock_item = form.save()

        # ✅ Auto-create a receipt if this is a new item
        Receipt.objects.create(
            stock_item=stock_item,
            quantity_received=stock_item.quantity,
            unit_price=stock_item.purchase_price,
            source='Initial Stock Entry'
        )

        return redirect('stock_list')  # or whatever your stock list view name is

    return render(request, 'store/stock_form.html', {'form': form})


# Issue Entry
@login_required
def issue_create(request):
    form = IssueForm(request.POST or None)
    stock_data = {str(item.id): item.quantity for item in StockItem.objects.all()}

    if request.method == 'POST' and form.is_valid():
        issue = form.save(commit=False)
        stock_item = issue.stock_item
        quantity_issued = issue.quantity_issued

        if stock_item.quantity >= quantity_issued:
            stock_item.quantity -= quantity_issued
            stock_item.save()
            issue.save()
            form = IssueForm()  # Clear the form
        else:
            form.add_error('quantity_issued', 'Not enough quantity in stock.')

    recent_issues = Issue.objects.order_by('-date_issued')[:5]
    return render(request, 'store/issue_form.html', {
        'form': form,
        'stock_data_json': json.dumps(stock_data),
        'recent_issues': recent_issues
    })

# PDF Report
@login_required
def report_pdf(request):
    query = request.GET.get('q', '')
    items = StockItem.objects.all()
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(vendor__name__icontains=query)
        )

    template = get_template('store/report_pdf.html')  # separate PDF-only layout
    html = template.render({'items': items})
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='filtered_report.pdf')

@login_required
def report_search(request):
    query = request.GET.get("q", "")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    include_issues = request.GET.get("include_issues") == "on"
    include_purchases = request.GET.get("include_purchases") == "on"
    show_vendor = request.GET.get("show_vendor") == "on"
    show_office = request.GET.get("show_office") == "on"

    results = []

    items = StockItem.objects.filter(name__icontains=query)

    for item in items:
        row = {
            'name': item.name,
            'unit': item.unit,
            'price': item.purchase_price,
            'quantity': item.quantity,
        }

        if show_vendor and item.vendor:
            row['vendor'] = item.vendor.name
        else:
            row['vendor'] = ''

        if include_purchases:
            receipts = item.receipt_set.all()
            if start_date:
                receipts = receipts.filter(date_received__gte=start_date)
            if end_date:
                receipts = receipts.filter(date_received__lte=end_date)
            for receipt in receipts:
                row_copy = row.copy()
                row_copy['quantity'] = receipt.quantity_received
                row_copy['date'] = receipt.date_received
                row_copy['type'] = 'Purchase'
                row_copy['office'] = ''
                results.append(row_copy)

        if include_issues:
            issues = item.issue_set.all()
            if start_date:
                issues = issues.filter(date_issued__gte=start_date)
            if end_date:
                issues = issues.filter(date_issued__lte=end_date)
            for issue in issues:
                row_copy = row.copy()
                row_copy['quantity'] = issue.quantity_issued
                row_copy['date'] = issue.date_issued
                row_copy['type'] = 'Issue'
                if show_office and issue.office:
                    row_copy['office'] = issue.office.name
                else:
                    row_copy['office'] = ''
                results.append(row_copy)

    return render(request, 'store/report_result.html', {
        'results': results,
        'show_vendor': show_vendor,
        'show_office': show_office
    })

@login_required
def report_view(request):
    show_vendor = 'show_vendor' in request.GET
    show_office = 'show_office' in request.GET
    include_receipts = 'include_receipts' in request.GET
    include_issues = 'include_issues' in request.GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    issues = Issue.objects.all()
    receipts = Receipt.objects.all()

    if start_date:
        issues = issues.filter(date_issued__gte=start_date)
        receipts = receipts.filter(date_received__gte=start_date)
    if end_date:
        issues = issues.filter(date_issued__lte=end_date)
        receipts = receipts.filter(date_received__lte=end_date)

    if 'export' in request.GET:
        template = get_template('store/report_pdf.html')
        html = template.render({
            'issues': issues if include_issues else [],
            'receipts': receipts if include_receipts else [],
            'show_vendor': show_vendor,
            'show_office': show_office,
        })
        buffer = io.BytesIO()
        pisa.CreatePDF(html, dest=buffer)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='filtered_report.pdf')

    return render(request, 'store/report.html', {
        'issues': issues if include_issues else [],
        'receipts': receipts if include_receipts else [],
        'show_vendor': show_vendor,
        'show_office': show_office,
    })

# ✅ Office Management Views
class OfficeListView(ListView):
    model = Office
    template_name = 'store/office_list.html'


class OfficeCreateView(CreateView):
    model = Office
    form_class = OfficeForm  # ✅ Use only form_class to avoid conflict
    template_name = 'store/office_form.html'
    success_url = reverse_lazy('office_list')
    
@login_required
def office_create(request):
    form = OfficeForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('office_list')
    return render(request, 'store/office_form.html', {'form': form})

@login_required
def report_form_view(request):
    return render(request, 'store/report_form.html')

@login_required
class IssueCreateView(CreateView):
    model = Issue
    form_class = IssueForm
    template_name = 'store/issue_form.html'
    success_url = None  # Remove this if you want to stay on the page

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data(form=self.form_class()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stock_data = {item.id: item.quantity for item in StockItem.objects.all()}
        context['stock_data_json'] = json.dumps(stock_data)
        context['issued_items'] = Issue.objects.select_related('stock_item', 'office').order_by('-date_issued')[:5]
        return context