from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView, DetailView, CreateView, DeleteView, View
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum
from django.conf import settings
import os
from core.models.order import Order
from core.models.return_request import ReturnRequest, ReturnImage
from core.models.product import Product
from core.models.customer import Customer
from core.models.category import Category
from core.models.brand import Brand
from core.models.offer import ProductOffer, CategoryOffer, ReferralOffer
from .forms import CategoryForm, ProductForm, ProductOfferForm, CategoryOfferForm, ReferralOfferForm
from django.db.models import Q, F
from django.utils import timezone  
from core.models.coupon import Coupon
from core.models.wallet import Wallet, WalletTransaction
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from datetime import datetime, timedelta


class StaffRequiredMixin(LoginRequiredMixin):
    """Mixin that requires the user to be staff"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('main')  # Redirect to main page if not staff
        return super().dispatch(request, *args, **kwargs)


class AdminLoginView(LoginView):
    template_name = 'adminoperations/admin_login.html'
    success_url = reverse_lazy('admin_home')
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('admin_home')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None and user.is_staff:
            login(self.request, user)
            messages.success(self.request, 'Successfully logged in as admin')
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(self.request, 'Invalid credentials or insufficient permissions')
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # Check if user is already logged in but not staff
        if request.user.is_authenticated and not request.user.is_staff:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('main')
        return super().dispatch(request, *args, **kwargs)

class AdminLogoutView(StaffRequiredMixin, LogoutView):
    next_page = reverse_lazy('admin_login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'Successfully logged out')
        return super().dispatch(request, *args, **kwargs)
    
    def get_next_page(self):
        """
        Override to customize redirect url after logout
        """
        return str(self.next_page)
    
class AdminHomeView(StaffRequiredMixin, TemplateView):
    template_name = 'adminoperations/admin_home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get dashboard statistics
        context['total_users'] = Customer.objects.count()
        context['total_products'] = Product.objects.count()
        context['total_orders'] = Order.objects.count()
        context['total_revenue'] = Order.objects.filter(status='Delivered').aggregate(
            total=Sum(F('price') * F('quantity')))['total'] or 0
        
        # Recent orders
        context['recent_orders'] = Order.objects.order_by('-date')[:5]
        
        # Top selling products
        context['top_products'] = Product.objects.annotate(
            order_count=Count('order')).order_by('-order_count')[:5]
        
        return context

class UserListView(StaffRequiredMixin, ListView):
    model = Customer
    template_name = 'adminoperations/admin_userlist.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add extra context data for each user
        users_data = []
        for user in context['users']:
            user_data = {
                'user': user,
                'total_orders': Order.objects.filter(customer=user).count(),
                'total_spent': Order.objects.filter(customer=user, status='Delivered').aggregate(
                    total=Sum(F('price') * F('quantity')))['total'] or 0,
            }
            users_data.append(user_data)
        context['users_data'] = users_data
        return context

class UserDetailView(StaffRequiredMixin, DetailView):
    model = Customer
    template_name = 'adminoperations/admin_userdetails.html'
    context_object_name = 'user'
    pk_url_kwarg = 'user_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get user's orders
        orders = Order.objects.filter(customer=user).order_by('-date') 
        context['orders'] = orders
        
        
        # Get user statistics
        context['total_orders'] = context['orders'].count()
        context['total_spent'] = context['orders'].filter(status='Delivered').aggregate(
            total=Sum(F('price') * F('quantity')))['total'] or 0
        context['order_status_count'] = context['orders'].values('status').annotate(
            count=Count('id'))
        
        return context

class CategoryListView(StaffRequiredMixin, ListView):
    model = Category
    template_name = 'adminoperations/admin_categorylist.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_categories'] = Category.objects.count()
        return context

class CategoryCreateView(StaffRequiredMixin, CreateView):
    model = Category
    template_name = 'adminoperations/admin_categoryform.html'
    form_class = CategoryForm
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)

class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Category
    template_name = 'adminoperations/admin_categoryform.html'
    form_class = CategoryForm
    pk_url_kwarg = 'category_id'  
    
    def get_success_url(self):
        return reverse('category_list')
        
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)

class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Category
    template_name = 'adminoperations/admin_categorydelete.html'
    success_url = reverse_lazy('category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Category deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'adminoperations/admin_productlist.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-name')
        search_query = self.request.GET.get('search')
        category_filter = self.request.GET.get('category')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        return context

class ProductCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'adminoperations/admin_productform.html'
    success_url = reverse_lazy('product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Product'
        context['button_text'] = 'Create Product'
        return context

    def form_valid(self, form):
        self.object = form.save()
        
        # Handle additional images
        additional_images = self.request.FILES.getlist('additional_images')
        if additional_images:
            from core.models.product import ProductImage
            import os, uuid
            from django.conf import settings
            
            for img_file in additional_images:
                # Generate unique filename for each additional image
                file_ext = os.path.splitext(img_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                
                # Define path for additional images
                images_dir = os.path.join(settings.BASE_DIR, 'core', 'static', 'images', 'additional')
                os.makedirs(images_dir, exist_ok=True)
                
                # Save the image
                img_path = os.path.join(images_dir, unique_filename)
                with open(img_path, 'wb+') as destination:
                    for chunk in img_file.chunks():
                        destination.write(chunk)
                
                # Create ProductImage instance
                ProductImage.objects.create(
                    product=self.object,
                    image=f'static/images/additional/{unique_filename}'
                )
                
        messages.success(self.request, 'Product created successfully!')
        return HttpResponseRedirect(self.get_success_url())

class ProductUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'adminoperations/admin_productform.html'
    success_url = reverse_lazy('product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Product'
        context['button_text'] = 'Update Product'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Product updated successfully!')
        return response

class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'adminoperations/admin_productdelete.html'
    success_url = reverse_lazy('product_list')
    context_object_name = 'product'

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'Product deleted successfully!')
        return response
    
    
class AdminOrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = 'adminoperations/admin_orderlist.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        # Get orders in descending order by date
        queryset = Order.objects.select_related('customer', 'product').all().order_by('-date')
        
        # Process each order to ensure customer data is available and calculate final price
        processed_orders = []
        for order in queryset:
            # If customer is None, try to find or create one based on available data
            if not order.customer and hasattr(order, 'user'):
                try:
                    # Try to find customer by email if user is available
                    customer = Customer.objects.get(email=order.user.username)
                    order.customer = customer
                    order.save()
                except (Customer.DoesNotExist, AttributeError):
                    pass
            
            # Calculate original price
            original_price = order.price
            
            # Calculate product offer discount (if applicable)
            product_discount = 0
            if hasattr(order.product, 'has_offer') and order.product.has_offer:
                product_discount = (order.product.price - order.product.get_discount_price) * order.quantity
            
            # Calculate coupon discount (if applicable)
            coupon_discount = 0
            if hasattr(order, 'coupon_discount'):
                coupon_discount = order.coupon_discount
            
            # Add convenience fee
            convenience_fee = 99  # ₹99
            
            # Calculate subtotal after product discounts
            subtotal = original_price * order.quantity - product_discount
            
            # Calculate final total
            final_total = subtotal - coupon_discount + convenience_fee
            
            # Add calculated values to order object
            order.final_total = final_total
            
            processed_orders.append(order)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add pagination info
        page_obj = context['page_obj']
        paginator = context['paginator']
        context['is_paginated'] = page_obj.has_other_pages()
        context['total_pages'] = paginator.num_pages
        context['total_orders'] = paginator.count
        
        # Process orders to ensure customer names are available in the template
        orders_with_names = []
        for order in context['orders']:
            if order.customer:
                # Ensure first_name and last_name are not None
                if not order.customer.first_name:
                    order.customer.first_name = "Customer"
                    order.customer.save()
                
                # Calculate final price if not already done
                if not hasattr(order, 'final_total'):
                    # Calculate original price
                    original_price = order.price
                    
                    # Calculate product offer discount (if applicable)
                    product_discount = 0
                    if hasattr(order.product, 'has_offer') and order.product.has_offer:
                        product_discount = (order.product.price - order.product.get_discount_price) * order.quantity
                    
                    # Calculate coupon discount (if applicable)
                    coupon_discount = 0
                    if hasattr(order, 'coupon_discount'):
                        coupon_discount = order.coupon_discount
                    
                    # Add convenience fee
                    convenience_fee = 99  # ₹99
                    
                    # Calculate subtotal after product discounts
                    subtotal = original_price * order.quantity - product_discount
                    
                    # Calculate final total
                    order.final_total = subtotal - coupon_discount + convenience_fee
                
                # Add the processed order
                orders_with_names.append(order)
            else:
                # If no customer, create a temporary attribute for display
                order.customer_name = "Unknown Customer"
                
                # Calculate final price if not already done
                if not hasattr(order, 'final_total'):
                    # Add convenience fee to original price
                    order.final_total = (order.price * order.quantity) + 99
                
                orders_with_names.append(order)
                
        context['orders'] = orders_with_names
        return context


class AdminOrderDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = 'adminoperations/admin_orderdetail.html'
    context_object_name = 'order'
    paginate_by = 10
    pk_url_kwarg = 'order_id'
    
    def get_queryset(self):
        return Order.objects.all().order_by('-created_at')  # Sort by newest first
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        
        # Calculate order totals
        order.subtotal = order.price * order.quantity
        
        # Get coupon discount - try from order model, fallback to calculation
        try:
            order.discount = float(getattr(order, 'coupon_discount', 0))
        except:
            # If coupon_discount field doesn't exist, set a default discount
            # You can modify this to calculate based on your business logic
            order.discount = 50.0  # Example: ₹50 discount for testing
        
        order.convenience_fee = 99
        order.final_total = order.subtotal - order.discount + order.convenience_fee
        
        context['order'] = order
        return context
    

class AdminOrderCancelView(StaffRequiredMixin, UpdateView):
    model = Order
    template_name = 'adminoperations/admin_ordercancel.html'
    fields = ['status']
    pk_url_kwarg = 'order_id'
    success_url = reverse_lazy('admin_order_list')

    def form_valid(self, form):
        form.instance.status = 'cancelled'
        return super().form_valid(form)

class OrderReturnView(StaffRequiredMixin, UpdateView):
    model = ReturnRequest
    template_name = 'adminoperations/admin_orderreturn.html'
    context_object_name = 'return_request'
    pk_url_kwarg = 'order_id'
    fields = ['status', 'admin_notes']

    def get_object(self):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        return_request, created = ReturnRequest.objects.get_or_create(
        order=order,
            defaults={
            'status': 'pending',
            'reason': 'Admin initiated return'
            }
        )
        return return_request

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ReturnRequest._meta.get_field('status').choices
        return context

    def form_valid(self, form):
        return_request = form.instance
        action = self.request.POST.get('action')
        
        if action == 'approve':
            return_request.status = 'approved'
            return_request.processed_date = timezone.now()
            return_request.order.status = 'return_approved'
            return_request.save()
            return_request.order.save()
            messages.success(self.request, f'Return request #{return_request.id} has been approved')
            return HttpResponseRedirect(self.get_success_url())
        
        elif action == 'reject':
            return_request.status = 'rejected'
            return_request.processed_date = timezone.now()
            return_request.order.status = 'return_rejected'
            return_request.save()
            return_request.order.save()
            messages.success(self.request, f'Return request #{return_request.id} has been rejected')
            return HttpResponseRedirect(self.get_success_url())
        
        elif action == 'complete':
            return_request.status = 'completed'
            return_request.processed_date = timezone.now()
            return_request.order.status = 'returned'
            return_request.save()
            return_request.order.save()
            messages.success(self.request, f'Return request #{return_request.id} has been marked as completed')
            return HttpResponseRedirect(self.get_success_url())
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('admin_order_list')

    
    
class BrandListView(StaffRequiredMixin, ListView):
    model = Brand
    template_name = 'adminoperations/admin_brandlist.html'
    context_object_name = 'brands'
    

class BrandCreateView(StaffRequiredMixin, CreateView):
    model = Brand
    template_name = 'adminoperations/admin_brandform.html'
    fields = ['brand_name']
    success_url = reverse_lazy('brand_list')

class BrandUpdateView(StaffRequiredMixin, UpdateView):
    model = Brand
    template_name = 'adminoperations/admin_brandform.html'
    fields = ['brand_name']
    success_url = reverse_lazy('brand_list')

class BrandDeleteView(StaffRequiredMixin, DeleteView):
    model = Brand
    template_name = 'adminoperations/admin_branddelete.html'
    success_url = reverse_lazy('brand_list')
    
# Product Offer Views
class ProductOfferListView(StaffRequiredMixin, ListView):
    model = ProductOffer
    template_name = 'adminoperations/product_offer_list.html'
    context_object_name = 'offers'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        for offer in context['offers']:
            if not offer.active:
                offer.status = "Inactive"
            elif now < offer.valid_from:
                offer.status = "Scheduled"
            elif now > offer.valid_to:
                offer.status = "Expired"
            else:
                offer.status = "Active"
        return context

class ProductOfferCreateView(StaffRequiredMixin, CreateView):
    model = ProductOffer
    form_class = ProductOfferForm
    template_name = 'adminoperations/product_offer_form.html'
    success_url = reverse_lazy('product_offer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Product offer created successfully!')
        return super().form_valid(form)

class ProductOfferUpdateView(StaffRequiredMixin, UpdateView):
    model = ProductOffer
    form_class = ProductOfferForm
    template_name = 'adminoperations/product_offer_form.html'
    success_url = reverse_lazy('product_offer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Product offer updated successfully!')
        return super().form_valid(form)

class ProductOfferDeleteView(StaffRequiredMixin, DeleteView):
    model = ProductOffer
    template_name = 'adminoperations/product_offer_delete.html'
    success_url = reverse_lazy('product_offer_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Product offer deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Category Offer Views
class CategoryOfferListView(StaffRequiredMixin, ListView):
    model = CategoryOffer
    template_name = 'adminoperations/category_offer_list.html'
    context_object_name = 'offers'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        for offer in context['offers']:
            if not offer.active:
                offer.status = "Inactive"
            elif now < offer.valid_from:
                offer.status = "Scheduled"
            elif now > offer.valid_to:
                offer.status = "Expired"
            else:
                offer.status = "Active"
        return context

class CategoryOfferCreateView(StaffRequiredMixin, CreateView):
    model = CategoryOffer
    form_class = CategoryOfferForm
    template_name = 'adminoperations/category_offer_form.html'
    success_url = reverse_lazy('category_offer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category offer created successfully!')
        return super().form_valid(form)

class CategoryOfferUpdateView(StaffRequiredMixin, UpdateView):
    model = CategoryOffer
    form_class = CategoryOfferForm
    template_name = 'adminoperations/category_offer_form.html'
    success_url = reverse_lazy('category_offer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category offer updated successfully!')
        return super().form_valid(form)

class CategoryOfferDeleteView(StaffRequiredMixin, DeleteView):
    model = CategoryOffer
    template_name = 'adminoperations/category_offer_delete.html'
    success_url = reverse_lazy('category_offer_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Category offer deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Referral Offer Views
class ReferralOfferListView(StaffRequiredMixin, ListView):
    model = ReferralOffer
    template_name = 'adminoperations/referral_offer_list.html'
    context_object_name = 'offers'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        for offer in context['offers']:
            if not offer.active:
                offer.status = "Inactive"
            elif now < offer.valid_from:
                offer.status = "Scheduled"
            elif now > offer.valid_to:
                offer.status = "Expired"
            else:
                offer.status = "Active"
            
            # Add usage info
            if offer.max_uses > 0:
                offer.usage_status = f"{offer.times_used}/{offer.max_uses}"
            else:
                offer.usage_status = f"{offer.times_used}/∞"
        return context

class ReferralOfferCreateView(StaffRequiredMixin, CreateView):
    model = ReferralOffer
    form_class = ReferralOfferForm
    template_name = 'adminoperations/referral_offer_form.html'
    success_url = reverse_lazy('referral_offer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Referral offer created successfully!')
        return super().form_valid(form)

class ReferralOfferUpdateView(StaffRequiredMixin, UpdateView):
    model = ReferralOffer
    form_class = ReferralOfferForm
    template_name = 'adminoperations/referral_offer_form.html'
    success_url = reverse_lazy('referral_offer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Referral offer updated successfully!')
        return super().form_valid(form)

class ReferralOfferDeleteView(StaffRequiredMixin, DeleteView):
    model = ReferralOffer
    template_name = 'adminoperations/referral_offer_delete.html'
    success_url = reverse_lazy('referral_offer_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Referral offer deleted successfully!')
        return super().delete(request, *args, **kwargs)
class UpdateOrderStatusView(StaffRequiredMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES).keys():
            # Set appropriate timestamps based on status
            if new_status == 'delivered':
                order.delivered_at = timezone.now()
            elif new_status == 'cancelled':
                order.cancelled_at = timezone.now()
                
            # Update the status
            order.status = new_status
            order.save()
            
            messages.success(request, f'Order status updated to {new_status.title()}')
        else:
            messages.error(request, 'Invalid status')
            
        return redirect('admin_order_details', order_id=order_id)
    
class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value', 'minimum_purchase', 
                 'valid_from', 'valid_to', 'active', 'usage_limit']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class CouponListView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        coupons = Coupon.objects.all().order_by('-valid_to')
        now = timezone.now()
        
        # Add status for each coupon
        for coupon in coupons:
            # Ensure datetime fields are timezone-aware for comparison
            valid_from = coupon.valid_from
            valid_to = coupon.valid_to
            
            if timezone.is_naive(valid_from):
                valid_from = timezone.make_aware(valid_from)
            if timezone.is_naive(valid_to):
                valid_to = timezone.make_aware(valid_to)
            
            if not coupon.active:
                coupon.status = "Inactive"
            elif now < valid_from:
                coupon.status = "Scheduled"
            elif now > valid_to:
                coupon.status = "Expired"
            else:
                coupon.status = "Active"
                
            # Check usage limit
            if coupon.usage_limit > 0:
                coupon.usage_status = f"{coupon.times_used}/{coupon.usage_limit}"
            else:
                coupon.usage_status = f"{coupon.times_used}/∞"
        
        return render(request, 'adminoperations/coupon_list.html', {'coupons': coupons})

class CreateCouponView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        form = CouponForm()
        return render(request, 'adminoperations/coupon_form.html', {'form': form, 'title': 'Create Coupon'})
    
    def post(self, request):
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon created successfully!")
            return redirect('coupon_list')
        return render(request, 'adminoperations/coupon_form.html', {'form': form, 'title': 'Create Coupon'})

class EditCouponView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        form = CouponForm(instance=coupon)
        return render(request, 'adminoperations/coupon_form.html', {'form': form, 'title': 'Edit Coupon'})
    
    def post(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully!")
            return redirect('coupon_list')
        return render(request, 'adminoperations/coupon_form.html', {'form': form, 'title': 'Edit Coupon'})

class DeleteCouponView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        return render(request, 'adminoperations/coupon_confirm_delete.html', {'coupon': coupon})
    
    def post(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.delete()
        messages.success(request, "Coupon deleted successfully!")
        return redirect('coupon_list')
    
class SalesReportView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        # Get filter parameters
        report_type = request.GET.get('report_type', 'daily')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Set default date range based on report type
        end_date = timezone.now().date()
        
        if report_type == 'daily':
            start_date = end_date
        elif report_type == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif report_type == 'monthly':
            start_date = end_date - timedelta(days=30)
        elif report_type == 'yearly':
            start_date = end_date - timedelta(days=365)
        else:  # custom
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                # Default to last 30 days if dates are invalid
                start_date = end_date - timedelta(days=30)
        
        # Query orders within date range
        orders = Order.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate sales metrics
        total_orders = orders.count()
        
        # Calculate original order amount (before discounts)
        original_amount = orders.aggregate(
            total=Sum(F('price') * F('quantity'), output_field=DecimalField())
        )['total'] or 0
        
        # Calculate actual order amount (after product offers)
        # This assumes the price field already includes product offer discounts
        actual_amount = original_amount
        
        # Calculate coupon discounts
        # This is a placeholder - you'll need to adjust based on your actual data model
        coupon_discount = 0
        
        # Group data by date for the chart - using a simpler approach
        sales_by_date = []
        chart_labels = []
        chart_data = []
        chart_counts = []
        
        # Get all orders and group them manually
        if orders.exists():
            # Create a dictionary to store data by date
            date_data = {}
            
            for order in orders:
                # Format the date based on report type
                if report_type == 'daily':
                    date_key = order.date.strftime('%Y-%m-%d')
                    display_date = order.date.strftime('%Y-%m-%d')
                elif report_type == 'weekly':
                    # Get the week number
                    week_num = order.date.isocalendar()[1]
                    year = order.date.year
                    date_key = f"{year}-W{week_num}"
                    display_date = f"Week {week_num}, {year}"
                elif report_type == 'monthly':
                    date_key = order.date.strftime('%Y-%m')
                    display_date = order.date.strftime('%b %Y')
                else:  # yearly or custom
                    date_key = order.date.strftime('%Y-%m')
                    display_date = order.date.strftime('%b %Y')
                
                # Calculate order total
                order_total = order.price * order.quantity
                
                # Add or update data for this date
                if date_key in date_data:
                    date_data[date_key]['total_sales'] += order_total
                    date_data[date_key]['order_count'] += 1
                else:
                    date_data[date_key] = {
                        'display_date': display_date,
                        'total_sales': order_total,
                        'order_count': 1
                    }
            
            # Convert dictionary to sorted list
            for date_key in sorted(date_data.keys()):
                data = date_data[date_key]
                sales_by_date.append({
                    'date_group': date_key,
                    'display_date': data['display_date'],
                    'total_sales': data['total_sales'],
                    'order_count': data['order_count']
                })
                
                # Add data for charts
                chart_labels.append(data['display_date'])
                chart_data.append(float(data['total_sales']))
                chart_counts.append(data['order_count'])
        
        # Chart data is now prepared in the previous step
        
        context = {
            'report_type': report_type,
            'start_date': start_date,
            'end_date': end_date,
            'total_orders': total_orders,
            'original_amount': original_amount,
            'actual_amount': actual_amount,
            'coupon_discount': coupon_discount,
            'product_discount': original_amount - actual_amount,
            'total_discount': (original_amount - actual_amount) + coupon_discount,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'chart_counts': chart_counts,
            'sales_by_date': sales_by_date,
        }
        
        return render(request, 'adminoperations/sales_report.html', context)
# Wallet Management Views
class AdminWalletListView(StaffRequiredMixin, ListView):
    model = WalletTransaction
    template_name = 'adminoperations/admin_wallet_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        return WalletTransaction.objects.select_related('wallet__user').order_by('-created_at')

class AdminWalletDetailView(StaffRequiredMixin, DetailView):
    model = WalletTransaction
    template_name = 'adminoperations/admin_wallet_detail.html'
    context_object_name = 'transaction'
    pk_url_kwarg = 'transaction_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction = self.get_object()
        
        # Check if transaction is related to order (return/cancel)
        related_order = None
        if 'RETURN' in transaction.transaction_id or 'CANCEL' in transaction.transaction_id:
            # Try to find related order by transaction_id pattern
            order_id = transaction.transaction_id.split('-')[-1] if '-' in transaction.transaction_id else None
            if order_id:
                try:
                    related_order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    pass
        
        context['related_order'] = related_order
        return context