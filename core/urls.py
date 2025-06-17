from django.urls import path, re_path
from .views import index, cart, checkout, orders, forgotpass, otp, ordermanage, profile, main, products, contact, about, wishlist, account, coupons, razorpay, returns,payment_views
from .views.returns import ReturnOrderView
from .views.email_verification import VerifyEmailView, SendOTPView
from django.urls import include

urlpatterns = [
    path("index", index.Index.as_view()  , name="index"),
    path("", main.Main.as_view()  , name="main"),
    path("about", about.AboutView.as_view()  , name="about"),
    path("account",account.Account.as_view(), name="account"),
    path("cart", cart.Cart.as_view(), name="cart"),
    path('cart/add/<int:product_id>/', cart.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:product_id>/', cart.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/update/<int:product_id>/', cart.UpdateCartView.as_view(), name='update_cart'),
    path("check-out", checkout.CheckOut.as_view(), name="checkout"),
    path('Place-cod-order/', checkout.PlaceCODOrderView.as_view(), name='place_cod_order'),
    
    path("proceed-to-pay", razorpay.razorpaycheck.as_view(), name="razorpaycheck"),
    path('payment-success/<str:payment_id>/', razorpay.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment-failure/', payment_views.PaymentFailureView.as_view(), name='payment_failure'),
    path('verify-payment/', razorpay.VerifyPaymentView.as_view(), name='verify_payment'),
    
    path("contact",contact.ContactView.as_view(), name="contact"),
    path("orders", orders.OrderView.as_view(), name="orders"),
    path('cancel-order/<int:order_id>/', orders.CancelOrderView.as_view(), name='cancel_order'),
    path("forgotpass", forgotpass.Forgotpass.as_view(), name="forgotpass"),
    path("otp", otp.Otp.as_view(), name="otp"),
    path("ordermanage", ordermanage.Ordermanage.as_view(), name="ordermanage"),
    path("profile", profile.Profile.as_view(), name="profile"),
    path("products", products.Products.as_view(), name="products"),
    path('products/<int:product_id>/', products.Products.as_view(), name='product_detail'),
    path('find-perfume/', products.PerfumeFinder.as_view(), name='perfume_finder'),
    path("wishlist", wishlist.WishlistView.as_view(), name="wishlist"),
    path('add-to-wishlist/<int:product_id>/', wishlist.AddToWishlistView.as_view(), name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', wishlist.RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),
    path('apply-coupon/', coupons.ApplyCouponView.as_view(), name='apply_coupon'),
    path('remove-coupon/', coupons.RemoveCouponView.as_view(), name='remove_coupon'),
    path('return-order/', returns.ReturnOrderView.as_view(), name='return_order'),
    
    # Email verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
]