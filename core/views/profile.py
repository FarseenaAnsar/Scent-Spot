from django.shortcuts import render, redirect
from django.views import View
from core.models.customer import Customer
from core.models.product import Product
from core.models.order import Order
from core.models.rate import Rate

class Profile(View):
    def get(self, request):
        info = request.GET.get("info")

        idd = request.session.get("customer_id")
        c_info = Customer.customer_info(idd)

        if (info == "personal"):
            return render(request, "profile.html", {"information":c_info, "type":"personal"})
        elif (info == "order"):
            o_info = Order.by_customer(c_info)
            return render(request, "profile.html", {"orders":o_info, "type":"order"})
        elif (info == "purchased"):
            o_info = Order.by_customer(c_info)
            p_o = []
            for o in o_info:
                if (o.status == "delivered"):
                    p_o.append(o)
                    r = Rate.check_order_id(o)
            return render(request, "profile.html", {"purchased":p_o, "type":"purchased"})
        return render(request, "profile.html")

    def post(self, request):
        o_idd = request.POST.get("o_idd")
        p_idd = request.POST.get("p_idd")
        rating1 = request.POST.get("rate1")
        rating2 = request.POST.get("rate2")
        rating3 = request.POST.get("rate3")
        rating4 = request.POST.get("rate4")
        rating5 = request.POST.get("rate5")
        
        customer = request.session.get("customer_id")
        orders = Order.by_customer(customer)
        order = Order.get_order_by_id(o_idd)

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
        return redirect("profile")