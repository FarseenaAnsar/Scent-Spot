from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from core.models.order import Order
from core.models.return_request import ReturnRequest
from core.models.customer import Customer

class ReturnOrderView(LoginRequiredMixin, View):
    def post(self, request):
        order_id = request.POST.get('order_id')
        reason = request.POST.get('reason')
        description = request.POST.get('description', 'No description provided.')
        condition = request.POST.get('condition')
        preferred_solution = request.POST.get('preferred_solution')
        
        try:
            # Get the order
            order = Order.objects.get(id=order_id)
            
            # Create return request
            return_request = ReturnRequest(
                order=order,
                reason=reason,
                description=description,
                condition=condition,
                preferred_solution=preferred_solution,
                status='pending'
            )
            return_request.save()
            
            # Update order status
            order.status = 'return_requested'
            order.save()
            
            messages.success(request, 'Return request submitted successfully!')
            
            # Render the return confirmation page
            return render(request, 'returns.html', {
                'return_request': return_request
            })
            
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
            return redirect('account')
        except Exception as e:
            messages.error(request, f'Error processing return request: {str(e)}')
            return redirect('account')