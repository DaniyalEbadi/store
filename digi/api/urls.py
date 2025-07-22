from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Auth endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('auth/login/', UserLoginView.as_view(), name='user_login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout_view, name='logout'),
    
    # Health check
    path('health/detailed/', HealthCheckView.as_view(), name='health_detailed'),
    
    # Debug endpoint (development only)
    path('debug/users/', DebugUsersView.as_view(), name='debug_users'),
    
    # Verification endpoints
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('verify-sms/', SMSVerificationView.as_view(), name='verify_sms'),

    # Product endpoints
    path('products/', ProductView.as_view(), name='product_list'),
    path('products/<int:product_id>/', ProductView.as_view(), name='product_detail'),

    # Order endpoints
    path('orders/', OrderView.as_view(), name='order_list'),
    path('orders/<int:order_id>/', OrderView.as_view(), name='order_detail'),

    # Address endpoint
    path('addresses/', AddressView.as_view(), name='address_list'),

    # Category endpoints
    path('categories/', CategoryView.as_view(), name='category_list'),

    # Subcategory endpoints
    path('subcategories/', SubCategoryView.as_view(), name='subcategory_list'),
    path('subcategories/<int:id>/', SubCategoryView.as_view(), name='subcategory_detail'),

    # Product Images & Descriptions
    path('product-images/', ProductImagesDescriptionsView.as_view(), name='product_image_description_list'),

    # Discount endpoint
    path('discounts/', DiscountView.as_view(), name='discount_list'),

    # Wishlist endpoint
    path('wishlists/', WishlistView.as_view(), name='wishlist_list'),

    # Payment endpoint
    path('payments/', PaymentView.as_view(), name='payment_list'),

    # Shipping endpoint
    path('shippings/', ShippingView.as_view(), name='shipping_list'),

    # Review endpoint
    path('reviews/', ReviewView.as_view(), name='review_list'),

    # Audit Log endpoint
    path('audit-logs/', AuditLogView.as_view(), name='audit_log_list'),
]
