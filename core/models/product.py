from django.db import models
from .category import Category
from .brand import Brand
from django.core.validators import MinValueValidator, MaxValueValidator

class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.IntegerField(default=0)
    description = models.CharField(max_length=2000, blank=True)
    image = models.ImageField(upload_to="images/")
    category = models.ForeignKey(Category, db_column='type2', on_delete=models.CASCADE)
    rating = models.IntegerField(default=1, validators=[MinValueValidator(0),MaxValueValidator(5)])
    brand = models.CharField(max_length=50, default="")
    gender = models.CharField(max_length=50, default="")
    size = models.CharField(max_length=50, default="")
    stock = models.IntegerField(default=0)

    @staticmethod
    def get_product_by_id(id):
        return Product.objects.filter(id__in = id)
    
    @staticmethod
    def get_product(id):
        return Product.objects.filter(id = id)

    @staticmethod
    def get_all_products():
        return Product.objects.all()

    @staticmethod
    def get_spf_products(category_id):
        if (category_id):
            return Product.objects.filter(category = category_id)
        else:
            return Product.objects.all()
    
    @staticmethod
    def get_brands():
        return Product.objects.values("brand").distinct()

    @staticmethod
    def gen_filter(g, prds):
        if (g == "Male"):
            return prds.filter(gender = g)
        elif (g == "Female"):
            g = "women"
            return prds.filter(gender = g)

    @staticmethod
    def sorting(s, prds):
        if (s == "Low To High"):
            return prds.order_by('price')
        elif (s == "High To Low"):
            return prds.order_by('-price')
        
    @staticmethod
    def typee(fil, prds):
        return prds.filter(category__in = fil)
    @staticmethod
    def brandfilter(brand, prds):
        return prds.filter(brand__in = brand)
    
    def get_similar_products(self):
        return Product.objects.filter(
            category=self.category
        ).exclude(id=self.id)[:4]  # Limit to 4 similar products
    
    @staticmethod
    def get_product(product_id):
        return Product.objects.filter(id=product_id)
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='additional_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/additional/")
    
    


class PerfumeAttributes(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    scent_family = models.CharField(max_length=50)  # e.g., Floral, Woody, Oriental
    notes_top = models.CharField(max_length=200)    # e.g., Citrus, Bergamot
    notes_middle = models.CharField(max_length=200)  # e.g., Rose, Jasmine
    notes_base = models.CharField(max_length=200)   # e.g., Vanilla, Musk
    occasion = models.CharField(max_length=100)     # e.g., Casual, Formal, Evening
    season = models.CharField(max_length=50)        # e.g., Summer, Winter
    longevity = models.CharField(max_length=50)     # e.g., Long-lasting, Moderate
    gender = models.CharField(max_length=50)        # e.g., Unisex, Feminine, Masculine
