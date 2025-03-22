from django.shortcuts import render, redirect
from core.models.product import Product, ProductImage
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
            additional_images = product.additional_images.all()   #aditional images
            
            cart = request.session.get("cart", {})  # Default to empty dict if no cart
            q = cart.get(prd_id, 0)  # Default to 0 if product not in cart
            q = int(q) + int(amt) if q else int(amt)
            cart[prd_id] = q
            request.session["cart"] = cart
            
            return render(request, "products.html", {
                "product": p_obj[0],
                "cat_type": type2,
                "similar_products": similar_products,
                "additional_images": additional_images  # Adding additional images to context
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
            additional_images = product.additional_images.all()
            
            return render(request, "products.html", {
                "product": p_obj[0],
                "cat_type": type2,
                "similar_products": similar_products,
                "additional_images": additional_images  # Adding additional images to context
            })
            
        # If no product_id, show all products or redirect
        products = Product.objects.all()
        products_with_images = []
        for product in products:
            additional_images = product.additional_images.all()
            products_with_images.append({
                'product': product,
                'additional_images': additional_images
            })
        return render(request, "products.html", {"products": products_with_images})

    @staticmethod
    def product_view(request):
        products = Product.objects.all()
        # Get additional images for each product
        products_data = []
        for product in products:
            additional_images = product.additional_images.all()
            products_data.append({
                'product': product,
                'additional_images': additional_images
            })
            print(f"Product: {product.name}, Rating: {product.rating}")
        return render(request, 'main.html', {'prds': products_data})
    
    @staticmethod
    def add_product_images(request, product_id):
        if request.method == 'POST' and request.FILES:
            product = get_object_or_404(Product, id=product_id)
            for image in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(
                    product=product,
                    image=image
                )
            return redirect('products')
    
