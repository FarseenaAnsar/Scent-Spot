from django import forms
from .models .customer import Customer

class CustomerProfileForm(forms.ModelForm):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}), required=True)

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EmailVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6, 
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP'
        })
    )
    email = forms.EmailField(widget=forms.HiddenInput())

