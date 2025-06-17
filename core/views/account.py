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
from core.models.offer import ReferralOffer
# from core.models.ordermanage import Ordermanage
# from core.models.wallet import WalletView
from core.forms import CustomerProfileForm

class Account(LoginRequiredMixin, View):
    template_name = 'account.html'
    login_url = '/user_login/'
    form_class = CustomerProfileForm

    def get(self, request):
        # Get or create customer data
        try:
            customer = Customer.objects.get(email=request.user.username)
            
            # Update customer data if fields are empty
            if not customer.first_name and request.user.first_name:
                customer.first_name = request.user.first_name
                customer.save()
                
            if not customer.last_name and request.user.last_name:
                customer.last_name = request.user.last_name
                customer.save()
                
        except Customer.DoesNotExist:
            # Create a new customer if one doesn't exist
            customer = Customer.objects.create(
                email=request.user.username,
                first_name=request.user.first_name or "",
                last_name=request.user.last_name or "",
                phone=""  # Explicitly set phone to empty string
            )
        
        # Get context data
        context = self.get_context_data()
        
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get('action')
        order_id = request.POST.get('order_id')

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
        elif action == 'verify_email':
            return self.verify_email(request)
        
        # Handle form submission for profile update
        try:
            customer = Customer.objects.get(email=request.user.username)
        except Customer.DoesNotExist:
            # Create a new customer if one doesn't exist
            customer = Customer.objects.create(
                email=request.user.username,
                first_name=request.user.first_name or "",
                last_name=request.user.last_name or "",
                phone=""  # Explicitly set phone to empty string
            )
        
        # Get form data directly from POST
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Update customer data
        customer.first_name = first_name
        customer.last_name = last_name
        # Only update phone if it's different from first_name
        if phone != first_name:
            customer.phone = phone
            
        # Only update email if it's different and verification is not required
        if email and email != customer.email:
            # Redirect to email verification
            return redirect(f'/verify-email/?email={email}')
            
        customer.save()
        
        # Update Django user model to keep in sync
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        # Handle password change if provided
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match!')
            elif not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect!')
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Profile and password updated successfully!')
        else:
            messages.success(request, 'Profile updated successfully!')
        
        return redirect('account')

    # Removed form_valid method as we're not using Django forms anymore

    def verify_email(self, request):
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Email is required')
            return redirect('account')
            
        # Redirect to the email verification page
        return redirect(f'/verify-email/?email={email}')
        
    def get_context_data(self, **kwargs):
        try:
            # Get all required data for the account page
            customer = Customer.objects.get(email=self.request.user.username)
            
            # Generate referral code if not exists
            if not customer.referral_code:
                customer.generate_referral_code()
            
            # Fix phone field if it contains first_name value
            if customer.phone == customer.first_name:
                customer.phone = ""
                customer.save()
                
            # Ensure customer has values for all fields
            if not customer.first_name:
                customer.first_name = self.request.user.first_name or ""
            if not customer.last_name:
                customer.last_name = self.request.user.last_name or ""
            if not customer.phone:
                customer.phone = ""
            if not customer.email:
                customer.email = self.request.user.username or ""
                
            # Get only this customer's orders
            orders = Order.objects.filter(customer=customer)
            
            # Get discount from session
            discount = self.request.session.get('discount', 0)
            
            # Add discount and convenience fee to each order
            for order in orders:
                order.discount = discount
                order.convenience_fee = 99
                order.final_total = (order.price * order.quantity) - discount + 99
            
            # Get cancelled orders
            cancelled_orders = Order.objects.filter(customer=customer, status='cancelled')
            
            # Add discount and convenience fee to cancelled orders too
            for order in cancelled_orders:
                order.discount = discount
                order.convenience_fee = 99
                order.final_total = (order.price * order.quantity) - discount + 99
            
            # Get referral offers for this customer
            referral_offers = ReferralOffer.objects.filter(
                name__contains=f"Referral Bonus for {customer.first_name}",
                active=True
            )
            
            # Get referrals made by this customer
            referrals = Customer.objects.filter(referred_by=customer)
            
            wallet = Wallet.objects.filter(user=self.request.user).first()
            return_requests = ReturnRequest.objects.filter(order__customer=customer)
            addresses = Address.objects.filter(customer=customer)

            return {
                'customer': customer,
                'orders': orders,  # Only show this customer's orders
                'cancelled_orders': cancelled_orders,  # Add cancelled orders to context
                'referral_offers': referral_offers,
                'referrals': referrals,
                'wallet': wallet,
                'return_requests': return_requests,
                'addresses': addresses,
                'user': self.request.user
            }
        except Customer.DoesNotExist:
            # Create a new customer with empty phone field
            customer = Customer.objects.create(
                email=self.request.user.username,
                first_name=self.request.user.first_name or "",
                last_name=self.request.user.last_name or "",
                phone=""
            )
            
            # Generate referral code for new customer
            customer.generate_referral_code()
            
            return {
                'customer': customer,
                'orders': [],
                'referral_offers': [],
                'referrals': [],
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