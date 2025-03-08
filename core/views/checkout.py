from django.shortcuts import render, redirect
from django.views import View
from core.models.customer import Customer
from core.models.product import Product
from core.models.order import Order
from core.models.cart import CartItem
from django.contrib.auth.mixins import LoginRequiredMixin

class CheckOut(LoginRequiredMixin, View):
    def get(self, request):
        # Handle the initial checkout page display
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum(item.product.price * item.quantity for item in cart_items)
        
        context = {
            'cart_items': cart_items,
            'total': total,
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

