from django.db import models

class Article(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Receipt(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    date = models.DateField()
    voucher_no = models.CharField(max_length=100)
    from_whom_purchased = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=50)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit


class Issue(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    date = models.DateField()
    quantity_issued = models.PositiveIntegerField()
    to_whom_issued = models.CharField(max_length=200)
    remarks = models.TextField(blank=True)
    signature = models.CharField(max_length=100, blank=True)
