from django.contrib.auth.models import User
from django.views.decorators.cache import cache_control
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email as django_validate_email
import re
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login(request):
    
    if request.user.is_authenticated:
        return redirect('main')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not email:
            messages.error(request, "Email cannot be blank.")
            return redirect('login')
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            messages.error(request, "Invalid email format.")
            return redirect('login')
        if not password:
            messages.error(request, "Password cannot be blank.")
            return redirect('login')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect('main')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')
    return render(request, 'login.html')




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def logout(request):
    logout(request)
    messages.success(request, 'Your have logged out successfully!')
    return redirect('login')





# from django.shortcuts import render, redirect
# from django.contrib.auth.hashers import make_password, check_password
# from core.models.customer import Customer
# from django.views import View

# class Login(View):
#     def get(self, request):
#          return render(request, "login.html")

#     def post(self, request):
#         user = request.POST.get("user")
#         password = request.POST.get("password")

#         x = user.find("@")
#         flag = "email"
#         if (x == -1):
#             flag = "phone"
#         userdata = Customer.checkk(user, flag)

#         error = None
#         if (not user):
#             error = "Enter either phone or email"
#         elif (not password):
#             error = "enter the password"
#         elif (userdata == None):
#             error = "enter correct " + flag
#         elif (check_password(password, userdata.password) == False):
#             error = "enter the correct password"
        
#         if (error == None):
#             request.session["customer_id"] = userdata.id
#             if (flag == "email"):
#                 request.session["customer_user"] = userdata.email
#             elif (flag == "phone"):
#                 request.session["customer_user"] = userdata.phone

#             return redirect("main") 
#         else:
#             data = {
#                 "error": error,
#                 "user": user
#             }
#             return render(request, "login.html", data)

# def logout(request):
#     request.session.clear()
#     return  redirect("login")