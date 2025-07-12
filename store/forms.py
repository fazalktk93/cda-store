from django import forms
from .models import Vendor, StockItem, Issue

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
        fields = ['stock_item', 'to_whom', 'quantity_issued', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }