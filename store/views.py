from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.template.loader import get_template
from django.utils.dateparse import parse_date
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, F
from django.forms import modelformset_factory
from collections import defaultdict
from datetime import date
import json, io
from xhtml2pdf import pisa
from decimal import Decimal
from django.db import models

from .models import Vendor, StockItem, Issue, Receipt, Office
from .forms import VendorForm, StockItemForm, IssueForm, OfficeForm, ReportSearchForm

# ---------------- Dashboard ----------------
@login_required
def dashboard(request):
    context = {
        'vendor_count': Vendor.objects.count(),
        'stock_count': StockItem.objects.count(),
        'issue_count': Issue.objects.count(),
        'low_stock_items': StockItem.objects.filter(quantity__lt=40),
    }
    return render(request, 'store/dashboard.html', context)

# ---------------- Vendor Views ----------------
@login_required
def vendor_list(request):
    query = request.GET.get('q', '')
    vendors = Vendor.objects.all()
    if query:
        vendors = vendors.filter(Q(name__icontains=query) | Q(contact__icontains=query))
    return render(request, 'store/vendor_list.html', {'vendors': vendors})

@login_required
def vendor_create(request):
    form = VendorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('vendor_list')
    return render(request, 'store/vendor_form.html', {'form': form})

@login_required
def vendor_detail(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    stock_items = StockItem.objects.filter(vendor=vendor)
    start = parse_date(request.GET.get('start', ''))
    end = parse_date(request.GET.get('end', ''))

    if start and end:
        receipts = Receipt.objects.filter(stock_item__in=stock_items, date_received__range=(start, end))
    else:
        receipts = Receipt.objects.filter(stock_item__in=stock_items)

    vouchers = (
        Receipt.objects.filter(stock_item__vendor=vendor)
        .values('voucher_number')
        .annotate(
            total_items=Sum('quantity_received'),
            total_price=Sum(F('unit_price') * F('quantity_received'), output_field=models.DecimalField()),
            date=F('date_received')
        ).order_by('-date')
    )

    return render(request, 'store/vendor_detail.html', {
        'vendor': vendor,
        'stock_items': stock_items,
        'receipts': receipts,
        'vouchers': vouchers,
        'start': request.GET.get('start', ''),
        'end': request.GET.get('end', '')
    })

@login_required
def add_vendor_stock(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    StockFormSet = modelformset_factory(StockItem, form=StockItemForm, extra=1)
    formset = StockFormSet(request.POST or None, queryset=StockItem.objects.none())
    if request.method == 'POST' and formset.is_valid():
        instances = formset.save(commit=False)
        for item in instances:
            item.vendor = vendor
            item.save()
        return redirect('vendor_detail', vendor_id=vendor.id)
    return render(request, 'store/add_vendor_stock.html', {'formset': formset, 'vendor': vendor})

# ---------------- Stock Views ----------------
@login_required
def stock_list(request):
    receipts = Receipt.objects.select_related('stock_item', 'stock_item__vendor').order_by('-date_received')
    grouped = defaultdict(list)
    for r in receipts:
        key = (r.voucher_number, r.stock_item.name)
        grouped[key].append(r)

    grouped_receipts = []
    for (voucher_number, item_name), items in grouped.items():
        grouped_receipts.append({
            'voucher_number': voucher_number,
            'item_name': item_name,
            'vendor_name': items[0].stock_item.vendor.name,
            'total_quantity': sum(r.quantity_received for r in items),
            'unit_price': items[0].unit_price,
            'total_price': sum(r.quantity_received * r.unit_price for r in items),
            'date_received': items[0].date_received,
        })

    return render(request, 'store/stock_list.html', {'grouped_receipts': grouped_receipts})

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
            date_received=date.today(),
            voucher_number=voucher_number
        )
        return redirect('stock_list')
    return render(request, 'store/stock_form.html', {'form': form})

# ---------------- Issue Views ----------------
@login_required
def issue_list(request):
    issues = Issue.objects.values('date_issued', 'stock_item__name', 'office__name', 'remarks').annotate(
        total_quantity=Sum('quantity_issued')
    ).order_by('-date_issued')
    return render(request, 'store/issue_list.html', {'recent_issues': issues})

@login_required
def issue_create(request):
    form = IssueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('issue_create')
    stock_items = StockItem.objects.all()
    stock_data = {str(i.id): i.total_quantity_available() for i in stock_items}
    recent_issues = Issue.objects.values('date_issued', 'stock_item__name', 'office__name', 'remarks').annotate(
        quantity_issued=Sum('quantity_issued')).order_by('-date_issued')
    return render(request, 'store/issue_form.html', {
        'form': form,
        'stock_data_json': json.dumps(stock_data),
        'recent_issues': recent_issues
    })

# ---------------- Reports ----------------
@login_required
def report_pdf(request):
    query = request.GET.get('q', '')
    items = StockItem.objects.filter(Q(name__icontains=query) | Q(vendor__name__icontains=query)) if query else StockItem.objects.all()
    html = get_template('store/report_pdf.html').render({'items': items})
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='filtered_report.pdf')

@login_required
def report_search(request):
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    office = request.GET.get("office")
    query = request.GET.get("query")

    issues = Issue.objects.all()
    if start: issues = issues.filter(date_issued__gte=start)
    if end: issues = issues.filter(date_issued__lte=end)
    if office: issues = issues.filter(office_id=office)
    if query: issues = issues.filter(stock_item__name__icontains=query)

    report = issues.values('date_issued', 'office__name', 'stock_item__name').annotate(total_quantity=Sum('quantity_issued')).order_by('-date_issued')
    return render(request, "store/report_search.html", {
        "report": report,
        "start_date": start,
        "end_date": end,
        "selected_office": office,
        "query": query,
        "offices": Office.objects.all()
    })

@login_required
def report_view(request):
    show_vendor = 'show_vendor' in request.GET
    show_office = 'show_office' in request.GET
    include_receipts = 'include_receipts' in request.GET
    include_issues = 'include_issues' in request.GET
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    issues = Issue.objects.all()
    receipts = Receipt.objects.all()
    if start:
        issues = issues.filter(date_issued__gte=start)
        receipts = receipts.filter(date_received__gte=start)
    if end:
        issues = issues.filter(date_issued__lte=end)
        receipts = receipts.filter(date_received__lte=end)

    if 'export' in request.GET:
        html = get_template('store/report_pdf.html').render({
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

# ---------------- Office Management ----------------
class OfficeListView(ListView):
    model = Office
    template_name = 'store/office_list.html'

class OfficeCreateView(CreateView):
    model = Office
    form_class = OfficeForm
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

# ---------------- Voucher Views ----------------
@login_required
def voucher_detail(request, voucher_number):
    receipts = Receipt.objects.filter(voucher_number=voucher_number).select_related('stock_item', 'stock_item__vendor')

    # Apply date filter if search=true is in query
    if request.GET.get("search") == "true":
        start = request.GET.get("start")
        end = request.GET.get("end")
        if start and end:
            receipts = receipts.filter(date_received__range=[start, end])
    else:
        start = end = None

    # Group items by (name, unit_price)
    grouped_data = defaultdict(lambda: {"quantity": 0, "total_price": Decimal("0.00")})
    for receipt in receipts:
        key = (receipt.stock_item.name, receipt.unit_price)
        grouped_data[key]["quantity"] += receipt.quantity_received
        grouped_data[key]["total_price"] += receipt.quantity_received * receipt.unit_price

    grouped_receipts = []
    for (name, unit_price), values in grouped_data.items():
        grouped_receipts.append({
            "item_name": name,
            "unit_price": unit_price,
            "quantity": values["quantity"],
            "total_price": values["total_price"]
        })

    grand_total = sum(item["total_price"] for item in grouped_receipts)
    vendor_name = receipts[0].stock_item.vendor.name if receipts else ""
    voucher_date = receipts[0].date_received if receipts else ""

    return render(request, 'store/voucher_detail.html', {
        "voucher_number": voucher_number,
        "vendor_name": vendor_name,
        "voucher_date": voucher_date,
        "receipts": grouped_receipts,
        "grand_total": grand_total,
        "search_mode": request.GET.get("search") == "true",
        "start": start,
        "end": end,
    })

@login_required
def voucher_print(request, voucher_number):
    receipts = Receipt.objects.filter(voucher_number=voucher_number).select_related('stock_item', 'stock_item__vendor')

    # Group items by (item name, unit price)
    grouped_data = defaultdict(lambda: {"quantity": 0, "total_price": Decimal("0.00")})
    for receipt in receipts:
        key = (receipt.stock_item.name, receipt.unit_price)
        grouped_data[key]["quantity"] += receipt.quantity_received
        grouped_data[key]["total_price"] += receipt.quantity_received * receipt.unit_price

    grouped_receipts = []
    for (name, unit_price), values in grouped_data.items():
        grouped_receipts.append({
            "item_name": name,
            "unit_price": unit_price,
            "quantity": values["quantity"],
            "total_price": values["total_price"]
        })

    grand_total = sum(item["total_price"] for item in grouped_receipts)
    vendor_name = receipts[0].stock_item.vendor.name if receipts else ""
    voucher_date = receipts[0].date_received if receipts else ""

    html = get_template('store/voucher_print.html').render({
        "voucher_number": voucher_number,
        "vendor_name": vendor_name,
        "voucher_date": voucher_date,
        "receipts": grouped_receipts,
        "grand_total": grand_total
    })

    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)

    return FileResponse(buffer, content_type='application/pdf')