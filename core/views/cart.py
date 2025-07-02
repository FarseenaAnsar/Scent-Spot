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
from django.http import JsonResponse


class Cart(LoginRequiredMixin, View):
    login_url = '/login/'  
    template_name = 'cart.html'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access your cart.')
            return redirect('login')  
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        # Get cart items from database
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        
        # Calculate subtotal (original price before any discounts)
        subtotal = 0
        for item in cart_items:
            subtotal += item.product.price * item.quantity
        
        # Calculate cart total with product/category offer discounts
        cart_total = 0
        for item in cart_items:
            if hasattr(item.product, 'has_offer') and item.product.has_offer:
                cart_total += item.product.get_discount_price * item.quantity
            else:
                cart_total += item.product.price * item.quantity
        
        # Calculate offer discount amount
        offer_discount = subtotal - cart_total
        
        # Apply coupon discount if available
        coupon_discount = 0
        if 'discount' in request.session:
            coupon_discount = request.session['discount']
        
        # Add convenience fee
        convenience_fee = 99  # ₹99
        
        # Calculate final total
        final_total = cart_total - coupon_discount + convenience_fee
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'offer_discount': offer_discount,
            'cart_total': cart_total,
            'coupon_discount': coupon_discount,
            'convenience_fee': convenience_fee,
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
        
        # Calculate subtotal (original price before any discounts)
        subtotal = 0
        for item in cart_items:
            subtotal += item.product.price * item.quantity
        
        # Calculate cart total with product/category offer discounts
        cart_total = 0
        for item in cart_items:
            if hasattr(item.product, 'has_offer') and item.product.has_offer:
                cart_total += item.product.get_discount_price * item.quantity
            else:
                cart_total += item.product.price * item.quantity
        
        # Calculate offer discount amount
        offer_discount = subtotal - cart_total
        
        # Apply coupon discount if available
        coupon_discount = 0
        if 'discount' in request.session:
            coupon_discount = request.session['discount']
        
        # Add convenience fee
        convenience_fee = 99  # ₹99
        
        # Calculate final total
        final_total = cart_total - coupon_discount + convenience_fee
            
        if not cart_items:
            messages.info(request, "There are no products in the cart. Let's add some products!")
            return render(request, self.template_name, {
                "cart_items": []
            })
            
        return render(request, self.template_name, {
            "cart_items": cart_items,
            "subtotal": subtotal,
            "offer_discount": offer_discount,
            "cart_total": cart_total,
            "coupon_discount": coupon_discount,
            "convenience_fee": convenience_fee,
            "final_total": final_total
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
            
            # Check quantity limits
            max_allowed = min(3, product.stock)
            if quantity > max_allowed:
                if product.stock < 3:
                    messages.error(request, f"Only {product.stock} items available in stock!")
                else:
                    messages.error(request, "Maximum 3 items allowed per order!")
                return redirect(request.META.get('HTTP_REFERER', 'cart'))
            
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                new_quantity = cart_item.quantity + quantity
                max_allowed = min(3, product.stock)
                
                if new_quantity > max_allowed:
                    if product.stock < 3:
                        messages.error(request, f"Only {product.stock} items available in stock!")
                    else:
                        messages.error(request, "Maximum 3 items allowed per order!")
                    return redirect('cart')
                    
                cart_item.quantity = new_quantity
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
            
            # Validate quantity with stock limits
            max_allowed = min(3, cart_item.product.stock)
            if new_quantity < 1:
                new_quantity = 1
            elif new_quantity > max_allowed:
                new_quantity = max_allowed
                if cart_item.product.stock < 3:
                    messages.warning(request, f"Only {cart_item.product.stock} items available in stock!")
                else:
                    messages.warning(request, "Maximum 3 items allowed per order!")
                
            # Update the quantity
            cart_item.quantity = new_quantity
            cart_item.save()
            
            # For AJAX requests, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Calculate subtotal and totals with offer prices
                cart_items = CartItem.objects.filter(user=request.user).select_related('product')
                
                # Calculate subtotal (original price before any discounts)
                subtotal = 0
                for item in cart_items:
                    subtotal += item.product.price * item.quantity
                
                # Calculate cart total with product/category offer discounts
                cart_total = 0
                for item in cart_items:
                    if hasattr(item.product, 'has_offer') and item.product.has_offer:
                        cart_total += item.product.get_discount_price * item.quantity
                    else:
                        cart_total += item.product.price * item.quantity
                
                # Calculate offer discount amount
                offer_discount = subtotal - cart_total
                
                # Apply coupon discount if available
                coupon_discount = 0
                if 'discount' in request.session:
                    coupon_discount = request.session['discount']
                
                # Add convenience fee
                convenience_fee = 99  # ₹99
                
                # Calculate final total
                final_total = cart_total - coupon_discount + convenience_fee
                
                # Calculate item total with offer price if applicable
                item_total = 0
                if hasattr(cart_item.product, 'has_offer') and cart_item.product.has_offer:
                    item_total = cart_item.product.get_discount_price * cart_item.quantity
                else:
                    item_total = cart_item.product.price * cart_item.quantity
                
                return JsonResponse({
                    'success': True,
                    'subtotal': subtotal,
                    'offer_discount': offer_discount,
                    'cart_total': cart_total,
                    'coupon_discount': coupon_discount,
                    'convenience_fee': convenience_fee,
                    'final_total': final_total,
                    'item_total': item_total
                })
            
            messages.success(request, 'Cart updated successfully!')
            return redirect('cart')
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity specified')
            return redirect('cart')
        except Exception as e:
            messages.error(request, f'Error updating cart: {str(e)}')
            return redirect('cart')