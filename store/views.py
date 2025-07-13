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
from datetime import date
from django.db.models import Sum, Avg, F
from collections import defaultdict
from store.models import Receipt


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
    receipts = Receipt.objects.select_related('stock_item', 'stock_item__vendor').order_by('-date_received')

    grouped = defaultdict(list)
    for receipt in receipts:
        key = (receipt.voucher_number, receipt.stock_item.name)
        grouped[key].append(receipt)

    grouped_receipts = []
    for (voucher_number, item_name), items in grouped.items():
        total_quantity = sum(r.quantity_received for r in items)
        unit_price = items[0].unit_price  # Assume same for all in group
        total_price = sum(r.quantity_received * r.unit_price for r in items)
        vendor_name = items[0].stock_item.vendor.name
        date_received = items[0].date_received

        grouped_receipts.append({
            'voucher_number': voucher_number,
            'item_name': item_name,
            'vendor_name': vendor_name,
            'total_quantity': total_quantity,
            'unit_price': unit_price,
            'total_price': total_price,
            'date_received': date_received,
        })

    return render(request, 'store/stock_list.html', {
        'grouped_receipts': grouped_receipts
    })

@login_required
def stock_create(request):
    form = StockItemForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        stock_item = form.save()
        voucher_number = request.POST.get('voucher_number', '').strip()

        if not voucher_number:
            form.add_error(None, "Voucher number is required.")
            return render(request, 'store/stock_form.html', {'form': form})

        Receipt.objects.create(
            stock_item=stock_item,
            quantity_received=stock_item.quantity,
            unit_price=stock_item.purchase_price,
            date_received=date.today(),  # ✅ No timezone
            voucher_number=voucher_number
        )

        return redirect('stock_list')

    return render(request, 'store/stock_form.html', {'form': form})

@login_required
def issue_list(request):
    recent_issues = (
        Issue.objects
        .values('date_issued', 'stock_item__name', 'office__name', 'remarks')
        .annotate(total_quantity=Sum('quantity_issued'))
        .order_by('-date_issued')
    )

    return render(request, 'store/issue_list.html', {
        'recent_issues': recent_issues
    })

# Issue Entry
@login_required
def issue_create(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('issue_create')
    else:
        form = IssueForm()

    # Prepare data for showing live quantity left
    stock_items = StockItem.objects.all()
    stock_data = {
        str(item.id): item.total_quantity_available() for item in stock_items
    }

    # Group issued items by date + item + office
    recent_issues = (
        Issue.objects
        .values('date_issued', 'stock_item__name', 'office__name', 'remarks')
        .annotate(quantity_issued=Sum('quantity_issued'))
        .order_by('-date_issued')
    )

    context = {
        'form': form,
        'stock_data_json': json.dumps(stock_data),
        'recent_issues': recent_issues
    }
    return render(request, 'store/issue_form.html', context)

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
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_office = request.GET.get('office')
    query = request.GET.get('query', '').strip()

    issues = Issue.objects.select_related('stock_item', 'office')

    if start_date:
        issues = issues.filter(date_issued__gte=start_date)
    if end_date:
        issues = issues.filter(date_issued__lte=end_date)
    if selected_office:
        issues = issues.filter(office__id=selected_office)
    if query:
        issues = issues.filter(stock_item__name__icontains=query)

    grouped = (
        issues.values('office__name', 'stock_item__name')
        .annotate(total_quantity=Sum('quantity_issued'))
        .order_by('office__name', 'stock_item__name')
    )

    offices = Office.objects.all()

    return render(request, 'store/report_search.html', {
        'report': grouped,
        'start_date': start_date,
        'end_date': end_date,
        'query': query,
        'selected_office': selected_office,
        'offices': offices,
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