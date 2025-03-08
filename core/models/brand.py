from django.db import models

class Brand(models.Model):
    brand_name = models.CharField(max_length=50, default="")
    image = models.ImageField(upload_to="images/")
    category = models.CharField(max_length=50, default="")

    @staticmethod
    def get_all_brands():
        return Brand.objects.all()