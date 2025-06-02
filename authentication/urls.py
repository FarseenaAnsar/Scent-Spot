from django.urls import path, include
from . import views


urlpatterns = [
    
    path('user_login/',views.user_login,name='login'),
    path('user_signup/',views.user_signup,name='signup'),
    # path('userprofile/',views.profile_view,name='user_profile'),
    path('user_logout/',views.user_logout,name='user_logout'),
    path('verify_otp/',views.verify_otp,name='verify_otp'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('verify_otp_for_password_reset/', views.verify_otp_for_password_reset, name='verify_otp_for_password_reset'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('verify-login-otp/', views.verify_login_otp, name='verify_login_otp'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    
]