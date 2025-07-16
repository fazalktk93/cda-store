from django.db import models
from django.db.models import Sum

class Office(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class StockCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class StockItem(models.Model):
    name = models.CharField(max_length=200)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE)
    category = models.ForeignKey(StockCategory, on_delete=models.CASCADE, related_name='items')  # ✅ new line
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_price = self.purchase_price * self.quantity
        super().save(*args, **kwargs)

    def total_quantity_available(self):
        total_received = self.receipt_set.aggregate(qty=Sum('quantity_received'))['qty'] or 0
        total_issued = self.issue_set.aggregate(qty=Sum('quantity_issued'))['qty'] or 0
        return total_received - total_issued

    def __str__(self):
        return self.name



class Issue(models.Model):
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_issued = models.PositiveIntegerField()
    remarks = models.TextField(blank=True)
    date_issued = models.DateField(auto_now_add=False, auto_now=False)

    def __str__(self):
        return f"Issued {self.quantity_issued} of {self.stock_item.name} to {self.office.name}"


class Receipt(models.Model):
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    quantity_received = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_received = models.DateField()
    voucher_number = models.CharField(max_length=50, default='', blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity_received
        super().save(*args, **kwargs)
