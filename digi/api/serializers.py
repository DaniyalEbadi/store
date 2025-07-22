from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from .models import *
from .models import EmailVerification
from django.core.mail import send_mail
from .models import SMSVerification
from random import randint

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = members
        fields = [
            'username', 'password', 'email', 'phone_number',
            'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser'
        ]

    def validate(self, data):
        # Check username uniqueness with a clearer error message
        username = data.get('username')
        if members.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "This username is already taken. Please choose another one."})
        
        # Check phone number uniqueness with a clearer error message
        phone_number = data.get('phone_number')
        if phone_number and members.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({"phone_number": "This phone number is already registered. Please use another one."})
        
        # Check email uniqueness with a clearer error message
        email = data.get('email')
        if email and members.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email is already registered. Please use another one."})
            
        return data

    def create(self, validated_data):
        user = members.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            email=validated_data.get("email"),
            phone_number=validated_data.get("phone_number", ""),
            password=validated_data['password'],  # Pass password directly here
        )
        return user


class TokenObtainPairSerializer(serializers.Serializer):
    login_id = serializers.CharField(required=True, help_text="Enter your username or email")
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        # Get login identifier and password
        login_id = data.get('login_id')
        password = data.get('password')

        if not login_id:
            raise serializers.ValidationError({'login_id': ['Please provide username or email']})

        # Debug info
        print(f"Login attempt with: login_id={login_id}")
        print(f"All users in database: {list(members.objects.values_list('username', 'email'))}")

        # Try to find the user
        user = None

        # Check if login_id is an email (contains @)
        if '@' in login_id:
            try:
                user = members.objects.get(email__iexact=login_id)
                print(f"User found by email: {user.email}")
            except members.DoesNotExist:
                print(f"No user found with email: {login_id}")
        else:
            # Treat as username
            try:
                user = members.objects.get(username__iexact=login_id)
                print(f"User found by username: {user.username}")
            except members.DoesNotExist:
                print(f"No user found with username: {login_id}")
        
        if not user:
            print("User lookup failed completely")
            raise serializers.ValidationError({'non_field_errors': ['User not found with provided credentials']})

        # Print debug info about the found user
        print(f"Found user: id={user.id}, username={user.username}, email={user.email}")
        
        # Check the password using Django's built-in check_password method
        if not user.check_password(password):
            print(f"Password mismatch for user {user.username}!")
            print(f"Password sent: {password}")
            raise serializers.ValidationError({'non_field_errors': ['Invalid password']})

        # Ensure the user is active
        if not user.is_active:
            print("User is inactive!")
            raise serializers.ValidationError({'non_field_errors': ['User account is inactive']})

        # Debugging: If the user is successfully authenticated
        print(f"User authenticated successfully: {user.username}")

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        return {
            'refresh': str(refresh),
            'access': f"Bearer {access_token}",
            'username': user.username,
            'email': user.email
        }

#EmailVerificationRequestSerializer:

class EmailVerificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = self.context['request'].user
        if user.email != value:
            raise serializers.ValidationError("Email does not match the user's registered email.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        email_verification = EmailVerification.objects.create(
            user=user,
            email=validated_data['email']
        )
        send_mail(
            'Email Verification',
            f'Your verification code is: {email_verification.token}',
            'no-reply@example.com',
            [email_verification.email],
        )
        return email_verification


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            verification = EmailVerification.objects.get(token=value, is_verified=False)
            if verification.is_expired():
                raise serializers.ValidationError("Token has expired.")
            return verification
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")

    def save(self, **kwargs):
        verification = self.validated_data['token']
        verification.is_verified = True
        verification.save()
        return verification


#SMSVerificationRequestSerializer:

class SMSVerificationRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

    def validate_phone_number(self, value):
        user = self.context['request'].user
        if user.phone_number != value:
            raise serializers.ValidationError("Phone number does not match the user's registered phone number.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        code = f"{randint(100000, 999999)}"  # Generate 6-digit OTP
        sms_verification = SMSVerification.objects.create(
            user=user,
            phone_number=validated_data['phone_number'],
            code=code
        )
        # Simulate SMS send (replace with actual SMS API integration)
        print(f"Sending SMS to {sms_verification.phone_number}: Your code is {code}")
        return sms_verification


class SMSVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate_code(self, value):
        try:
            verification = SMSVerification.objects.get(code=value, is_verified=False)
            if verification.is_expired():
                raise serializers.ValidationError("Code has expired.")
            return verification
        except SMSVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid code.")

    def save(self, **kwargs):
        verification = self.validated_data['code']
        verification.is_verified = True
        verification.save()
        return verification




class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ProductImagesDescriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_Images_Descriptions
        fields = '__all__'

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = '__all__'

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'

class ProductViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductView
        fields = '__all__'
