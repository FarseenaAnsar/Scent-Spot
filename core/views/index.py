from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from core.models.product import Product
from core.models.rate import Rate
from core.models.category import Category
from django.views import View
from django.db.models import Q
import math

class Index(View):
    def post(self, request):
        amt = request.POST.get("amount")
        prd_id = request.POST.get("prdid")
        if (prd_id != None):
            cart = request.session.get("cart")  
            if cart:
                q = cart.get(prd_id)
                if q:
                    q = int(q) + int(amt)
                else:
                    q = amt
                cart[prd_id] = q
            else:
                cart = {} 
                cart[prd_id] = amt
            
            request.session["cart"] = cart
            return redirect("index")
        
        applied_filters = []
        prds = Product.get_all_products()
        cat_ty = Category.get_category_type()
        brands = Product.get_brands()
        b = list()
        for br in brands:
            b.append(br["brand"])
        sort = ["Low To High", "High To Low"]
        gender = ["Male", "Female"]
        
        genderr = request.POST.get("gender")
        if (genderr):
            applied_filters.append(genderr)
            prds = Product.gen_filter(genderr, prds)
        sorting = request.POST.get("sort")
        if (sorting):
            applied_filters.append(sorting)
            prds = Product.sorting(sorting, prds)
        brands = request.POST.getlist("brands")
        if (brands):
            applied_filters.append(brands)
            prds = Product.brandfilter(brands, prds)
        category = request.POST.getlist("category")
        if (category):
            applied_filters.append(category)
            prds = self.filter_category(prds, category)
        search = request.POST.get("search")
        if (search):
            s = []
            s.append(search)
            prds = Product.get_all_products()
            prds1 = self.filter_category(prds, s)
            if (prds1):
                return render(request, "index.html", {"products": prds1, "gender":gender, "sort":sort, "category":cat_ty, "brands":b})
            else:
                prds2 = Product.brandfilter(s, prds)
                if (prds2):
                    return render(request, "index.html", {"products": prds2, "gender":gender, "sort":sort, "category":cat_ty, "brands":b})
                else:
                    prds3 = Product.gen_filter(search, prds)
                    if (prds3):
                        print("c")
                        return render(request, "index.html", {"products": prds3, "gender":gender, "sort":sort, "category":cat_ty, "brands":b})
                    else:
                        pass
        return render(request, "index.html", {"products": prds, "gender":gender, "sort":sort, "category":cat_ty, "brands":b, "applied_filters":applied_filters})

    def get(self, request):
        # Check if this is a product list view request
        if request.path == '/products/list/' or request.path.startswith('/products/category/'):
            return self.product_list_view(request)
            
        # Regular index view
        cart = request.session.get("cart")  
        if cart == False:
            cart = {}

        prds = Product.get_all_products()
        self.add_rating(prds)
        cat_ty = Category.get_category_type()
        brands = Product.get_brands()
        b = list()
        for br in brands:
            b.append(br["brand"])
        sort = ["Low To High", "High To Low"]
        gender = ["Male", "Female"]
        return render(request, "index.html", {"products": prds, "gender":gender, "sort":sort, "category":cat_ty, "brands":b, "show_advanced_filters": False})

    def filter_category(self, prds, category):
        num = []
        for c in category:
            cat_num = Category.get_cat_num(c)
            num.append(cat_num)
        flatten_list = sum(num, [])
        prds = Product.typee(flatten_list, prds)
        return prds
    
    def add_rating(self, prds):
        for p in prds:
            pr = Rate.objects.filter(product = p)
            len = pr.count()
            if(len != 0):
                prate = 0
                for p_obj in pr:
                    prate = prate + p_obj.rating
                p.rating = math.floor(prate / len)
                p.save()
            else:
                p.rating = 0
                p.save()
                
    def product_list_view(self, request):
        # Get category_id from URL if available
        category_id = None
        if request.path.startswith('/products/category/'):
            try:
                category_id = int(request.path.split('/')[-2])
            except (ValueError, IndexError):
                pass
                
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
            'show_advanced_filters': True
        }
        
        return render(request, 'index.html', context)