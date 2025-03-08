
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from core.models.coupon import Coupon

class ApplyCouponView(View):
    def post(self, request):
        code = request.POST.get('coupon_code')
        cart_total = float(request.POST.get('cart_total', 0))
        
        try:
            coupon = Coupon.objects.get(code__iexact=code)
            is_valid, message = coupon.is_valid(cart_total)
            
            if is_valid:
                discount = coupon.calculate_discount(cart_total)
                request.session['coupon_id'] = coupon.id
                request.session['discount'] = float(discount)
                messages.success(request, f"Coupon applied successfully! You saved ${discount:.2f}")
            else:
                messages.error(request, message)
                
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code")
            
        return redirect('cart')  # Redirect back to cart page

class RemoveCouponView(View):
    def post(self, request):
        if 'coupon_id' in request.session:
            del request.session['coupon_id']
        if 'discount' in request.session:
            del request.session['discount']
        messages.success(request, "Coupon removed successfully")
        return redirect('cart')
