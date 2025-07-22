from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, request
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
import psutil
import django
import sys
import platform
from django.db import connection
from django.conf import settings
import os
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes




class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register new user",
        description="Create a new user account with email and phone verification. Returns authentication tokens on successful registration.",
        tags=["Authentication"],
        request=UserSerializer,
        responses={
            201: OpenApiResponse(
                description="User successfully registered",
                examples=[
                    OpenApiExample(
                        name="Registration Success",
                        value={
                            "id": 123,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "phone_number": "09123456789",
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request, *args, **kwargs):
        # Print request data for debugging
        print(f"Registration attempt with data: {request.data}")
        
        # Check for existing users with similar data (extra validation)
        username = request.data.get('username')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        
        # Debug existing users
        print(f"Current users in DB: {members.objects.count()}")
        if username:
            print(f"Users with username '{username}': {members.objects.filter(username=username).count()}")
        if email:
            print(f"Users with email '{email}': {members.objects.filter(email=email).count()}")
        if phone_number:
            print(f"Users with phone '{phone_number}': {members.objects.filter(phone_number=phone_number).count()}")
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Add JWT token generation here
            refresh = RefreshToken.for_user(user)
            response_data = serializer.data
            response_data['refresh'] = str(refresh)
            response_data['access'] = str(refresh.access_token)
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        # Enhanced error response
        print(f"Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User login",
        description="Authenticate with username/email and password to obtain JWT tokens for API access. The access token is valid for 60 minutes, while the refresh token is valid for 1 day.",
        tags=["Authentication"],
        request=TokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                examples=[
                    OpenApiExample(
                        name="Login Success",
                        value={
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "access": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "username": "johndoe",
                            "email": "john@example.com"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Invalid credentials")
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            # Debug incoming request data
            print(f"Login request data: {request.data}")
            
            login_id = request.data.get('login_id')
            password = request.data.get('password')
            
            print(f"Attempting login with: login_id={login_id}")
            print(f"All users: {list(members.objects.values_list('id', 'username', 'email'))}")
            
            # Check if login_id exists
            if not login_id:
                return Response(
                    {"detail": "Login ID is required", "code": "login_id_required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Try to find the user directly
            user = None
            
            try:
                if '@' in login_id:
                    # Try email login
                    try:
                        user = members.objects.get(email__iexact=login_id)
                        print(f"Found user by email: {user.email}")
                    except members.DoesNotExist:
                        print(f"No user found with email: {login_id}")
                else:
                    # Try username login
                    try:
                        user = members.objects.get(username__iexact=login_id)
                        print(f"Found user by username: {user.username}")
                    except members.DoesNotExist:
                        print(f"No user found with username: {login_id}")
                    
                if not user:
                    return Response(
                        {"detail": "User not found", "code": "user_not_found"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Verify password
                if not user.check_password(password):
                    print(f"Password check failed for user {user.username}")
                    return Response(
                        {"detail": "Invalid password", "code": "invalid_password"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Check if user is active
                if not user.is_active:
                    return Response(
                        {"detail": "User account is inactive", "code": "user_inactive"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Generate tokens - use custom token generation approach
                print(f"Generating tokens for user: {user.username}")
                
                # Create the tokens manually
                from rest_framework_simplejwt.tokens import RefreshToken
                from rest_framework_simplejwt.settings import api_settings

                refresh = RefreshToken()
                
                # Set the user ID in the token payload
                refresh[api_settings.USER_ID_CLAIM] = user.id 
                
                # Add custom claims
                refresh['username'] = user.username
                refresh['email'] = user.email
                
                # Get the access token from the refresh token
                access_token = str(refresh.access_token)
                
                return Response({
                    'refresh': str(refresh),
                    'access': access_token,
                    'username': user.username,
                    'email': user.email
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                print(f"Error during user lookup: {str(e)}")
                return Response(
                    {"detail": f"Authentication error: {str(e)}", "code": "auth_error"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            print(f"Unexpected error in login view: {str(e)}")
            return Response(
                {"detail": f"An unexpected error occurred: {str(e)}", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# email and SMS verification:
class EmailVerificationView(APIView):
    @extend_schema(
        summary="Send verification email",
        description="Send a verification email to the user's registered email address.",
        tags=["Authentication"],
        request=EmailVerificationRequestSerializer,
        responses={
            201: OpenApiResponse(description="Verification email sent successfully"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        """
        Send verification email.
        """
        serializer = EmailVerificationRequestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Verification email sent."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Verify email token",
        description="Verify the token sent to the user's email.",
        tags=["Authentication"],
        request=EmailVerificationSerializer,
        responses={
            200: OpenApiResponse(description="Email verified successfully"),
            400: OpenApiResponse(description="Invalid token or expired")
        }
    )
    def put(self, request):
        """
        Verify email token.
        """
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SMSVerificationView(APIView):
    @extend_schema(
        summary="Send verification SMS",
        description="Send a verification code via SMS to the user's registered phone number.",
        tags=["Authentication"],
        request=SMSVerificationRequestSerializer,
        responses={
            201: OpenApiResponse(description="Verification SMS sent successfully"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        """
        Send verification SMS.
        """
        serializer = SMSVerificationRequestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Verification SMS sent."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Verify SMS code",
        description="Verify the code sent to the user's phone via SMS.",
        tags=["Authentication"],
        request=SMSVerificationSerializer,
        responses={
            200: OpenApiResponse(description="Phone number verified successfully"),
            400: OpenApiResponse(description="Invalid code or expired")
        }
    )
    def put(self, request):
        """
        Verify SMS code.
        """
        serializer = SMSVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Phone number verified successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# Address API View
class AddressView(APIView):
    @extend_schema(
        summary="List user addresses",
        description="Retrieve all addresses associated with the authenticated user.",
        tags=["User Profile"],
        responses={
            200: OpenApiResponse(description="List of user addresses")
        }
    )
    def get(self, request):
        addresses = Address.objects.all()
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create new address",
        description="Add a new address to the authenticated user's profile.",
        tags=["User Profile"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Address created successfully"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Address created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update address",
        description="Update an existing address in the user's profile.",
        tags=["User Profile"],
        request=None,  # Replace with actual serializer
        responses={
            200: OpenApiResponse(description="Address updated successfully"),
            404: OpenApiResponse(description="Address not found")
        }
    )
    def put(self, request, address_id):
        try:
            address = Address.objects.get(id=address_id)
            serializer = AddressSerializer(address, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Address updated successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Address.DoesNotExist:
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete address",
        description="Remove an address from the user's profile.",
        tags=["User Profile"],
        responses={
            204: OpenApiResponse(description="Address deleted"),
            404: OpenApiResponse(description="Address not found")
        }
    )
    def delete(self, request, address_id):
        try:
            address = Address.objects.get(id=address_id)
            address.delete()
            return Response({"message": "Address deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Address.DoesNotExist:
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)


# Category API View
class CategoryView(APIView):
    @extend_schema(
        summary="List all categories",
        description="Retrieve all product categories available in the store.",
        tags=["Categories"],
        responses={
            200: OpenApiResponse(description="List of product categories")
        }
    )
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create new category",
        description="Create a new product category. Admin access required.",
        tags=["Categories"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Category created successfully"),
            403: OpenApiResponse(description="Permission denied, admin access required")
        }
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Category created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update category",
        description="Update an existing product category. Admin access required.",
        tags=["Categories"],
        request=None,  # Replace with actual serializer
        responses={
            200: OpenApiResponse(description="Category updated successfully"),
            404: OpenApiResponse(description="Category not found")
        }
    )
    def put(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Category updated successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete category",
        description="Delete a product category. Admin access required.",
        tags=["Categories"],
        responses={
            204: OpenApiResponse(description="Category deleted"),
            404: OpenApiResponse(description="Category not found")
        }
    )
    def delete(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
            category.delete()
            return Response({"message": "Category deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)



# SubCategory View
class SubCategoryView(APIView):
    @extend_schema(
        summary="List all subcategories",
        description="Retrieve all product subcategories available in the store.",
        tags=["Categories"],
        responses={
            200: OpenApiResponse(description="List of subcategories")
        }
    )
    def get(self, request):
        subcategories = SubCategory.objects.all()
        serializer = SubCategorySerializer(subcategories, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create new subcategory",
        description="Create a new product subcategory. Admin access required.",
        tags=["Categories"],
        request=SubCategorySerializer,
        responses={
            201: OpenApiResponse(description="Subcategory created successfully"),
            400: OpenApiResponse(description="Invalid input data"),
            403: OpenApiResponse(description="Permission denied, admin access required")
        }
    )
    def post(self, request):
        serializer = SubCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "SubCategory created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update subcategory",
        description="Update an existing product subcategory. Admin access required.",
        tags=["Categories"],
        request=SubCategorySerializer,
        responses={
            200: OpenApiResponse(description="Subcategory updated successfully"),
            404: OpenApiResponse(description="Subcategory not found")
        }
    )
    def put(self, request, subcategory_id):
        try:
            subcategory = SubCategory.objects.get(id=subcategory_id)
            serializer = SubCategorySerializer(subcategory, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "SubCategory updated successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SubCategory.DoesNotExist:
            return Response({"error": "SubCategory not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete subcategory",
        description="Delete a product subcategory. Admin access required.",
        tags=["Categories"],
        responses={
            204: OpenApiResponse(description="Subcategory deleted"),
            404: OpenApiResponse(description="Subcategory not found")
        }
    )
    def delete(self, request, subcategory_id):
        try:
            subcategory = SubCategory.objects.get(id=subcategory_id)
            subcategory.delete()
            return Response({"message": "SubCategory deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except SubCategory.DoesNotExist:
            return Response({"error": "SubCategory not found."}, status=status.HTTP_404_NOT_FOUND)

# Product View
class ProductView(APIView):
    @extend_schema(
        summary="List all products",
        description="Retrieve a paginated list of all available products with optional filtering.",
        tags=["Products"],
        responses={
            200: OpenApiResponse(description="List of products")
        }
    )
    def get(self, request, product_id=None):
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            data = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "category": product.category.name if product.category else None,
                "sub_category": product.sub_category.name if product.sub_category else None,
                "tags": product.tags
            }
        else:
            products = Product.objects.all()
            data = [{
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "category": product.category.name if product.category else None,
                "sub_category": product.sub_category.name if product.sub_category else None,
                "tags": product.tags
            } for product in products]
        return JsonResponse(data, safe=False)

    @extend_schema(
        summary="Create new product",
        description="Add a new product to the catalog. Admin access required.",
        tags=["Products"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Product created successfully"),
            400: OpenApiResponse(description="Invalid input data"),
            403: OpenApiResponse(description="Permission denied, admin access required")
        }
    )
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Product created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update product",
        description="Update an existing product. Admin access required.",
        tags=["Products"],
        request=None,  # Replace with actual serializer
        responses={
            200: OpenApiResponse(description="Product updated successfully"),
            404: OpenApiResponse(description="Product not found")
        }
    )
    def put(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Product updated successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete product",
        description="Delete a product from the catalog. Admin access required.",
        tags=["Products"],
        responses={
            204: OpenApiResponse(description="Product deleted"),
            404: OpenApiResponse(description="Product not found")
        }
    )
    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            product.delete()
            return Response({"message": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)


# Product Images Descriptions View
class ProductImagesDescriptionsView(APIView):
    @extend_schema(
        summary="List product images and descriptions",
        description="Retrieve all product images and detailed descriptions.",
        tags=["Products"],
        responses={
            200: OpenApiResponse(description="List of product images and descriptions")
        }
    )
    def get(self, request):
        descriptions = Product_Images_Descriptions.objects.all()
        serializer = ProductImagesDescriptionsSerializer(descriptions, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create product image and description",
        description="Add a new image and detailed description for a product. Admin access required.",
        tags=["Products"],
        request=ProductImagesDescriptionsSerializer,
        responses={
            201: OpenApiResponse(description="Product image and description created successfully"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        serializer = ProductImagesDescriptionsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Description created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update product image and description",
        description="Update an existing product image and description. Admin access required.",
        tags=["Products"],
        request=ProductImagesDescriptionsSerializer,
        responses={
            200: OpenApiResponse(description="Product image and description updated successfully"),
            404: OpenApiResponse(description="Product image and description not found")
        }
    )
    def put(self, request, description_id):
        try:
            description = Product_Images_Descriptions.objects.get(id=description_id)
            serializer = ProductImagesDescriptionsSerializer(description, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Description updated successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product_Images_Descriptions.DoesNotExist:
            return Response({"error": "Description not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete product image and description",
        description="Remove a product image and its detailed description. Admin access required.",
        tags=["Products"],
        responses={
            204: OpenApiResponse(description="Product image and description deleted successfully"),
            404: OpenApiResponse(description="Product image and description not found")
        }
    )
    def delete(self, request, description_id):
        try:
            description = Product_Images_Descriptions.objects.get(id=description_id)
            description.delete()
            return Response({"message": "Description deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Product_Images_Descriptions.DoesNotExist:
            return Response({"error": "Description not found."}, status=status.HTTP_404_NOT_FOUND)

# Discount View
class DiscountView(APIView):
    @extend_schema(
        summary="List discounts",
        description="Retrieve all available product discounts.",
        tags=["Products"],
        responses={
            200: OpenApiResponse(description="List of discounts")
        }
    )
    def get(self, request):
        discounts = Discount.objects.all()
        serializer = DiscountSerializer(discounts, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create discount",
        description="Create a new product discount. Admin access required.",
        tags=["Products"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Discount created successfully"),
            403: OpenApiResponse(description="Permission denied, admin access required")
        }
    )
    def post(self, request):
        serializer = DiscountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update discount",
        description="Update an existing product discount. Admin access required.",
        tags=["Products"],
        request=None,  # Replace with actual serializer
        responses={
            200: OpenApiResponse(description="Discount updated successfully"),
            404: OpenApiResponse(description="Discount not found")
        }
    )
    def put(self, request, discount_id):
        try:
            discount = Discount.objects.get(id=discount_id)
            serializer = DiscountSerializer(discount, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Discount.DoesNotExist:
            return Response({"error": "Discount not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete discount",
        description="Delete a product discount. Admin access required.",
        tags=["Products"],
        responses={
            204: OpenApiResponse(description="Discount deleted"),
            404: OpenApiResponse(description="Discount not found")
        }
    )
    def delete(self, request, discount_id):
        try:
            discount = Discount.objects.get(id=discount_id)
            discount.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Discount.DoesNotExist:
            return Response({"error": "Discount not found."}, status=status.HTTP_404_NOT_FOUND)

# Wishlist View
class WishlistView(APIView):
    @extend_schema(
        summary="List wishlist items",
        description="Retrieve all items in the authenticated user's wishlist.",
        tags=["User Profile"],
        responses={
            200: OpenApiResponse(description="List of wishlist items")
        }
    )
    def get(self, request):
        """
        Retrieve a list of all wishlist items.
        """
        wishlists = Wishlist.objects.all()
        serializer = WishlistSerializer(wishlists, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Add to wishlist",
        description="Add a product to the authenticated user's wishlist.",
        tags=["User Profile"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Item added to wishlist"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        """
        Add a new item to the wishlist.
        """
        serializer = WishlistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Remove from wishlist",
        description="Remove a product from the authenticated user's wishlist.",
        tags=["User Profile"],
        responses={
            204: OpenApiResponse(description="Item removed from wishlist"),
            404: OpenApiResponse(description="Wishlist item not found")
        }
    )
    def delete(self, request, wishlist_id):
        """
        Delete a wishlist item by ID.
        """
        try:
            wishlist = Wishlist.objects.get(id=wishlist_id)
            wishlist.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response({"error": "Wishlist item not found."}, status=status.HTTP_404_NOT_FOUND)

# Payment View
class PaymentView(APIView):
    @extend_schema(
        summary="List payment records",
        description="Retrieve payment information for all orders. Admin access required.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="List of payment records")
        }
    )
    def get(self, request):
        """
        Retrieve all payment records.
        """
        payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Process payment",
        description="Process a payment for an order.",
        tags=["Orders"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Payment processed successfully"),
            400: OpenApiResponse(description="Invalid payment information")
        }
    )
    def post(self, request):
        """
        Create a new payment record.
        """
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update payment",
        description="Update an existing payment record. Admin access required.",
        tags=["Orders"],
        request=None,
        responses={
            200: OpenApiResponse(description="Payment updated successfully"),
            404: OpenApiResponse(description="Payment not found")
        }
    )
    def put(self, request, payment_id):
        """
        Update a payment record by ID.
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.payment_type = request.data.get('payment_type', payment.payment_type)
            payment.save()
            return Response({"message": "Payment updated successfully."})
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete payment",
        description="Delete a payment record. Admin access required.",
        tags=["Orders"],
        responses={
            204: OpenApiResponse(description="Payment deleted successfully"),
            404: OpenApiResponse(description="Payment not found")
        }
    )
    def delete(self, request, payment_id):
        """
        Delete a payment record by ID.
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

# Order View
class OrderView(APIView):
    @extend_schema(
        summary="List user orders",
        description="Retrieve all orders placed by the authenticated user.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="List of user orders")
        }
    )
    def get(self, request, order_id=None):
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        else:
            orders = Order.objects.all()
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)

    @extend_schema(
        summary="Create new order",
        description="Place a new order with items from the user's cart.",
        tags=["Orders"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Order created successfully"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Order created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update order",
        description="Update an existing order. Admin or order owner access required.",
        tags=["Orders"],
        request=None,  # Replace with actual serializer
        responses={
            200: OpenApiResponse(description="Order updated successfully"),
            404: OpenApiResponse(description="Order not found")
        }
    )
    def put(self, request, order_id):
        try:
            order = get_object_or_404(Order, id=order_id)
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Order updated successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Delete order",
        description="Cancel/delete an order. Admin or order owner access required.",
        tags=["Orders"],
        responses={
            204: OpenApiResponse(description="Order deleted"),
            404: OpenApiResponse(description="Order not found")
        }
    )
    def delete(self, request, order_id):
        try:
            order = get_object_or_404(Order, id=order_id)
            order.delete()
            return Response({"message": "Order deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

# Shipping View
class ShippingView(APIView):
    @extend_schema(
        summary="List shipping information",
        description="Retrieve shipping information for all orders.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="List of shipping records")
        }
    )
    def get(self, request):
        shippings = Shipping.objects.all()
        data = [{
            "order": shipping.order.id,
            "address": shipping.address,
            "cost": shipping.cost
        } for shipping in shippings]
        return JsonResponse(data, safe=False)

    @extend_schema(
        summary="Create shipping record",
        description="Create shipping information for an order. Admin access required.",
        tags=["Orders"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Shipping information created"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        data = json.loads(request.body)
        order = get_object_or_404(Order, id=data['order_id'])
        shipping = Shipping.objects.create(
            order=order,
            address=data['address'],
            cost=data['cost']
        )
        return JsonResponse({"id": shipping.id, "message": "Shipping created successfully"}, status=201)

    @extend_schema(
        summary="Update shipping information",
        description="Update shipping details for an order. Admin access required.",
        tags=["Orders"],
        request=None,  # Replace with actual serializer
        responses={
            200: OpenApiResponse(description="Shipping information updated"),
            404: OpenApiResponse(description="Shipping record not found")
        }
    )
    def put(self, request, shipping_id):
        data = json.loads(request.body)
        shipping = get_object_or_404(Shipping, id=shipping_id)
        shipping.address = data.get('address', shipping.address)
        shipping.cost = data.get('cost', shipping.cost)
        shipping.save()
        return JsonResponse({"message": "Shipping updated successfully"})

    @extend_schema(
        summary="Delete shipping record",
        description="Delete shipping information. Admin access required.",
        tags=["Orders"],
        responses={
            204: OpenApiResponse(description="Shipping record deleted"),
            404: OpenApiResponse(description="Shipping record not found")
        }
    )
    def delete(self, request, shipping_id):
        shipping = get_object_or_404(Shipping, id=shipping_id)
        shipping.delete()
        return JsonResponse({"message": "Shipping deleted successfully"}, status=204)

# Review View
class ReviewView(APIView):
    @extend_schema(
        summary="List all reviews",
        description="Retrieve all product reviews with ratings and comments.",
        tags=["Products"],
        responses={
            200: OpenApiResponse(description="List of product reviews")
        }
    )
    def get(self, request):
        """
        Retrieve all product reviews.
        """
        reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create product review",
        description="Add a new review for a product with rating and comments.",
        tags=["Products"],
        request=ReviewSerializer,
        responses={
            201: OpenApiResponse(description="Review created successfully"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        """
        Create a new product review.
        """
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update product review",
        description="Update an existing product review.",
        tags=["Products"],
        request=ReviewSerializer,
        responses={
            200: OpenApiResponse(description="Review updated successfully"),
            404: OpenApiResponse(description="Review not found")
        }
    )
    def put(self, request, review_id):
        """
        Update a product review by ID.
        """
        review = Review.objects.filter(id=review_id).first()
        if not review:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Review updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete product review",
        description="Delete a product review.",
        tags=["Products"],
        responses={
            204: OpenApiResponse(description="Review deleted successfully"),
            404: OpenApiResponse(description="Review not found")
        }
    )
    def delete(self, request, review_id):
        """
        Delete a product review by ID.
        """
        review = Review.objects.filter(id=review_id).first()
        if not review:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        review.delete()
        return Response({"message": "Review deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

# AuditLog View
class AuditLogView(APIView):
    @extend_schema(
        summary="List audit logs",
        description="Retrieve audit logs for system activities. Admin access required.",
        tags=["System"],
        responses={
            200: OpenApiResponse(description="List of audit logs")
        }
    )
    def get(self, request):
        """
        Retrieve all audit logs.
        """
        logs = AuditLog.objects.all()
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create audit log",
        description="Create a new audit log entry. System use only.",
        tags=["System"],
        request=None,  # Replace with actual serializer
        responses={
            201: OpenApiResponse(description="Audit log created successfully")
        }
    )
    def post(self, request):
        """
        Create a new audit log.
        """
        serializer = AuditLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update audit log",
        description="Update an existing audit log entry. Admin access required.",
        tags=["System"],
        request=None,  # Replace with actual serializer
        responses={
            200: OpenApiResponse(description="Audit log updated"),
            404: OpenApiResponse(description="Audit log not found")
        }
    )
    def put(self, request, log_id):
        """
        Update an audit log by ID.
        """
        log = AuditLog.objects.filter(id=log_id).first()
        if not log:
            return Response({"error": "Audit log not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AuditLogSerializer(log, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Audit log updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete audit log",
        description="Delete an audit log entry. Admin access required.",
        tags=["System"],
        responses={
            204: OpenApiResponse(description="Audit log deleted"),
            404: OpenApiResponse(description="Audit log not found")
        }
    )
    def delete(self, request, log_id):
        """
        Delete an audit log by ID.
        """
        log = AuditLog.objects.filter(id=log_id).first()
        if not log:
            return Response({"error": "Audit log not found."}, status=status.HTTP_404_NOT_FOUND)

        log.delete()
        return Response({"message": "Audit log deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="System Health Check",
        description="Get detailed system health information including Python, Django, database, and system resources. Used for monitoring and diagnostics.",
        tags=["System"],
        responses={
            200: OpenApiResponse(
                description="Complete system health information",
                examples=[
                    OpenApiExample(
                        name="Healthy System",
                        value={
                            "status": "healthy",
                            "system": {
                                "os": "Windows",
                                "os_version": "10.0.22000",
                                "python_version": "3.10.0",
                                "django_version": "4.2.5",
                            },
                            "cpu": {
                                "cpu_count": 8,
                                "cpu_percent": 15.2,
                            },
                            "memory": {
                                "total": 16000000000,
                                "available": 8000000000,
                                "percent": 50.0,
                                "used": 8000000000,
                            },
                        }
                    )
                ]
            )
        },
    )
    def get(self, request):
        # System Info
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version,
            "django_version": django.get_version(),
        }

        # CPU Info
        cpu_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
        }

        # Memory Info
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
        }

        # Disk Info
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }

        # Database Check
        db_status = "healthy"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Storage Check
        storage_status = "healthy"
        try:
            test_file_path = os.path.join(settings.MEDIA_ROOT, 'test.txt')
            with open(test_file_path, 'w') as f:
                f.write('test')
            os.remove(test_file_path)
        except Exception as e:
            storage_status = f"unhealthy: {str(e)}"

        response_data = {
            "status": "healthy",
            "system": system_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "database": {
                "status": db_status,
                "engine": settings.DATABASES['default']['ENGINE'],
            },
            "storage": {
                "status": storage_status,
            }
        }

        return Response(response_data)

class DebugUsersView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Debug database users",
        description="Get information about existing users in the database (development only).",
        tags=["System"],
        responses={
            200: OpenApiResponse(description="User information")
        }
    )
    def get(self, request):
        """
        Debug endpoint to check users in the database.
        """
        try:
            users = members.objects.all()
            user_data = [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone_number': user.phone_number,
                'is_active': user.is_active,
                'created_at': user.created_at
            } for user in users]
            
            return Response({
                'count': len(user_data),
                'users': user_data
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'detail': 'An error occurred when retrieving users'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=["Authentication"],
    summary="Logout",
    description="Logout the current user by blacklisting the refresh token",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "refresh": {"type": "string"}
            },
            "required": ["refresh"]
        }
    },
    responses={
        status.HTTP_200_OK: {
            "type": "object",
            "properties": {
                "detail": {"type": "string"}
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "type": "object",
            "properties": {
                "detail": {"type": "string"}
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout the user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
