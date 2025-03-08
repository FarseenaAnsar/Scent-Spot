from django.shortcuts import render, redirect
from core.models.product import Product
from core.models.category import Category
from core.models.rate import Rate
from django.views import View
from django.shortcuts import get_object_or_404

class Products(View):
    def post(self, request):
        amt = request.POST.get("amount")
        prd_id = request.POST.get("prdid")
        p_obj = None
        type2 = None
        
        if prd_id is not None:
            product = get_object_or_404(Product, id=prd_id)
            p_obj = Product.get_product(prd_id)
            cat = p_obj[0].category
            type2 = Category.get_category_type2(cat)
            similar_products = product.get_similar_products()

            cart = request.session.get("cart", {})  # Default to empty dict if no cart
            q = cart.get(prd_id, 0)  # Default to 0 if product not in cart
            q = int(q) + int(amt) if q else int(amt)
            cart[prd_id] = q
            request.session["cart"] = cart
            
            return render(request, "products.html", {
                "product": p_obj[0],
                "cat_type": type2,
                "similar_products": similar_products
            })
        
        # If no product_id, redirect to products list or show error
        return redirect('products')  # or wherever you want to redirect
        
    def get(self, request):
        product_id = request.GET.get("product_id")
        p_obj = None
        type2 = None
        
        if product_id is not None:
            product = get_object_or_404(Product, id=product_id)
            p_obj = Product.get_product(product_id)
            cat = p_obj[0].category
            type2 = Category.get_category_type()
            similar_products = product.get_similar_products()
            
            return render(request, "products.html", {
                "product": p_obj[0],
                "cat_type": type2,
                "similar_products": similar_products
            })
            
        # If no product_id, show all products or redirect
        products = Product.objects.all()
        return render(request, "products.html", {"products": products})

    @staticmethod
    def product_view(request):
        products = Product.objects.all()
        for product in products:
            print(f"Product: {product.name}, Rating: {product.rating}")
        return render(request, 'main.html', {'prds': products})
