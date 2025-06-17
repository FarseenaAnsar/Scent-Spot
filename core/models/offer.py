from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from .product import Product
from .category import Category

class Offer(models.Model):
    name = models.CharField(max_length=100)
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
    
    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to
    
    def calculate_discount(self, price):
        return (Decimal(str(price)) * self.discount_percentage) / 100

class ProductOffer(Offer):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    
    def __str__(self):
        return f"{self.name} - {self.product.name} ({self.discount_percentage}%)"

class CategoryOffer(Offer):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='offers')
    
    def __str__(self):
        return f"{self.name} - {self.category.name} ({self.discount_percentage}%)"

class ReferralOffer(Offer):
    code = models.CharField(max_length=20, unique=True)
    max_uses = models.IntegerField(default=1)
    times_used = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} - {self.code} ({self.discount_percentage}%)"
    
    def is_valid(self):
        basic_valid = super().is_valid()
        return basic_valid and (self.max_uses == 0 or self.times_used < self.max_uses)