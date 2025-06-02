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
import time
from core.models.wishlist import Wishlist


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

    def proceed_to_pay(request):
        if request.method == "POST":
            total = request.POST.get('total')
            # Convert to integer and return as is (Razorpay expects amount in paise)
            return JsonResponse({
                'total': int(total)
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

class PlaceCODOrderView(LoginRequiredMixin, View):
    def post(self, request):
        print("DEBUG: PlaceCODOrderView.post() called")
        try:
            # Get form data
            fname = request.POST.get('fname')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            total = request.POST.get('total')
            
            # Generate a unique order ID for COD
            order_id = f"COD-{int(time.time())}"
            payment_id = order_id  # Use the same ID for payment_id
            
            # Get cart items
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            
            if not cart_items:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your cart is empty'
                })
            
            # Get or create customer - use a single clean approach
            try:
                customer = Customer.objects.get(email=request.user.username)
                print(f"DEBUG: Found existing customer with ID {customer.id} and email {customer.email}")
            except Customer.DoesNotExist:
                customer = Customer.objects.create(
                    email=request.user.username,
                    first_name=fname,
                    phone=phone
                )
                print(f"DEBUG: Created new customer with ID {customer.id} and email {customer.email}")
            
            # Create orders for each cart item
            for item in cart_items:
                order = Order(
                    product=item.product,
                    customer=customer,
                    quantity=item.quantity,
                    price=item.product.price,
                    adress=address,
                    phone=phone,
                    order_id=order_id,
                    payment_id=payment_id,
                    status="received"
                )
                
                print(f"DEBUG: All orders in database: {Order.objects.all().count()}")
                print(f"DEBUG: Orders for customer {customer.id}: {Order.objects.filter(customer=customer).count()}")
                
                order.save()
                print(f"DEBUG: Created order with ID {order.id} for customer {customer.id}")
                print(f"DEBUG: Order customer ID: {order.customer_id}, Customer ID: {customer.id}")
                
                # Check if the customer IDs match
                if order.customer_id != customer.id:
                    print(f"ERROR: Customer ID mismatch! order.customer_id={order.customer_id}, customer.id={customer.id}")
                
                # Remove from wishlist if present
                Wishlist.objects.filter(user=request.user, product=item.product).delete()
            
            # After saving all orders
            all_orders = Order.objects.filter(customer=customer)
            print(f"DEBUG: After creating orders, customer {customer.id} has {all_orders.count()} orders")
            print(f"DEBUG: Order IDs: {[o.id for o in all_orders]}")
            
            # Also check the by_customer method
            customer_orders = Order.by_customer(customer)
            print(f"DEBUG: by_customer method shows {len(customer_orders)} orders")
            
            # Clear cart
            cart_items.delete()
            
            # Return JSON with redirect URL
            from django.urls import reverse
            redirect_url = reverse('payment_success', kwargs={'payment_id': payment_id})
            return JsonResponse({
                'status': 'success',
                'order_id': order_id,
                'payment_id': payment_id,
                'redirect_url': redirect_url,
                'message': 'Your order has been placed successfully!'
            })
            
        except Exception as e:
            import traceback
            print(f"COD Order Error: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = kwargs.get('payment_id')
        
        # Get discount from session
        discount = self.request.session.get('discount', 0)
        
        try:
            # Checking if it's a COD order (payment_id starts with COD-)
            if payment_id.startswith('COD-'):
                orders = Order.objects.filter(payment_id=payment_id)
                if orders.exists():
                    context['orders'] = orders
                    context['is_cod'] = True
                    context['payment_id'] = payment_id
                    
                    # Calculate subtotal
                    subtotal = sum(order.price * order.quantity for order in orders)
                    context['subtotal'] = subtotal
                    context['discount'] = discount
                    context['total'] = subtotal - discount + 99  # Add convenience fee
                else:
                    context['error'] = 'Order not found'
            else:
                # Handle regular Razorpay orders
                try:
                    order = Order.objects.get(payment_id=payment_id, customer__email=self.request.user.email)
                    context['order'] = order
                    context['order_items'] = order.orderitem_set.all()
                    
                    # Calculate subtotal
                    subtotal = order.price
                    context['subtotal'] = subtotal
                    context['discount'] = discount
                    context['total'] = subtotal - discount + 99  
                except Order.DoesNotExist:
                    context['error'] = 'Order not found'
        except Exception as e:
            context['error'] = str(e)
        
        return context


