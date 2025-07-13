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
        fields = ['name', 'vendor', 'purchase_price', 'quantity']


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['stock_item', 'office', 'quantity_issued', 'remarks', 'date_issued']
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'})
        }
        
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
