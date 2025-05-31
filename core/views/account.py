# views.py
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
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
from core.models.address import Address
# from core.models.ordermanage import Ordermanage
# from core.models.wallet import WalletView
from core.forms import CustomerProfileForm

class Account(LoginRequiredMixin, View):
    template_name = 'account.html'
    login_url = '/user_login/'
    form_class = CustomerProfileForm

    def get(self, request):
        # Create form instance with customer data
        try:
            customer = Customer.objects.get(email=request.user.username)
        except Customer.DoesNotExist:
            # Create a new customer if one doesn't exist
            customer = Customer.objects.create(
                email=request.user.username,
                first_name=request.user.first_name,
                last_name=request.user.last_name
            )
        
        form = self.form_class(instance=customer)
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get('action')
        order_id = request.POST.get('order_id')
        form = None  # Initialize form variable

        if action == 'cancel':
            return self.cancel_order(request, order_id)
        elif action == 'return':
            return self.return_order(request, order_id)
        elif action == 'add_address':
            return self.add_address(request)
        elif action == 'edit_address':
            return self.edit_address(request)
        elif action == 'delete_address':
            return self.delete_address(request)
        elif action == 'set_default_address':
            return self.set_default_address(request)
        
        # Handle form submission for profile update
        try:
            customer = Customer.objects.get(email=request.user.username)
        except Customer.DoesNotExist:
            # Create a new customer if one doesn't exist
            customer = Customer.objects.create(
                email=request.user.username,
                first_name=request.user.first_name,
                last_name=request.user.last_name
            )
        
        form = self.form_class(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            
            # Handle password change if provided
            if form.cleaned_data.get('new_password'):
                if form.cleaned_data['new_password'] != form.cleaned_data['confirm_password']:
                    messages.error(request, 'New passwords do not match!')
                elif not request.user.check_password(form.cleaned_data['current_password']):
                    messages.error(request, 'Current password is incorrect!')
                else:
                    request.user.set_password(form.cleaned_data['new_password'])
                    request.user.save()
                    messages.success(request, 'Profile and password updated successfully!')
            else:
                messages.success(request, 'Profile updated successfully!')
            
            return redirect('account')
        
        # If we get here, there was an error
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

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
            addresses = Address.objects.filter(customer=customer)

            return {
                'customer': customer,
                'orders': orders,
                'wishlist': wishlist,
                'wallet': wallet,
                'return_requests': return_requests,
                'addresses': addresses,
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
                'addresses': [],
                'user': self.request.user
            }

    def add_address(self, request):
        customer = Customer.objects.get(email=request.user.username)
        is_default = request.POST.get('is_default') == 'on'
        
        # If this is the first address or set as default, unset other defaults
        if is_default:
            Address.objects.filter(customer=customer, is_default=True).update(is_default=False)
        
        Address.objects.create(
            customer=customer,
            address_line1=request.POST.get('address_line1'),
            address_line2=request.POST.get('address_line2', ''),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postal_code=request.POST.get('postal_code'),
            is_default=is_default
        )
        messages.success(request, 'Address added successfully!')
        return redirect('account')

    def edit_address(self, request):
        address_id = request.POST.get('address_id')
        address = get_object_or_404(Address, id=address_id)
        is_default = request.POST.get('is_default') == 'on'
        
        # If setting as default, unset other defaults
        if is_default and not address.is_default:
            Address.objects.filter(customer=address.customer, is_default=True).update(is_default=False)
        
        # Update address fields
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2', '')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.postal_code = request.POST.get('postal_code')
        address.is_default = is_default
        address.save()
        
        messages.success(request, 'Address updated successfully!')
        return redirect('account')

    def delete_address(self, request):
        address_id = request.POST.get('address_id')
        address = get_object_or_404(Address, id=address_id)
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('account')

    def set_default_address(self, request):
        customer = Customer.objects.get(email=request.user.username)
        address_id = request.POST.get('address_id')
        
        # Unset all default addresses
        Address.objects.filter(customer=customer, is_default=True).update(is_default=False)
        
        # Set the selected address as default
        address = get_object_or_404(Address, id=address_id)
        address.is_default = True
        address.save()
        
        messages.success(request, 'Default address updated successfully!')
        return redirect('account')

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