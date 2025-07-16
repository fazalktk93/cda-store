from django.urls import path, include  # ✅ Correct import
from django.urls import path
from . import views
from .views import OfficeListView, OfficeCreateView, report_form_view, report_view
from .views import report_search    
from .views import report_view
from .views import vendor_detail, add_vendor_stock

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/add/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:vendor_id>/', vendor_detail, name='vendor_detail'),
    path('vendors/<int:vendor_id>/add-stock/', add_vendor_stock, name='add_vendor_stock'),
    path('voucher/<str:voucher_number>/', views.voucher_detail, name='voucher_detail'),
    path('voucher/<str:voucher_number>/print/', views.voucher_print, name='voucher_print'),
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/add/', views.stock_create, name='stock_create'),
    path('stock/issue/', views.issue_list, name='issue_list'),
    path('stock/issue/add/', views.issue_create, name='issue_create'),
    path('offices/', OfficeListView.as_view(), name='office_list'),
    path('offices/add/', OfficeCreateView.as_view(), name='office_add'),
    path('report/', report_view, name='report_view'),
    path('report/form/', report_form_view, name='report_form'),
    path('report/pdf/', views.report_pdf, name='report_pdf'),
    path('report/search/', report_search, name='report_search'),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout
]
