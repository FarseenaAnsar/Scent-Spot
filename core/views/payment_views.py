from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

class PaymentFailureView(LoginRequiredMixin, TemplateView):
    template_name = 'payment_failure.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get error message from query parameters if available
        error_message = self.request.GET.get('error_message', '')
        order_id = self.request.GET.get('order_id', '')
        
        context['error_message'] = error_message
        context['order_id'] = order_id
        
        return context