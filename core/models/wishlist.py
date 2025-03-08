
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from .product import Product

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')  # Prevents duplicate wishlist items
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.product.name}"
