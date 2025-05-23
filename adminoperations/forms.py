from django import forms
from core.models.category import Category
from core.models.product import Product
import os
from django.conf import settings

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        
class ProductForm(forms.ModelForm):
    category = forms.CharField(max_length=100)
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unisex')
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'image', 'category', 'brand', 'gender', 'size']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.cleaned_data.get('image'):
            image_file = self.cleaned_data['image']
            # to define the path where you want to save the image
            images_dir = os.path.join(settings.BASE_DIR, 'core', 'static', 'images')
    
            # Create directory if it doesn't exist
            os.makedirs(images_dir, exist_ok=True)
            
            # Save the image
            file_path = os.path.join(images_dir, image_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
            
            # Save the image path to the model
            instance.image = f'static/images/{image_file.name}'
        
        if commit:
            instance.save()
        return instance

    def clean_category(self):
        category_name = self.cleaned_data.get('category')
        try:
            category, created = Category.objects.get_or_create(name=category_name)
            return category
        except Exception as e:
            raise forms.ValidationError(f"Error processing category: {str(e)}")

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero")
        return price