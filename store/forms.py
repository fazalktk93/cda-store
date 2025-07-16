from django import forms
from .models import Vendor, StockItem, Issue
from .models import Issue, Office
from .models import StockCategory

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact']

class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ['name', 'unit']


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['stock_item', 'office', 'quantity_issued', 'remarks', 'date_issued']

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