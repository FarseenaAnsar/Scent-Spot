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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.conf import settings
import os
from core.models.order import Order
from core.models.return_request import ReturnRequest, ReturnImage
from core.models.product import Product
from core.models.customer import Customer
from core.models.category import Category
from core.models.brand import Brand
from .forms import CategoryForm
from django.db.models import Q, F
from .forms import ProductForm
from django.utils import timezone  

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
        return Order.objects.select_related('customer', 'product').all().order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add pagination info
        page_obj = context['page_obj']
        paginator = context['paginator']
        context['is_paginated'] = page_obj.has_other_pages()
        context['total_pages'] = paginator.num_pages
        context['total_orders'] = paginator.count
        return context


class AdminOrderDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = 'adminoperations/admin_orderdetail.html'
    context_object_name = 'order'
    paginate_by = 10
    pk_url_kwarg = 'order_id'
    
    def get_queryset(self):
        return Order.objects.all().order_by('-created_at')  # Sort by newest first
    

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