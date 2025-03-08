from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


# Create your models here.


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile', null=True)
    address = models.TextField(null=True)
    is_current = models.BooleanField(default=False)

    pincode = models.CharField(
        max_length=6,
        validators=[RegexValidator(regex='^\d{6}$', message='Pincode must be exactly 6 digits', code='invalid_pincode')],
        null=True
    )
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex='^\d{10}$', message='Phone number must be exactly 10 digits', code='invalid_phone_number')],
        null=True
    )
    STATE_CHOICES = [
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Arunachal Pradesh', 'Arunachal Pradesh'),
        ('Assam', 'Assam'),
        ('Bihar', 'Bihar'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Goa', 'Goa'),
        ('Gujarat', 'Gujarat'),
        ('Haryana', 'Haryana'),
        ('Himachal Pradesh', 'Himachal Pradesh'),
        ('Jharkhand', 'Jharkhand'),
        ('Karnataka', 'Karnataka'),
        ('Kerala', 'Kerala'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Maharashtra', 'Maharashtra'),
        ('Manipur', 'Manipur'),
        ('Meghalaya', 'Meghalaya'),
        ('Mizoram', 'Mizoram'),
        ('Nagaland', 'Nagaland'),
        ('Odisha', 'Odisha'),
        ('Punjab', 'Punjab'),
        ('Rajasthan', 'Rajasthan'),
        ('Sikkim', 'Sikkim'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Telangana', 'Telangana'),
        ('Tripura', 'Tripura'),
        ('Uttar Pradesh', 'Uttar Pradesh'),
        ('Uttarakhand', 'Uttarakhand'),
        ('West Bengal', 'West Bengal'),
        ('Delhi', 'Delhi'),
        ('Chandigarh', 'Chandigarh'),
        ('Puducherry', 'Puducherry'),
        ('Jammu and Kashmir', 'Jammu and Kashmir'),
        ('Ladakh', 'Ladakh'),
    ]
    state = models.CharField(max_length=50, choices=STATE_CHOICES, null=True)
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

