from django import forms
from .models import Vendor, StockItem, Issue
from .models import Issue, Office
from .models import StockCategory, Receipt
from .models import StockItem, Office
from .models import VendorStock

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact']

class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ['name', 'unit', 'category']


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['stock_item', 'quantity_issued', 'remarks', 'date_issued']
        widgets = {
            'date_issued': forms.DateInput(attrs={
                'type': 'date',             # ✅ triggers native calendar popup
                'class': 'form-control'     # ✅ applies Bootstrap styling
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only include unique stock items by name (first occurrence)
        unique_names = StockItem.objects.values_list('name', flat=True).distinct()
        self.fields['stock_item'].queryset = StockItem.objects.filter(name__in=unique_names).order_by('name')
        
class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ['name', 'location']
        
class ReportSearchForm(forms.Form):
    query = forms.CharField(required=False, label='', widget=forms.TextInput(attrs={
        'placeholder': 'Search name/vendor',
        'class': 'form-control'
    }))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))
    office = forms.ModelChoiceField(
        queryset=Office.objects.all(),
        required=False,
        empty_label="All Offices",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class StockCategoryForm(forms.ModelForm):
    class Meta:
        model = StockCategory
        fields = ['name']
        
class VendorStockForm(forms.ModelForm):
    class Meta:
        model = VendorStock
        fields = ['stock_item', 'purchase_price', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stock_item'].queryset = StockItem.objects.all()
        self.fields['stock_item'].widget.attrs.update({'class': 'form-select'})
        self.fields['purchase_price'].widget.attrs.update({'class': 'form-control'})
        self.fields['quantity'].widget.attrs.update({'class': 'form-control'})
        
class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['stock_item', 'unit_price', 'quantity_received']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stock_item'].queryset = StockItem.objects.all()
        
class VendorReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['stock_item', 'unit_price', 'quantity_received']
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity_received': forms.NumberInput(attrs={'class': 'form-control'}),
        }