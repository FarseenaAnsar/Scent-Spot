
from django.shortcuts import render, redirect
from django.views import View
from core.models.order import Order

class Ordermanage(View):
    def get(self, request):
        orders = Order.get_all_orders()
        return render(request, "ordermanage.html", {"order":orders})
    
    def post(self, request):
        status = request.POST.get("status")
        id = request.POST.get("id")
        orders = Order.get_all_orders()
        Order.status_update(id, status)
        return render(request, "ordermanage.html", {"order":orders})
