
from django.urls import path
from adminoperations import views


urlpatterns = [

    path('admin_login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('admin_logout/', views.AdminLogoutView.as_view(), name='admin_logout'),

    path('adminhome/',views.AdminHomeView.as_view(), name='admin_home'),
    path('adminhome/userlist/', views.UserListView.as_view(), name='user_list'),
    path('adminhome/userlist/userdetails/<int:user_id>/', views.UserDetailView.as_view(), name='user_detail'),

    path('adminhome/categorylist/', views.CategoryListView.as_view(), name='category_list'),
    path('adminhome/categorylist/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('adminhome/categorylist/delete/<int:pk>/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('adminhome/categorylist/editcategory/<int:category_id>/', views.CategoryUpdateView.as_view(), name='edit_category'),

    path('adminhome/productlist/', views.ProductListView.as_view(), name='product_list'),
    path('adminhome/productlist/add/', views.ProductCreateView.as_view(), name='add_product'),
    path('adminhome/productlist/edit/<int:pk>/',views.ProductUpdateView.as_view(), name='edit_product'),
    path('adminhome/productlist/delete/<int:pk>/', views.ProductDeleteView.as_view(), name='delete_product'),

    path('adminhome/orders/', views.AdminOrderListView.as_view(), name='admin_order_list'),
    path('adminhome/orders/<int:order_id>/', views.AdminOrderDetailView.as_view(), name='admin_order_details'),
    path('adminhome/orders/cancel/<int:order_id>/', views.AdminOrderCancelView.as_view(), name='admin_order_cancel'),
    path('adminhome/orders/returned/<int:order_id>/', views.OrderReturnView.as_view(), name='change_to_returned'),
    path('adminhome/orders/update-status/<int:order_id>/', views.UpdateOrderStatusView.as_view(), name='update_order_status'),

    path('adminhome/brands/', views.BrandListView.as_view(), name='brand_list'),
    path('adminhome/brands/add/', views.BrandCreateView.as_view(), name='brand_add'),
    path('adminhome/brands/edit/<int:pk>/', views.BrandUpdateView.as_view(), name='brand_edit'),
    path('adminhome/brands/delete/<int:pk>/', views.BrandDeleteView.as_view(), name='brand_delete'),
    
    # Product Offer URLs
    path('adminhome/offers/product/', views.ProductOfferListView.as_view(), name='product_offer_list'),
    path('adminhome/offers/product/add/', views.ProductOfferCreateView.as_view(), name='product_offer_create'),
    path('adminhome/offers/product/edit/<int:pk>/', views.ProductOfferUpdateView.as_view(), name='product_offer_update'),
    path('adminhome/offers/product/delete/<int:pk>/', views.ProductOfferDeleteView.as_view(), name='product_offer_delete'),
    
    # Category Offer URLs
    path('adminhome/offers/category/', views.CategoryOfferListView.as_view(), name='category_offer_list'),
    path('adminhome/offers/category/add/', views.CategoryOfferCreateView.as_view(), name='category_offer_create'),
    path('adminhome/offers/category/edit/<int:pk>/', views.CategoryOfferUpdateView.as_view(), name='category_offer_update'),
    path('adminhome/offers/category/delete/<int:pk>/', views.CategoryOfferDeleteView.as_view(), name='category_offer_delete'),
    
    # Referral Offer URLs
    path('adminhome/offers/referral/', views.ReferralOfferListView.as_view(), name='referral_offer_list'),
    path('adminhome/offers/referral/add/', views.ReferralOfferCreateView.as_view(), name='referral_offer_create'),
    path('adminhome/offers/referral/edit/<int:pk>/', views.ReferralOfferUpdateView.as_view(), name='referral_offer_update'),
    path('adminhome/offers/referral/delete/<int:pk>/', views.ReferralOfferDeleteView.as_view(), name='referral_offer_delete'),
    
    path('coupons/', views.CouponListView.as_view(), name='coupon_list'),
    path('coupons/create/', views.CreateCouponView.as_view(), name='create_coupon'),
    path('coupons/<int:pk>/edit/', views.EditCouponView.as_view(), name='edit_coupon'),
    path('coupons/<int:pk>/delete/', views.DeleteCouponView.as_view(), name='delete_coupon'),

    path('sales-report/', views.SalesReportView.as_view(), name='sales_report'),
    
    # Wallet Management 
    path('adminhome/wallet/', views.AdminWalletListView.as_view(), name='admin_wallet_list'),
    path('adminhome/wallet/<int:transaction_id>/', views.AdminWalletDetailView.as_view(), name='admin_wallet_detail'),
] 
