import random
import re
from django.http import HttpResponse, HttpResponseNotFound
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_control
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError
from .models import Profile
from core.models.wallet import Wallet
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_login')
        return redirect('main')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Generate OTP and store in session
                otp = random.randint(100000, 999999)
                request.session['login_otp'] = str(otp)
                request.session['login_username'] = username
                request.session['login_password'] = password
                
                # For development: display OTP in message instead of sending email
                messages.success(request, f"Your OTP is: {otp} (For development only)")
                return redirect('verify_login_otp')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'authentication/login.html', {'form': form})


def verify_login_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        sent_otp = request.session.get('login_otp')
        username = request.session.get('login_username')
        password = request.session.get('login_password')
        
        if str(entered_otp) == str(sent_otp):
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Clean up session
                del request.session['login_otp']
                del request.session['login_username']
                del request.session['login_password']
                
                if user.is_staff:
                    return redirect('admin_login')
                return redirect('main')
            else:
                messages.error(request, 'Authentication failed.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('verify_login_otp')
    
    return render(request, 'authentication/verify_login_otp.html')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def user_logout(request):
    logout(request)
    messages.success(request, 'Your have logged out successfully!')
    return redirect('login')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_signup(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_login')
        return redirect('login')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Remove commit=False since we don't need to modify the user
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'authentication/signup.html', {'form': form})


def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        sent_otp = request.session.get('otp')
        email = request.session.get('email')
        password = request.session.get('password')
        if str(entered_otp) == str(sent_otp):
            user = User.objects.create_user(username=email, email=email, password=password)
            user.is_active = True
            user.save()
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
            del request.session['otp']
            del request.session['email']
            del request.session['password']
            messages.success(request, 'Your account has been activated successfully!')
            return redirect('user_profile')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('verify_otp')
    return render(request, 'verify_otp.html',)



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not User.objects.filter(email=email).exists():
            messages.error(request, "Email is not registered.")
            return redirect('forgot_password')
        otp = random.randint(100000, 999999)
        request.session['password_reset_otp'] = str(otp)
        request.session['reset_email'] = email
        send_mail(
            'Your OTP for Password Reset',
            f'Your OTP for Password Reset in vrindapots is: {otp}',
            'your-email@gmail.com',
            [email],
            fail_silently=False,
        )
        messages.success(request, "OTP sent to your email. Please check your inbox.")
        return redirect('verify_otp_for_password_reset')
    return render(request, 'forgot_password.html')



def verify_otp_for_password_reset(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        sent_otp = request.session.get('password_reset_otp')
        email = request.session.get('reset_email')
        if str(entered_otp) == str(sent_otp):
            messages.success(request, "OTP verified. Please reset your password.")
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('verify_otp_for_password_reset')
    return render(request, 'verify_otp_for_password_reset.html')


def reset_password(request):
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.session.get('reset_email')
        if not password1 or not password2:
            messages.error(request, "Password fields cannot be blank.")
            return redirect('reset_password')
        if len(password1) < 8 or not re.search(r'\d', password1):
            messages.error(request, "Password must be at least 8 characters long and include a number.")
            return redirect('reset_password')
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('reset_password')
        user = User.objects.get(email=email)
        user.set_password(password1)
        user.save()
        messages.success(request, "Your password has been reset successfully. Please log in.")
        del request.session['password_reset_otp']
        del request.session['reset_email']
        return redirect('user_login')
    return render(request, 'reset_password.html')