from django.contrib import admin
from django.utils.html import mark_safe
from .models.product import Product
from .models.category import Category
from .models.customer import Customer
from .models.order import Order
from .models.rate import Rate
from .models.brand import Brand
from core.models.coupon import Coupon
from core.models import *

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

# Register your models here.
admin.site.register(Product, AdminProduct)
admin.site.register(Customer, AdminCustomer)
admin.site.register(Category, AdminCategory)
admin.site.register(Order, AdminOrder)
admin.site.register(Rate, AdminRate)
admin.site.register(Brand, AdminBrand)
admin.site.register(Coupon, CouponAdmin)

