# views.py
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from core.views.orders import Order
from core.models.order import Order
from core.models.return_request import ReturnRequest
from core.models.wishlist import Wishlist
from core.models.wallet import Wallet
from core.models.customer import Customer
# from core.models.ordermanage import Ordermanage
# from core.models.wallet import WalletView
from core.forms import CustomerProfileForm

class Account(LoginRequiredMixin, View):
    template_name = 'account.html'
    login_url = '/login'
    form_class = CustomerProfileForm

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get('action')
        order_id = request.POST.get('order_id')

        if action == 'cancel':
            return self.cancel_order(request, order_id)
        elif action == 'return':
            return self.return_order(request, order_id)
        
        return redirect('account')

    def form_valid(self, form):
        if form.cleaned_data.get('new_password'):
            if form.cleaned_data['new_password'] != form.cleaned_data['confirm_password']:
                messages.error(self.request, 'New passwords do not match!')
                return self.form_invalid(form)
            
            if not self.request.user.check_password(form.cleaned_data['current_password']):
                messages.error(self.request, 'Current password is incorrect!')
                return self.form_invalid(form)
            
            self.request.user.set_password(form.cleaned_data['new_password'])
            self.request.user.save()
            messages.success(self.request, 'Profile updated successfully!')
        
        return super().form_valid(form)

    
    def get_context_data(self, **kwargs):
        
        try:
        # Get all required data for the account page
            
            customer = Customer.objects.get(email=self.request.user.username)
            orders = Order.objects.filter(customer=customer).order_by('-date')
            wishlist = Wishlist.objects.filter(user=self.request.user)
            wallet = Wallet.objects.filter(user=self.request.user).first()
            return_requests = ReturnRequest.objects.filter(order__customer=customer)

            return {
                'customer': customer,
                'orders': orders,
                'wishlist': wishlist,
                'wallet': wallet,
                'return_requests': return_requests,
                'user': self.request.user
            }
        except Customer.DoesNotExist:
            customer = Customer.objects.create(
                email=self.request.user.email,
                first_name=self.request.user.first_name,
                last_name=self.request.user.last_name
            )
            
            return {
                'customer': customer,
                'orders': [],
                'wishlist': Wishlist.objects.filter(user=self.request.user),
                'wallet': Wallet.objects.filter(user=self.request.user).first(),
                'return_requests': [],
                'user': self.request.user
            }

    def cancel_order(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
            
            # Check if order is eligible for cancellation
            if order.status in ['PENDING', 'PROCESSING']:
                # Refund amount to wallet
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.balance += order.total_amount
                wallet.save()

                # Update order status
                order.status = 'CANCELLED'
                order.cancelled_at = timezone.now()
                order.save()

                messages.success(request, 'Order cancelled successfully. Amount refunded to wallet.')
            else:
                messages.error(request, 'This order cannot be cancelled.')

        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')

        return redirect('account')

    def return_order(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            
            # Check if order is eligible for return (e.g., within 7 days of delivery)
            if order.status == 'DELIVERED' and (timezone.now() - order.delivered_at).days <= 7:
                # Create return request
                ReturnRequest.objects.create(
                    order=order,
                    reason=request.POST.get('return_reason', ''),
                    status='PENDING'
                )
                
                order.status = 'RETURN_REQUESTED'
                order.save()

                messages.success(request, 'Return request submitted successfully.')
            else:
                messages.error(request, 'This order is not eligible for return.')

        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')

        return redirect('account')
