from django.db import models
from .product import Product
from .customer import Customer
from .order import Order
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Rate(models.Model):
    rating = models.IntegerField(default=1, validators=[MinValueValidator(0),MaxValueValidator(5)])
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def place_order(self):
        self.save()
    
    @staticmethod
    def check_order_id(id):
        return Rate.objects.filter(order = id)