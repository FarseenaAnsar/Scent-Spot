from django.shortcuts import render, redirect
from core.models.product import Product, ProductImage
from core.models.category import Category
from core.models.rate import Rate
from django.views import View
from django.shortcuts import get_object_or_404
from core.models.product import PerfumeAttributes
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

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
        
        if product_id:
            try:
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
                    "additional_images": additional_images
                })
            except (Product.DoesNotExist, ValueError):
                # Handle invalid product_id
                return redirect('products')
                
        # If no product_id, show all products
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
    

class PerfumeFinder(View):
    def get(self, request):
        return render(request, 'perfume_finder.html')

    def post(self, request):
        # to Get user preferences from the form
        preferences = {
            'scent_family': request.POST.get('scent_family'),
            'occasion': request.POST.get('occasion'),
            'season': request.POST.get('season'),
            'gender': request.POST.get('gender'),
        }

        # to Get all perfumes
        perfumes = PerfumeAttributes.objects.all()

        # to Create feature vectors
        mlb = MultiLabelBinarizer()
        
        # to Convert perfume attributes to features
        perfume_features = []
        for perfume in perfumes:
            features = [
                perfume.scent_family.split(','),
                perfume.occasion.split(','),
                perfume.season.split(','),
                perfume.gender.split(',')
            ]
            perfume_features.append([item for sublist in features for item in sublist])

        # to Convert user preferences to features
        user_features = [
            preferences['scent_family'].split(','),
            preferences['occasion'].split(','),
            preferences['season'].split(','),
            preferences['gender'].split(',')
        ]
        user_features = [item for sublist in user_features for item in sublist]

        # to Transform features to binary matrix
        X = mlb.fit_transform(perfume_features)
        user_X = mlb.transform([user_features])

        # Calculating similarity scores
        similarities = cosine_similarity(user_X, X)[0]

        # to Get top 5 recommendations
        top_indices = np.argsort(similarities)[-5:][::-1]
        recommended_perfumes = [perfumes[int(i)].product for i in top_indices]    # Converting np.int64 to regular Python int before indexing

        return render(request, 'perfume_finder.html', {
            'recommendations': recommended_perfumes
        })
        

