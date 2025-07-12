from django.db import models

class OfficeCreateView(CreateView):
    model = Office
    fields = ['name', 'location']  # ✅ This will auto-generate the form
    template_name = 'store/office_form.html'
    success_url = reverse_lazy('office_list')

class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class StockItem(models.Model):
    name = models.CharField(max_length=200)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    unit = models.CharField(max_length=50)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)

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
    date_received = models.DateField(auto_now_add=True)
    source = models.CharField(max_length=200)

    def __str__(self):
        return f"Received {self.quantity_received} of {self.stock_item.name} from {self.source}"
