from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from core.models.wishlist import Wishlist
from core.models.product import Product  
from django.views.generic import View, ListView
from django.urls import reverse_lazy


class WishlistView(LoginRequiredMixin, View):
    template_name = 'wishlist.html'
    login_url = '/login/'  
    context_object_name = 'wishlist_items'
    paginate_by = 10  # Number of items per page
    
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_items'] = self.get_queryset().count()
        return context

    def get(self, request):
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
        context = {
            'wishlist_items': wishlist_items
        }
        return render(request, self.template_name, context)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access your wishlist.')
            return redirect('login')  
        return super().dispatch(request, *args, **kwargs)

class AddToWishlistView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        
        # Check if item already exists in wishlist
        product, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            messages.success(request, 'Item added to your wishlist!')
        else:
            messages.info(request, 'Item is already in your wishlist!')
            
        return redirect('wishlist')

class RemoveFromWishlistView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()
        
        messages.success(request, 'Item removed from your wishlist!')
        return redirect('wishlist')
