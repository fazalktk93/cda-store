from django.contrib import admin
from .models import Vendor, StockItem, Receipt, Issue

admin.site.register(Vendor)
admin.site.register(StockItem)
admin.site.register(Receipt)
admin.site.register(Issue)
