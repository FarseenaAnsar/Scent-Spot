from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from core.models.wallet import Wallet, WalletTransaction
import uuid

class WalletView(LoginRequiredMixin, View):
    template_name = 'wallet.html'
    
    def get(self, request):
        try:
            # Get or create wallet for the user
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            # Get all transactions for the user
            transactions = WalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')
            
            context = {
                'wallet': wallet,
                'transactions': transactions,
                'balance': wallet.balance
            }
            return render(request, self.template_name, context)
        except Exception as e:
            messages.error(request, "Error fetching wallet details")
            return redirect('home')

    def post(self, request):
        try:
            amount = float(request.POST.get('amount', 0))
            
            if amount <= 0:
                messages.error(request, "Amount must be greater than 0")
                return redirect('wallet')
            
            wallet = Wallet.objects.get(user=request.user)
            
            # Create transaction record
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_id=str(uuid.uuid4())[:10],
                transaction_type='DEPOSIT',
                amount=amount,
                status='PENDING'
            )
            
            # Here you would typically integrate with a payment gateway
            # For demonstration, we'll directly add the money
            wallet.balance += amount
            wallet.save()
            
            # Update transaction status
            transaction.status = 'COMPLETED'
            transaction.save()
            
            messages.success(request, f"₹{amount} added to wallet successfully")
            return redirect('wallet')
            
        except Wallet.DoesNotExist:
            messages.error(request, "Wallet not found")
            return redirect('wallet')
        except ValueError:
            messages.error(request, "Invalid amount")
            return redirect('wallet')
        except Exception as e:
            messages.error(request, "Error processing transaction")
            return redirect('wallet')

class WithdrawMoneyView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            amount = float(request.POST.get('amount', 0))
            
            if amount <= 0:
                messages.error(request, "Amount must be greater than 0")
                return redirect('wallet')
            
            wallet = Wallet.objects.get(user=request.user)
            
            if wallet.balance < amount:
                messages.error(request, "Insufficient balance")
                return redirect('wallet')
            
            # Create withdrawal transaction
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_id=str(uuid.uuid4())[:10],
                transaction_type='WITHDRAWAL',
                amount=amount,
                status='PENDING'
            )
            
            # Process withdrawal (you would typically integrate with payment gateway here)
            wallet.balance -= amount
            wallet.save()
            
            transaction.status = 'COMPLETED'
            transaction.save()
            
            messages.success(request, f"₹{amount} withdrawn successfully")
            return redirect('wallet')
            
        except Exception as e:
            messages.error(request, "Error processing withdrawal")
            return redirect('wallet')
