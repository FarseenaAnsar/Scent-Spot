from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView, DetailView, CreateView, DeleteView
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

# This is the fixed OrderReturnView class
class OrderReturnView(LoginRequiredMixin, UpdateView):
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
        context['status_choices'] = ReturnRequest.STATUS_CHOICES
        return context

    def form_valid(self, form):
        return_request = form.instance
        action = self.request.POST.get('action')
        
        if action == 'approve':
            return_request.status = 'approved'
            return_request.processed_date = timezone.now()
            return_request.order.status = 'return_approved'
            return_request.order.save()
            messages.success(self.request, f'Return request #{return_request.id} has been approved')
        
        elif action == 'reject':
            return_request.status = 'rejected'
            return_request.processed_date = timezone.now()
            return_request.order.status = 'return_rejected'
            return_request.order.save()
            messages.success(self.request, f'Return request #{return_request.id} has been rejected')
        
        elif action == 'complete':
            return_request.status = 'completed'
            return_request.processed_date = timezone.now()
            return_request.order.status = 'returned'
            return_request.order.save()
            messages.success(self.request, f'Return request #{return_request.id} has been marked as completed')
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('admin_order_list')