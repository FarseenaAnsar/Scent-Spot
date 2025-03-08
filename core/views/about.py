from django.views import View
from django.shortcuts import render

class AboutView(View):
    template_name = 'about.html'

    def get(self, request):
        context = {
            'company_info': {
                'name': 'ScentSpot',
                'established': '2023',
                'mission': 'To provide authentic and luxurious fragrances that help people express their unique personality and style.',
                'vision': 'To become the most trusted destination for premium fragrances worldwide.',
            },
            'features': [
                {
                    'title': 'Authentic Products',
                    'description': '100% genuine fragrances sourced directly from authorized distributors.',
                    'icon': 'fas fa-check-circle'
                },
                {
                    'title': 'Wide Selection',
                    'description': 'Carefully curated collection of premium fragrances from top brands.',
                    'icon': 'fas fa-spray-can'
                },
                {
                    'title': 'Expert Guidance',
                    'description': 'Professional advice to help you find your perfect scent.',
                    'icon': 'fas fa-user-tie'
                },
                {
                    'title': 'Fast Delivery',
                    'description': 'Secure packaging and quick delivery to your doorstep.',
                    'icon': 'fas fa-shipping-fast'
                }
            ],
            'team_members': [
                {
                    'name': 'John Doe',
                    'position': 'Founder & CEO',
                    'image': 'static/images/jhondoe.jpg',
                    'description': 'Fragrance industry expert with 15 years of experience.'
                },
                {
                    'name': 'Jane Smith',
                    'position': 'Head of Curation',
                    'image': 'static/images/jamessmith.jpeg',
                    'description': 'Certified perfumer with a passion for unique scents.'
                },
                # Add more team members as needed
            ]
        }
        return render(request, self.template_name, context)
