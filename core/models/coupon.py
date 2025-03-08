from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=[
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ])
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    minimum_purchase = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(default=0)  # 0 means unlimited
    times_used = models.IntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self, total_amount):
        from django.utils import timezone
        now = timezone.now()
        
        if not self.active:
            return False, "Coupon is not active"
        
        if now < self.valid_from:
            return False, "Coupon period has not started yet"
            
        if now > self.valid_to:
            return False, "Coupon has expired"
            
        if self.usage_limit > 0 and self.times_used >= self.usage_limit:
            return False, "Coupon usage limit exceeded"
            
        if total_amount < self.minimum_purchase:
            return False, f"Minimum purchase amount of ${self.minimum_purchase} required"
            
        return True, "Coupon is valid"

    def calculate_discount(self, total_amount):
        if self.discount_type == 'percentage':
            return (self.discount_value / 100) * total_amount
        return min(self.discount_value, total_amount)  # Fixed amount
