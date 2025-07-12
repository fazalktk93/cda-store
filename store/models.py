from django.db import models

class Vendor(models.Model):
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class StockItem(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Issue(models.Model):
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    issued_to = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    issued_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} of {self.stock_item.name} to {self.issued_to}"
class Receipt(models.Model):
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    received_from = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    received_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} of {self.stock_item.name} from {self.received_from}"