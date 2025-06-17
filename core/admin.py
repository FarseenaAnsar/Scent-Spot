from django.contrib import admin
from django.utils.html import mark_safe
from .models.product import Product, ProductImage, PerfumeAttributes
from .models.category import Category
from .models.customer import Customer
from .models.order import Order
from .models.rate import Rate
from .models.brand import Brand
from core.models.coupon import Coupon
from core.models import *
from .models.offer import ProductOffer, CategoryOffer, ReferralOffer

class AdminProduct(admin.ModelAdmin):
    list_display = ["name", "price", "brand", "gender", "size", "category"]

class AdminCategory(admin.ModelAdmin):
    list_display = ["id", "name", "description"]

class AdminCustomer(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "email", "phone", "password"]

class AdminOrder(admin.ModelAdmin):
    list_display = ["product", "customer", "quantity", "price", "adress", "phone", "date", "status"]

class AdminRate(admin.ModelAdmin):
    list_display = ["rating", "product", "customer"]

class AdminBrand(admin.ModelAdmin):
    def image_display(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "No image"
    
    image_display.short_description = 'Image'  # Column header in admin
    
    list_display = ["brand_name", "image_display", "category"]  # Change 'image' to 'image_display'


class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'valid_from', 
                    'valid_to', 'active', 'usage_limit', 'times_used']
    list_filter = ['active', 'valid_from', 'valid_to', 'discount_type']
    search_fields = ['code']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3

class PerfumeAttributesInline(admin.StackedInline):
    model = PerfumeAttributes
    can_delete = False

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'stock', 'has_offer', 'get_discount_price']
    list_filter = ['category', 'brand', 'gender']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline, PerfumeAttributesInline]

class ProductOfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'discount_percentage', 'valid_from', 'valid_to', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['name', 'product__name']

class CategoryOfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'discount_percentage', 'valid_from', 'valid_to', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['name', 'category__name']
    
# Register your models here.
admin.site.register(Product, AdminProduct)
admin.site.register(Customer, AdminCustomer)
admin.site.register(Category, AdminCategory)
admin.site.register(Order, AdminOrder)
admin.site.register(Rate, AdminRate)
admin.site.register(Brand, AdminBrand)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(ProductOffer)
admin.site.register(CategoryOffer)
admin.site.register(ReferralOffer)
