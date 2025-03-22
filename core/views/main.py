from django.shortcuts import render, redirect
from django.views import View
from core.models.product import Product, ProductImage
from core.models.brand import Brand

class Main(View):
    def get(self, request):
        prds = Product.get_all_products()
        p_show = []
        count = 0
        for p in prds:
            if (count < 9):
                p_show.append(p)
                count = count + 1
        brands = []
        celeb_brand = []

        br = Brand.get_all_brands()
        for b in br:
            if (b.category == "normal"):
                brands.append(b)
            else:
                celeb_brand.append(b)
        return render(request, "main.html", {"prds": p_show, "brands":brands, "celeb_brand": celeb_brand})
    
    def post(self, request):
        pass


