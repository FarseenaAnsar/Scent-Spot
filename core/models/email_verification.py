from django.db import models
from django.utils import timezone
import random
import string

class EmailVerification(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    @classmethod
    def generate_otp(cls, email):
        # Generate a 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        # Create or update verification record
        verification, created = cls.objects.update_or_create(
            email=email,
            defaults={
                'otp': otp,
                'expires_at': expires_at,
                'is_verified': False
            }
        )
        
        return verification
    
    def is_valid(self):
        return not self.is_verified and timezone.now() < self.expires_at