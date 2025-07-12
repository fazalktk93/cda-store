from django.urls import path
from .views import (
    dashboard, VendorListView, VendorCreateView,
    StockItemListView, StockItemCreateView
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('vendors/', VendorListView.as_view(), name='vendor_list'),
    path('vendors/add/', VendorCreateView.as_view(), name='vendor_create'),
    path('stock/', StockItemListView.as_view(), name='stockitem_list'),
    path('stock/add/', StockItemCreateView.as_view(), name='stockitem_create'),
]
