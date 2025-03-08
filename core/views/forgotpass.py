from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django.core.mail import send_mail
import random

class Forgotpass(View):

    def get(self, request):
        return render(request, "forgotpass.html", {"flag":False})

    def post(self, request):
        email = request.POST.get("email")
        otp = random.randint(1111,9999)
        subject = 'OTP'
        message = f"this is your OTP(one time password). Do not share this with anyone.{otp}"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, email_from, recipient_list)
        return render(request, "forgotpass.html", {"flag":True, "otp":otp, "email":email})