
from django.db import models
from django.utils import timezone
from core.models.order import Order

class ReturnRequest(models.Model):
    CONDITION_CHOICES = [
        ('unused', 'Unused/New'),
        ('opened', 'Opened but unused'),
        ('used', 'Used'),
        ('damaged', 'Damaged')
    ]
    
    SOLUTION_CHOICES = [
        ('refund', 'Full Refund'),
        ('replacement', 'Product Replacement'),
        ('exchange', 'Exchange for different item')
    ]
    
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255)
    description = models.TextField(default="No description provided.")
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='unused')
    preferred_solution = models.CharField(max_length=20, choices=SOLUTION_CHOICES, default='refund')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('completed', 'Completed')
        ],
        default='pending'
    )
    admin_notes = models.TextField(blank=True, null=True)
    processed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Return Request #{self.id} for Order #{self.order.id}"

class ReturnImage(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='return_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Return Request #{self.return_request.id}"


