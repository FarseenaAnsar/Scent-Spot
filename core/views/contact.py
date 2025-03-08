from django.shortcuts import render, redirect
from django.views import View

from django.shortcuts import render, redirect
from django.views import View
from django.core.mail import send_mail
from django.contrib import messages

class ContactView(View):
    template_name = 'contact.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message = request.POST.get('message', '')

        # Basic form validation
        if name and email and message:
            try:
                # Email configuration - use environment variables in production
                email_message = f"""
                New contact form submission:
                
                Name: {name}
                Email: {email}
                Subject: {subject}
                Message: {message}
                """

                send_mail(
                    subject=f'Contact Form: {subject}',
                    message=email_message,
                    from_email=email,
                    recipient_list=['your-email@example.com'],  # Replace with your email
                    fail_silently=False,
                )

                # Success message
                messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
                return redirect('contact')  # Redirect to same page after successful submission

            except Exception as e:
                messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
                return render(request, self.template_name, {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message,
                })
        else:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, self.template_name, {
                'name': name,
                'email': email,
                'subject': subject,
                'message': message,
            })
