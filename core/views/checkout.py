from django.shortcuts import render, redirect
from django.views import View
from core.models.customer import Customer
from core.models.product import Product
from core.models.order import Order
from core.models.order import OrderItem
from core.models.cart import CartItem
from core.models.wishlist import Wishlist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import time

class CheckOut(LoginRequiredMixin, View):
    def get(self, request):
        # Handle the initial checkout page display
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum(item.product.price * item.quantity for item in cart_items)
        
            # Get discount from session if available
        discount = request.session.get('discount', 0)
        
        context = {
            'cart_items': cart_items,
            'total': total,
            'discount': discount,
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
                order = Order(
                    product=cart_item.product,
                    customer=cart_item.user,  # Assuming you're using Django's auth system
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    address=address,
                    
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
            
            # Get the first customer with this email or create a new one
            try:
                customer = Customer.objects.filter(email=email).first()
                if not customer:
                    customer = Customer.objects.create(
                        email=email,
                        first_name=fname,
                        phone=phone
                    )
            except Exception as e:
                print(f"Error getting customer: {str(e)}")
                # Create a new customer as fallback
                customer = Customer.objects.create(
                    email=f"{email}-{int(time.time())}",  # Make email unique
                    first_name=fname,
                    phone=phone
                )
            
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

