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
from django.views.generic import TemplateView


class razorpaycheck(LoginRequiredMixin, View):
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        
        # Calculate original total (without offers)
        original_total = sum(item.product.price * item.quantity for item in cart_items)
        
        # Calculate total with offers
        total_with_offers = 0
        for item in cart_items:
            if hasattr(item.product, 'has_offer') and item.product.has_offer:
                total_with_offers += item.product.get_discount_price * item.quantity
            else:
                total_with_offers += item.product.price * item.quantity
        
        # Get discount from session
        discount = request.session.get('discount', 0)
        
        # Calculate final amount including discount and convenience fee
        final_amount = total_with_offers - discount + 99  # Add convenience fee
        
        return JsonResponse({
            "amount": final_amount * 100,  # Convert to paise
            "key": settings.RAZORPAY_KEY_ID
        })
        
    def post(self, request):
        # Get the total from the form which already includes discount and convenience fee
        total = float(request.POST.get('total', 0))
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order using the total from the form
        payment = client.order.create({
            "amount": int(total * 100),  # Amount in paise
            "currency": "INR",
            "payment_capture": "1"
        })
        
        return JsonResponse({
            "order_id": payment['id'],
            "amount": int(total * 100),
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
            
            # Fetch payment details from Razorpay to validate amount
            payment_details = client.payment.fetch(payment_id)
            paid_amount = payment_details['amount'] / 100  # Convert from paise to rupees
            
            # Calculate expected amount from cart
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            expected_total = 0
            for item in cart_items:
                if hasattr(item.product, 'has_offer') and item.product.has_offer:
                    expected_total += item.product.get_discount_price * item.quantity
                else:
                    expected_total += item.product.price * item.quantity
            
            # Add discount and convenience fee
            coupon_discount = request.session.get('discount', 0)
            expected_total = expected_total - coupon_discount + 99
            
            # Validate payment amount
            if abs(paid_amount - expected_total) > 0.01:  # Allow small floating point differences
                return JsonResponse({
                    'status': 'error',
                    'message': f'Payment amount mismatch. Expected: ₹{expected_total}, Paid: ₹{paid_amount}'
                })
            
            # Verify payment status
            if payment_details['status'] != 'captured':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment not completed successfully'
                })
            
            # Get cart items
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            
            # Get or create customer
            try:
                customer = Customer.objects.get(email=request.user.username)
            except Customer.DoesNotExist:
                customer = Customer.objects.create(
                    email=request.user.username,
                    first_name=request.user.first_name,
                    phone=""
                )
            
            # Get coupon discount from session
            coupon_discount = request.session.get('discount', 0)
            
            # Create orders for each cart item
            for item in cart_items:
                # Check if product has enough stock
                if item.product.stock < item.quantity:
                    from django.urls import reverse
                    error_message = f'Not enough stock for {item.product.name}. Only {item.product.stock} available.'
                    return JsonResponse({
                        'status': 'error',
                        'message': error_message,
                        'redirect_url': f"{reverse('payment_failure')}?error_message={error_message}"
                    })
                
                # Decrement product stock
                item.product.stock -= item.quantity
                item.product.save()
                
                # Use discounted price if offer is available
                price = item.product.get_discount_price if hasattr(item.product, 'has_offer') and item.product.has_offer else item.product.price
                
                order = Order(
                    product=item.product,
                    customer=customer,
                    quantity=item.quantity,
                    price=price,
                    adress=request.POST.get('address', ''),
                    phone=request.POST.get('phone', ''),
                    order_id=order_id,
                    payment_id=payment_id,
                    coupon_discount=coupon_discount,
                    status="processing"
                )
                order.save()
                
                # Remove from wishlist if present
                Wishlist.objects.filter(user=request.user, product=item.product).delete()
            
            # Clear the cart
            cart_items.delete()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            import traceback
            from django.urls import reverse
            print(f"Payment Verification Error: {str(e)}")
            print(traceback.format_exc())
            error_message = str(e)
            return JsonResponse({
                'status': 'error', 
                'message': error_message,
                'redirect_url': f"{reverse('payment_failure')}?error_message={error_message}"
            })

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
                from django.urls import reverse
                error_message = 'Your cart is empty'
                return JsonResponse({
                    'status': 'error',
                    'message': error_message,
                    'redirect_url': f"{reverse('payment_failure')}?error_message={error_message}"
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
                # Check if product has enough stock
                if item.product.stock < item.quantity:
                    from django.urls import reverse
                    error_message = f'Not enough stock for {item.product.name}. Only {item.product.stock} available.'
                    return JsonResponse({
                        'status': 'error',
                        'message': error_message,
                        'redirect_url': f"{reverse('payment_failure')}?error_message={error_message}"
                    })
                
                # Decrement product stock
                item.product.stock -= item.quantity
                item.product.save()
                
                # Use discounted price if offer is available
                price = item.product.get_discount_price if hasattr(item.product, 'has_offer') and item.product.has_offer else item.product.price
                
                order = Order(
                    product=item.product,
                    customer=customer,
                    quantity=item.quantity,
                    price=price,
                    adress=address,
                    phone=phone,
                    order_id=order_id,
                    payment_id=payment_id,
                    status="processing"
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
            from django.urls import reverse
            print(f"COD Order Error: {str(e)}")
            print(traceback.format_exc())
            error_message = str(e)
            return JsonResponse({
                'status': 'error',
                'message': error_message,
                'redirect_url': f"{reverse('payment_failure')}?error_message={error_message}"
            })
            
class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payment_success.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = kwargs.get('payment_id')
        
        # Get discount from session
        discount = self.request.session.get('discount', 0)
        
        try:
            # Get all orders with this payment_id
            orders = Order.objects.filter(payment_id=payment_id)
            
            if orders.exists():
                context['orders'] = orders
                context['is_cod'] = payment_id.startswith('COD-')
                context['payment_id'] = payment_id
                
                # Calculate subtotal
                subtotal = sum(order.price * order.quantity for order in orders)
                context['subtotal'] = subtotal
                context['discount'] = discount
                context['total'] = subtotal - discount + 99  # Add convenience fee
            else:
                context['error'] = 'Order not found'
                print(f"No orders found with payment_id: {payment_id}")
                # Debug info
                user_orders = Order.objects.filter(customer__email=self.request.user.username)
                print(f"User has {user_orders.count()} orders with payment IDs: {[o.payment_id for o in user_orders]}")
                
        except Exception as e:
            import traceback
            print(f"Error in PaymentSuccessView: {str(e)}")
            print(traceback.format_exc())
            context['error'] = str(e)
        
        return context