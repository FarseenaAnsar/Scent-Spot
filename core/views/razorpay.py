from django.shortcuts import render, redirect
from django.views import View
from core.models.customer import Customer
from core.models.product import Product
from core.models.order import Order
from core.models.cart import CartItem
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import razorpay
from django.conf import settings


class razorpaycheck(LoginRequiredMixin, View):
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum(item.product.price * item.quantity for item in cart_items)
        
        return JsonResponse({
            "amount": total * 100,
            "key": settings.RAZORPAY_KEY_ID
        })
        
    def post(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum(item.product.price * item.quantity for item in cart_items)
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        payment = client.order.create({
            "amount": total * 100,  # Amount in paise
            "currency": "INR",
            "payment_capture": "1"
        })
        
        return JsonResponse({
            "order_id": payment['id'],
            "amount": total * 100,
            "key": settings.RAZORPAY_KEY_ID,
            "name": request.POST.get('fname'),
            "email": request.POST.get('email'),
            "contact": request.POST.get('phone'),
        })

from django.views.generic import TemplateView
from django.views import View
from core.models import Order  # Assuming you have these models

class VerifyPaymentView(View):
    def post(self, request):
        payment_id = request.POST.get('payment_id')
        order_id = request.POST.get('order_id')
        signature = request.POST.get('signature')
        
        # Verify the payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature({
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            })
            
            # Create order record
            cart_items = CartItem.objects.filter(user=request.customer)
            order = Order.objects.create(
                customer=request.customer,
                payment_id=payment_id,
                order_id=order_id,
                total_amount=request.POST.get('amount'),
                status='PAID'
            )
            
            # Create order items
            for item in cart_items:
                Order.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
            
            # Clear the cart
            cart_items.delete()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

class PlaceOrder(LoginRequiredMixin, View):
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum(item.product.price * item.quantity for item in cart_items)
        return render(request, 'razorpay.html', {'cart_items': cart_items, 'total': total})

class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = kwargs.get('payment_id')
        try:
            order = Order.objects.get(payment_id=payment_id, user=self.request.user)
            context['order'] = order
            context['order_items'] = order.orderitem_set.all()
        except Order.DoesNotExist:
            context['error'] = 'Order not found'
        return context
