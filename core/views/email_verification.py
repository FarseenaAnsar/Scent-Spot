from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from core.models.email_verification import EmailVerification
from core.forms import EmailVerificationForm

class VerifyEmailView(View):
    template_name = 'verify_email.html'
    
    @method_decorator(login_required)
    def get(self, request):
        email = request.GET.get('email')
        if not email:
            messages.error(request, 'Email is required')
            return redirect('account')
            
        form = EmailVerificationForm(initial={'email': email})
        return render(request, self.template_name, {'form': form})
    
    @method_decorator(login_required)
    def post(self, request):
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = form.cleaned_data['otp']
            
            try:
                verification = EmailVerification.objects.get(email=email, otp=otp)
                
                if verification.is_valid():
                    # Mark as verified
                    verification.is_verified = True
                    verification.save()
                    
                    # Update user's email
                    user = request.user
                    user.email = email
                    user.username = email  # If username is email
                    user.save()
                    
                    # Update customer's email
                    from core.models.customer import Customer
                    try:
                        customer = Customer.objects.get(email=request.user.username)
                        customer.email = email
                        customer.save()
                    except Customer.DoesNotExist:
                        pass
                    
                    messages.success(request, 'Email verified successfully!')
                    return redirect('account')
                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
            except EmailVerification.DoesNotExist:
                messages.error(request, 'Invalid OTP. Please try again.')
                
        return render(request, self.template_name, {'form': form})


class SendOTPView(View):
    @method_decorator(login_required)
    def post(self, request):
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        
        # Generate OTP
        verification = EmailVerification.generate_otp(email)
        
        # Send email with OTP
        try:
            send_mail(
                'Email Verification OTP',
                f'Your OTP for email verification is: {verification.otp}. It will expire in 10 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Failed to send OTP: {str(e)}'})