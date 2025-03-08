from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from core.models.customer import Customer

class Otp(View):

    def post(self, request):
        otp_given = request.POST.get("otp_given")
        otp = request.POST.get("otp")
        email = request.POST.get("email")

        if (int(otp_given) == int(otp)):
            userdata = Customer.info(email)
            request.session["customer_id"] = userdata.id
            request.session["customer_user"] = userdata.email
            return redirect("index")
        else:
            status = "the OTP you entered was incorrect. Please try again"
            return render(request, "forgotpass.html", {"flag":False, "status":status})
        