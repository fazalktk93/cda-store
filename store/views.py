from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.template.loader import get_template
import io
from xhtml2pdf import pisa
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Vendor, StockItem, Issue, Receipt, Office
from .forms import VendorForm, StockItemForm, IssueForm, OfficeForm


# Dashboard
@login_required
def dashboard(request):
    return render(request, 'store/dashboard.html', {
        'vendor_count': Vendor.objects.count(),
        'stock_count': StockItem.objects.count(),
        'issue_count': Issue.objects.count()
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


# Stock CRUD
@login_required
def stock_list(request):
    items = StockItem.objects.all()
    return render(request, 'store/stock_list.html', {'items': items})

@login_required
def stock_create(request):
    form = StockItemForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('stock_list')
    return render(request, 'store/stock_form.html', {'form': form})


# Issue Entry
@login_required
def issue_create(request):
    form = IssueForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('stock_list')
    return render(request, 'store/issue_form.html', {'form': form})


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

    template = get_template('store/report.html')
    html = template.render({'items': items, 'query': query})
    
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='report.pdf')

@login_required
def report_search(request):
    query = request.GET.get('q', '')
    items = StockItem.objects.all()

    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(vendor__name__icontains=query)
        )

    return render(request, 'store/report_search.html', {
        'items': items,
        'query': query
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