from django.urls import path
from . import views
from .views import OfficeListView, OfficeCreateView, report_view

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/add/', views.vendor_create, name='vendor_create'),
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/add/', views.stock_create, name='stock_create'),
    path('stock/issue/', views.issue_create, name='issue_create'),
    path('report/pdf/', views.report_pdf, name='report_pdf'),
    path('offices/', OfficeListView.as_view(), name='office_list'),
    path('offices/add/', OfficeCreateView.as_view(), name='office_add'),
    path('report/', report_view, name='report_view'),
    path('report/pdf/', views.report_pdf, name='report_pdf'),
]
