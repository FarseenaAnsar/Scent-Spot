# authentication/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from core.models.customer import Customer

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    referral_code = forms.CharField(required=False, max_length=10, 
                                   help_text="Optional: Enter referral code if you have one")
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "referral_code")

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username
    
    def clean_referral_code(self):
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            try:
                Customer.objects.get(referral_code=referral_code)
            except Customer.DoesNotExist:
                raise ValidationError("Invalid referral code.")
        return referral_code
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
