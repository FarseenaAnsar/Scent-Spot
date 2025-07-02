from django.shortcuts import render, redirect
from core.models.product import Product, ProductImage
from core.models.category import Category
from core.models.rate import Rate
from django.views import View
from django.shortcuts import get_object_or_404
from core.models.product import PerfumeAttributes
from core.models.cart import CartItem
from core.models.wishlist import Wishlist
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.utils.offer_utils import get_offer_details

class Products(View):
    def post(self, request):
        amt = request.POST.get("amount")
        prd_id = request.POST.get("prdid")
        p_obj = None
        type2 = None
        
        # Add request to product for template filter access
        Product.add_to_class('_request', None)
        setattr(Product, '_request', request)
        
        if prd_id is not None:
            product = get_object_or_404(Product, id=prd_id)
            p_obj = Product.get_product(prd_id)
            cat = p_obj[0].category
            type2 = Category.get_category_type2(cat)
            similar_products = product.get_similar_products()
            additional_images = product.additional_images.all()   #aditional images
            
            # Get perfume attributes if they exist
            try:
                perfume_attributes = PerfumeAttributes.objects.get(product=product)
            except PerfumeAttributes.DoesNotExist:
                perfume_attributes = None
            
            # Check if product is in stock
            if product.stock < 1:
                messages.error(request, f"{product.name} is out of stock!")
                return render(request, "products.html", {
                    "product": p_obj[0],
                    "cat_type": type2,
                    "similar_products": similar_products,
                    "additional_images": additional_images,
                    "perfume_attributes": perfume_attributes,
                    "out_of_stock": True
                })
            
            # If in stock, proceed with adding to cart
            if request.user.is_authenticated:
                # Add to database cart for logged-in users
                try:
                    quantity = int(amt)
                    
                    # Check if requested quantity exceeds stock
                    if quantity > product.stock:
                        messages.error(request, f"Only {product.stock} items available in stock!")
                        return render(request, "products.html", {
                            "product": p_obj[0],
                            "cat_type": type2,
                            "similar_products": similar_products,
                            "additional_images": additional_images,
                            "perfume_attributes": perfume_attributes,
                            "out_of_stock": product.stock < 1
                        })
                    
                    cart_item, created = CartItem.objects.get_or_create(
                        user=request.user,
                        product=product,
                        defaults={'quantity': quantity}
                    )
                    
                    if not created:
                        # Check if adding more would exceed available stock
                        if cart_item.quantity + quantity > product.stock:
                            available = product.stock - cart_item.quantity
                            if available <= 0:
                                messages.error(request, f"You already have the maximum available quantity in your cart!")
                            else:
                                messages.error(request, f"Only {available} more items can be added to cart!")
                            return render(request, "products.html", {
                                "product": p_obj[0],
                                "cat_type": type2,
                                "similar_products": similar_products,
                                "additional_images": additional_images,
                                "perfume_attributes": perfume_attributes,
                                "out_of_stock": product.stock < 1
                            })
                        
                        cart_item.quantity += quantity
                        cart_item.save()
                        messages.success(request, 'Cart updated successfully!')
                    else:
                        messages.success(request, 'Item added to your cart!')
                        
                    # Also update session cart for consistency
                    cart = request.session.get("cart", {})
                    cart[str(prd_id)] = cart_item.quantity
                    request.session["cart"] = cart
                except Exception as e:
                    messages.error(request, f'Error adding item to cart: {str(e)}')
            else:
                # Use session cart for non-logged in users
                cart = request.session.get("cart", {})
                q = cart.get(str(prd_id), 0)
                quantity = int(amt)
                
                # Check if requested quantity exceeds stock
                if quantity > product.stock:
                    messages.error(request, f"Only {product.stock} items available in stock!")
                    return render(request, "products.html", {
                        "product": p_obj[0],
                        "cat_type": type2,
                        "similar_products": similar_products,
                        "additional_images": additional_images,
                        "perfume_attributes": perfume_attributes,
                        "out_of_stock": product.stock < 1
                    })
                
                # Check if adding more would exceed available stock
                if int(q) + quantity > product.stock:
                    available = product.stock - int(q)
                    if available <= 0:
                        messages.error(request, f"You already have the maximum available quantity in your cart!")
                    else:
                        messages.error(request, f"Only {available} more items can be added to cart!")
                    return render(request, "products.html", {
                        "product": p_obj[0],
                        "cat_type": type2,
                        "similar_products": similar_products,
                        "additional_images": additional_images,
                        "perfume_attributes": perfume_attributes,
                        "out_of_stock": product.stock < 1
                    })
                    
                q = int(q) + quantity if q else quantity
                cart[str(prd_id)] = q
                request.session["cart"] = cart
            
            return render(request, "products.html", {
                "product": p_obj[0],
                "cat_type": type2,
                "similar_products": similar_products,
                "additional_images": additional_images,
                "perfume_attributes": perfume_attributes,
                "out_of_stock": product.stock < 1
            })
        
        return redirect('products')
        
    def get(self, request):
        # Add request to product for template filter access
        Product.add_to_class('_request', None)
        setattr(Product, '_request', request)
            
        product_id = request.GET.get("product_id")
        
        if product_id:
            try:
                product = get_object_or_404(Product, id=product_id)
                p_obj = Product.get_product(product_id)
                cat = p_obj[0].category
                type2 = Category.get_category_type()
                similar_products = product.get_similar_products()
                additional_images = product.additional_images.all()
                
                # Get perfume attributes if they exist
                try:
                    perfume_attributes = PerfumeAttributes.objects.get(product=product)
                except PerfumeAttributes.DoesNotExist:
                    perfume_attributes = None
                
                return render(request, "products.html", {
                    "product": p_obj[0],
                    "cat_type": type2,
                    "similar_products": similar_products,
                    "additional_images": additional_images,
                    "perfume_attributes": perfume_attributes,
                    "out_of_stock": product.stock < 1
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
                'additional_images': additional_images,
                'out_of_stock': product.stock < 1
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
                'additional_images': additional_images,
                'out_of_stock': product.stock < 1
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


class ProductListView(View):
    def get(self, request, category_id=None):
        if category_id:
            products = Product.get_spf_products(category_id)
            category_name = products[0].category.name if products else "Products"
        else:
            products = Product.get_all_products()
            category_name = "All Products"
        
        # Apply filters if provided
        gender = request.GET.get('gender')
        sort = request.GET.get('sort')
        brand = request.GET.getlist('brand')
        
        if gender:
            products = Product.gen_filter(gender, products)
        
        if sort:
            products = Product.sorting(sort, products)
        
        if brand:
            products = Product.brandfilter(brand, products)
        
        # Get all available brands for filter
        all_brands = Product.get_brands()
        
        context = {
            'products': products,
            'category_name': category_name,
            'all_brands': all_brands,
            'selected_gender': gender,
            'selected_sort': sort,
            'selected_brands': brand,
        }
        
        return render(request, 'product_list.html', context)


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