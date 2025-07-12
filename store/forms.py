from django import forms
from .models import Vendor, StockItem, Issue
from .models import Issue, Office

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact']

class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ['name', 'vendor', 'unit', 'purchase_price', 'quantity']

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['stock_item', 'office', 'quantity_issued', 'remarks', 'date_issued']
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'})
        }
        
class OfficeCreateView(CreateView):
    model = Office
    form_class = OfficeForm  # ✅ only use this
    template_name = 'store/office_form.html'
    success_url = reverse_lazy('office_list')