from django.db import models 
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class Customer(models.Model):
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=10, null=True)
    gender = models.CharField(max_length=10, default="", null=True)
    password = models.CharField(max_length=150, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null = True)

    def register(self):
        self.save()
    
    def customer_info(id):
        return Customer.objects.get(id = id)
        
    def checkk(user, flag):
        if (flag == "email"):
            try:
                return Customer.objects.get(email = user)
            except:
                return None
        elif (flag == "phone"):
            try:
                return Customer.objects.get(phone = user)
            except:
                return None
    def info(email):
       return Customer.objects.get(email=email) 
   
    def __str__(self):
       return self.first_name
   
    @receiver(post_save, sender=User)
    def create_customer_profile(sender, instance, created, **kwargs):
        if created:
            Customer.objects.get_or_create(
                email=instance.username,
                defaults={
                    'first_name': instance.first_name,
                    'last_name': instance.last_name
                }
            )