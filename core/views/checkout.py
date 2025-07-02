from django.shortcuts import render, redirect
from django.views import View
from core.models.customer import Customer
from core.models.product import Product
from core.models.order import Order
from core.models.order import OrderItem
from core.models.cart import CartItem
from core.models.wishlist import Wishlist
from core.models.address import Address
from core.models.wallet import Wallet, WalletTransaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import time
import uuid

class CheckOut(LoginRequiredMixin, View):
    def get(self, request):
        # Handling the initial checkout page display
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
        
        # Calculate offer discount
        offer_discount = original_total - total_with_offers
        
        # Getting discount from session if available
        coupon_discount = request.session.get('discount', 0)
        
        # Get saved addresses
        try:
            customer = Customer.objects.get(email=request.user.username)
            addresses = Address.objects.filter(customer=customer)
        except Customer.DoesNotExist:
            addresses = []
        
        # Get wallet balance
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet_balance = wallet.balance
        except Wallet.DoesNotExist:
            wallet_balance = 0
        
        context = {
            'cart_items': cart_items,
            'original_total': original_total,
            'total': total_with_offers,
            'offer_discount': offer_discount,
            'discount': coupon_discount,
            'addresses': addresses,
            'wallet_balance': wallet_balance,
        }
        return render(request, 'pay.html', context)
    
    def post(self, request):
        status = ""
        address = request.POST.get("address")  
        total = request.POST.get("total")
        
        # Get cart items from the database instead of session
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        
        if not address:
            status = "Please enter your address for placing the order"
            return render(request, "cart.html", {
                "status": status, 
                "type": False, 
                "cart_items": cart_items
            })
        
        try:
            # Create orders for each cart item
            for cart_item in cart_items:
                # Check if product has enough stock
                if cart_item.product.stock < cart_item.quantity:
                    status = f"Not enough stock for {cart_item.product.name}. Only {cart_item.product.stock} available."
                    return render(request, "cart.html", {
                        "status": status, 
                        "type": False, 
                        "cart_items": cart_items
                    })
                
                # Decrement product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()
                
                order = Order(
                    product=cart_item.product,
                    customer=cart_item.user,  # Assuming you're using Django's auth system
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    adress=address,
                    
                )
                order.save()
            
            # Clear the cart after successful order
            cart_items.delete()
            
            return render(request, 'pay.html', {
                "products": [item.product for item in cart_items],
                "total": total
            })
            
        except Exception as e:
            status = f"Error processing order: {str(e)}"
            return render(request, "cart.html", {
                "status": status, 
                "type": False, 
                "cart_items": cart_items
            })
    def checkout(self, request):
        # Your existing order creation code
        customer = request.user
        cart_items = CartItem.objects.filter(user=customer)
        
        # Create the order
        order = Order.objects.create(
            customer=customer,
            # other order fields
        )
        
        # Call the method to create order items and clean up wishlist
        return self.create_order(request, cart_items, order)

class PlaceCODOrderView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            # Get form data
            fname = request.POST.get('fname')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            total = request.POST.get('total')
            
            # Generate a unique order ID for COD
            order_id = f"COD-{int(time.time())}"
            payment_id = f"COD-{int(time.time())}"
            
            # Get cart items
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            
            if not cart_items:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your cart is empty'
                })
            
            # Get or create customer using the user's username for consistency
            try:
                customer = Customer.objects.get(email=request.user.username)
                print(f"Using existing customer with email {request.user.username}")
            except Customer.DoesNotExist:
                customer = Customer.objects.create(
                    email=request.user.username,  # Use username for consistency
                    first_name=fname,
                    phone=phone
                )
                print(f"Created new customer with email {request.user.username}")
                
            # Store customer ID in session for compatibility with older code
            request.session['customer_id'] = customer.id
            print(f"Stored customer ID {customer.id} in session")
            
            # Calculate expected amount from cart (server-side validation)
            cart_total = 0
            for item in cart_items:
                if hasattr(item.product, 'has_offer') and item.product.has_offer:
                    cart_total += item.product.get_discount_price * item.quantity
                else:
                    cart_total += item.product.price * item.quantity
            
            # Get coupon discount from session
            coupon_discount = request.session.get('discount', 0)
            expected_total = cart_total - coupon_discount + 99  # Add convenience fee
            
            # Validate submitted amount against calculated amount
            submitted_total = float(request.POST.get('total'))
            if abs(submitted_total - expected_total) > 0.01:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Amount validation failed. Expected: ₹{expected_total}, Submitted: ₹{submitted_total}'
                })
            
            final_total = expected_total  # Use server-calculated amount
            
            # Check if COD is allowed (orders above ₹1000 not allowed for COD)
            if expected_total > 1000:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cash on Delivery is not available for orders above ₹1000. Please choose online payment.'
                })
            
            # Create orders for each cart item
            for item in cart_items:
                # Debug the customer object
                print(f"Creating order with customer ID: {customer.id}, email: {customer.email}")
                
                # Check if product has enough stock
                if item.product.stock < item.quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Not enough stock for {item.product.name}. Only {item.product.stock} available.'
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
                    coupon_discount=coupon_discount,
                    status="processing"
                )
                order.save()
                
                # Remove from wishlist if present
                Wishlist.objects.filter(user=request.user, product=item.product).delete()
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({
                'status': 'success',
                'order_id': order_id,
                'payment_id': payment_id,
                'redirect_url': f'/payment-success/{payment_id}/',
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

class PlaceWalletOrderView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            fname = request.POST.get('fname')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            from decimal import Decimal
            # Calculate expected amount from cart (server-side validation)
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            expected_total = Decimal('0')
            for item in cart_items:
                if hasattr(item.product, 'has_offer') and item.product.has_offer:
                    expected_total += Decimal(str(item.product.get_discount_price)) * item.quantity
                else:
                    expected_total += Decimal(str(item.product.price)) * item.quantity
            
            # Add discount and convenience fee
            coupon_discount = Decimal(str(request.session.get('discount', 0)))
            expected_total = expected_total - coupon_discount + Decimal('99')
            
            # Validate submitted amount against calculated amount
            submitted_total = Decimal(str(request.POST.get('total')))
            if abs(submitted_total - expected_total) > Decimal('0.01'):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Amount validation failed. Expected: ₹{expected_total}, Submitted: ₹{submitted_total}'
                })
            
            total = expected_total  # Use server-calculated amount
            
            if not cart_items:
                return JsonResponse({'status': 'error', 'message': 'Your cart is empty'})
            
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Wallet not found. Please add money to your wallet first.'})
            
            if wallet.balance < total:
                return JsonResponse({'status': 'error', 'message': f'Insufficient wallet balance. Your balance: ₹{wallet.balance}, Required: ₹{total}'})
            
            try:
                customer = Customer.objects.get(email=request.user.username)
            except Customer.DoesNotExist:
                customer = Customer.objects.create(email=request.user.username, first_name=fname, phone=phone)
            
            order_id = f"WALLET-{int(time.time())}"
            payment_id = f"WALLET-{int(time.time())}"
            coupon_discount = request.session.get('discount', 0)
            
            for item in cart_items:
                if item.product.stock < item.quantity:
                    return JsonResponse({'status': 'error', 'message': f'Not enough stock for {item.product.name}. Only {item.product.stock} available.'})
                
                item.product.stock -= item.quantity
                item.product.save()
                
                price = item.product.get_discount_price if hasattr(item.product, 'has_offer') and item.product.has_offer else item.product.price
                
                Order.objects.create(
                    product=item.product, customer=customer, quantity=item.quantity, price=price,
                    adress=address, phone=phone, order_id=order_id, payment_id=payment_id,
                    coupon_discount=coupon_discount, status="processing"
                )
                
                Wishlist.objects.filter(user=request.user, product=item.product).delete()
            
            wallet.balance -= total
            wallet.save()
            
            WalletTransaction.objects.create(
                wallet=wallet, transaction_id=str(uuid.uuid4())[:10],
                transaction_type='WITHDRAWAL', amount=total, status='COMPLETED'
            )
            
            cart_items.delete()
            
            return JsonResponse({
                'status': 'success', 'order_id': order_id, 'payment_id': payment_id,
                'redirect_url': f'/payment-success/{payment_id}/',
                'message': 'Your order has been placed successfully using wallet!'
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})