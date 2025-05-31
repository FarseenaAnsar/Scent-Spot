from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from core.models.product import Product
from core.models.cart import CartItem
from core.models.wishlist import Wishlist
from core.models.customer import Customer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import View, ListView
from django.db import transaction


class Cart(LoginRequiredMixin, View):
    login_url = '/login/'  
    template_name = 'cart.html'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access your cart.')
            return redirect('login')  
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        final_total = cart_total
        if 'discount' in request.session:
            final_total = cart_total - request.session['discount']
            
        context = {
            'cart_items': cart_items,
            'cart_total': cart_total,
            'final_total': final_total
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        prdid = request.POST.get("prdid")
        if prdid:
            try:
                cart_item = CartItem.objects.get(user=request.user, product_id=prdid)
                cart_item.delete()
                messages.success(request, 'Item removed from cart successfully!')
            except CartItem.DoesNotExist:
                pass
            
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        if not cart_items:
            messages.info(request, "There are no products in the cart. Let's add some products!")
            return render(request, "cart.html", {
                "cartItem": []
            })
        return render(request, "cart.html", {
            "cartItem": cart_items
        })

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)
            quantity = int(request.POST.get('quantity', 1))
            
            # Check if product is in stock
            if product.stock < 1:
                messages.error(request, f"{product.name} is out of stock!")
                return redirect(request.META.get('HTTP_REFERER', 'cart'))
            
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, 'Cart updated successfully!')
            else:
                messages.success(request, 'Item added to your cart!')
            
            # Remove from wishlist if present
            Wishlist.objects.filter(user=request.user, product=product).delete()
            
            return redirect('cart')
        except Exception as e:
            messages.error(request, f'Error adding item to cart: {str(e)}')
            return redirect('wishlist')



class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        cart_item = get_object_or_404(
            CartItem,
            user=request.user,
            product_id=product_id
        )
        
        # Check if quantity should be decreased or item should be removed
        quantity_to_remove = int(request.POST.get('quantity', 0))
        
        if quantity_to_remove >= cart_item.quantity or quantity_to_remove == 0:
            cart_item.delete()
            messages.success(request, 'Item removed from your cart!')
        else:
            cart_item.quantity -= quantity_to_remove
            cart_item.save()
            messages.success(request, 'Cart updated successfully!')
            
        return redirect('cart')

class UpdateCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        cart_item = get_object_or_404(
            CartItem,
            user=request.user,
            product_id=product_id
        )
        
        try:
            # Get the new quantity from the form
            new_quantity = int(request.POST.get('quantity', 1))
            
            # Validate quantity
            if new_quantity < 1:
                new_quantity = 1
            elif new_quantity > 3:
                new_quantity = 3
                
            # Update the quantity
            cart_item.quantity = new_quantity
            cart_item.save()
            
            messages.success(request, 'Cart updated successfully!')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity specified')
        except Exception as e:
            messages.error(request, f'Error updating cart: {str(e)}')
            
        return redirect('cart')