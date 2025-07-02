from django.shortcuts import render, redirect
from django.views import View
from core.models.customer import Customer
from core.models.product import Product
from core.models.order import Order
from core.models.rate import Rate
from core.models.wallet import Wallet, WalletTransaction
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import uuid
from decimal import Decimal

class OrderView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
            
        print(f"Getting orders for user: {request.user.username}")
        
        # Get customer associated with the user
        try:
            customer = Customer.objects.get(email=request.user.username)
            orders = Order.objects.filter(customer=customer)
            print(f"Found {orders.count()} orders for customer {customer.id}")
        except Customer.DoesNotExist:
            print(f"No customer found with email {request.user.username}")
            orders = []
            
        o = []
        for od in orders:
            try:
                chk_rate = Rate.check_order_id(od)
                if not chk_rate:
                    o.append(od)
            except Exception as e:
                print(f"Error checking rate for order {od.id}: {str(e)}")
                o.append(od)  # Include the order anyway
                
        print(f"Found {len(o)} orders to display")
        return render(request, "orders.html", {"order":o})
    
    def post(self, request):
        action = request.POST.get("action")
        
        if action == "cancel_order":
            order_id = request.POST.get("order_id")
            reason = request.POST.get("cancel_reason")
            
            try:
                order = Order.objects.get(id=order_id)
                
                # Check if order is in processing status
                if order.status == "processing":
                    # Increment product stock when order is cancelled
                    product = order.product
                    product.stock += order.quantity
                    product.save()
                    
                    # Calculate refund amount and add to wallet
                    from core.models.wallet import Wallet, WalletTransaction
                    import uuid
                    from decimal import Decimal
                    
                    refund_amount = (order.price * order.quantity) + 99 - (order.coupon_discount or 0)
                    
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += Decimal(str(refund_amount))
                    wallet.save()
                    
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_id=f"REFUND-{order.id}-{uuid.uuid4().hex[:6].upper()}",
                        transaction_type='DEPOSIT',
                        amount=Decimal(str(refund_amount)),
                        status='COMPLETED'
                    )
                    
                    order.status = "cancelled"
                    order.cancelled_at = timezone.now()
                    order.cancel_reason = reason
                    order.save()
                    messages.success(request, f"Order cancelled successfully. ₹{refund_amount} refunded to your wallet.")
                else:
                    messages.error(request, "Only orders in processing status can be cancelled")
                
                return redirect("orders")
            except Order.DoesNotExist:
                messages.error(request, "Order not found")
                return redirect("orders")
        else:
            # Handle existing rating functionality
            o_idd = request.POST.get("o_idd")
            p_idd = request.POST.get("p_idd")
            rating1 = request.POST.get("rate1")
            rating2 = request.POST.get("rate2")
            rating3 = request.POST.get("rate3")
            rating4 = request.POST.get("rate4")
            rating5 = request.POST.get("rate5")
            val = request.POST.get("sub_btn")
            
            customer = request.session.get("customer_id")
            order = Order.get_order_by_id(o_idd)
            orders = Order.by_customer(customer)
            o = []
            for od in orders:
                chk_rate = Rate.check_order_id(od)
                if (chk_rate):
                    pass
                else:
                    o.append(od)

            if (val == "RATE"):
                flag = 0
                if (rating1 != None):
                    flag = 1
                elif (rating2 != None):
                    flag = 2
                elif (rating3 != None):
                    flag = 3
                elif (rating4 != None):
                    flag = 4
                elif (rating5 != None):
                    flag = 5
            
                p = Product.get_product(p_idd)
                c = Customer.customer_info(str(customer))
        
                for i in p:
                    rate = Rate (
                        rating = flag,
                        product = i,
                        customer = c,
                        order = order
                    )
                Rate.place_order(rate)
                Order.rating_update(o_idd, flag)
                return redirect("orders")

            elif (val == "NOT NOW"):
                return render(request, "orders.html", {"order":o, "my_class":"hide_class"})

class CancelOrderView(View):
    def post(self, request, order_id):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            reason = request.POST.get('reason')
            
            try:
                order = Order.objects.get(id=order_id)
                
                # Check if order is in processing status
                if order.status == "processing":
                    # Increment product stock when order is cancelled
                    product = order.product
                    product.stock += order.quantity
                    product.save()
                    
                    # Calculate refund amount and add to wallet
                    from core.models.wallet import Wallet, WalletTransaction
                    import uuid
                    from decimal import Decimal
                    
                    refund_amount = (order.price * order.quantity) + 99 - (order.coupon_discount or 0)
                    
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += Decimal(str(refund_amount))
                    wallet.save()
                    
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_id=f"REFUND-{order.id}-{uuid.uuid4().hex[:6].upper()}",
                        transaction_type='DEPOSIT',
                        amount=Decimal(str(refund_amount)),
                        status='COMPLETED'
                    )
                    
                    order.status = "cancelled"
                    order.cancelled_at = timezone.now()
                    order.cancel_reason = reason
                    order.save()
                    return JsonResponse({'status': 'success', 'message': f'Order cancelled. ₹{refund_amount} refunded to wallet.'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Only orders in processing status can be cancelled'})
            except Order.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Order not found'})
        else:
            return redirect('orders')