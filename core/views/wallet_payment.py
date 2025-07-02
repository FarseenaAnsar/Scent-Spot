from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from core.models.customer import Customer
from core.models.cart import CartItem
from core.models.order import Order
from core.models.wishlist import Wishlist
from core.models.wallet import Wallet, WalletTransaction
import time
import uuid

class PlaceWalletOrderView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            # Get form data
            fname = request.POST.get('fname')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            total = float(request.POST.get('total'))
            
            # Get cart items
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            
            if not cart_items:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your cart is empty'
                })
            
            # Get wallet
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Wallet not found. Please add money to your wallet first.'
                })
            
            # Check wallet balance
            if wallet.balance < total:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Insufficient wallet balance. Your balance: ₹{wallet.balance}, Required: ₹{total}'
                })
            
            # Get or create customer
            try:
                customer = Customer.objects.get(email=request.user.username)
            except Customer.DoesNotExist:
                customer = Customer.objects.create(
                    email=request.user.username,
                    first_name=fname,
                    phone=phone
                )
            
            # Generate order ID
            order_id = f"WALLET-{int(time.time())}"
            payment_id = f"WALLET-{int(time.time())}"
            
            # Get coupon discount from session
            coupon_discount = request.session.get('discount', 0)
            
            # Create orders for each cart item
            for item in cart_items:
                # Check stock
                if item.product.stock < item.quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Not enough stock for {item.product.name}. Only {item.product.stock} available.'
                    })
                
                # Decrement stock
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
            
            # Deduct amount from wallet
            wallet.balance -= total
            wallet.save()
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_id=str(uuid.uuid4())[:10],
                transaction_type='WITHDRAWAL',
                amount=total,
                status='COMPLETED'
            )
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({
                'status': 'success',
                'order_id': order_id,
                'payment_id': payment_id,
                'redirect_url': f'/payment-success/{payment_id}/',
                'message': 'Your order has been placed successfully using wallet!'
            })
            
        except Exception as e:
            import traceback
            print(f"Wallet Order Error: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })