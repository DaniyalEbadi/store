from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import Group, Permission
import uuid
from django.utils.timezone import now
from datetime import timedelta

# Create your models here.
class members(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=11, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    last_login = None

    # Remove groups and user_permissions entirely
    groups = None
    user_permissions = None

    def __str__(self):
        return self.username


def email_verification_expiry():
    return now() + timedelta(minutes=15)

def sms_verification_expiry():
    return now() + timedelta(minutes=5)


class EmailVerification(models.Model):
    user = models.ForeignKey('members', on_delete=models.CASCADE, related_name="email_verifications")
    email = models.EmailField()  # Verification email
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=email_verification_expiry)

    def is_expired(self):
        return now() > self.expires_at

    def __str__(self):
        return f"EmailVerification for {self.email}"


class SMSVerification(models.Model):
    user = models.ForeignKey('members', on_delete=models.CASCADE, related_name="sms_verifications")
    phone_number = models.CharField(max_length=11)  # Verification phone number
    code = models.CharField(max_length=6)  # 6-digit OTP
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=sms_verification_expiry)

    def is_expired(self):
        return now() > self.expires_at

    def __str__(self):
        return f"SMSVerification for {self.phone_number}"





class Address(models.Model):
    user = models.ForeignKey(members, on_delete=models.CASCADE, related_name='addresses')
    Address = models.TextField(null=True, blank=True)
    City = models.CharField(max_length=20)
    Landmark = models.CharField(max_length=30)
    Postal_code = models.CharField(max_length=10, db_index=True)
    Phone_number = models.CharField(max_length=11, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.Address


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)




    def __str__(self):
        return self.name

class SubCategory(models.Model):
    Category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)



    def __str__(self):
        return self.name
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    #sku = models.textField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    price = models.FloatField(null=True, blank=True)
    img = models.CharField(max_length=255, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="sub_categories")
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)



    def __str__(self):
        return self.name

class Product_Images_Descriptions(models.Model):
    product= models.ForeignKey(Product, on_delete=models.CASCADE)
    product_Images_Description = models.TextField(null=True, blank=True)
    product_Description = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.product_Images_Description

class Discount(models.Model):
    user = models.ForeignKey(members, on_delete=models.CASCADE, related_name="discounts")  # Relationship to the user
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="discounts")  # Relationship to the product
    description = models.TextField(null=True, blank=True)
    discount_percentage = models.FloatField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)




    def __str__(self):
        return f"{self.product.name} - {self.discount_percentage}%"


class Wishlist(models.Model):
    user = models.ForeignKey(members, on_delete=models.CASCADE, related_name="wishlist")
    notes = models.TextField(null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(default=now)
    deleted_at = models.DateTimeField(null=True, blank=True)




class Payment(models.Model):
    user = models.ForeignKey(members, on_delete=models.CASCADE, related_name='payments')
    Payment_type = models.CharField(max_length=20)
    models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return self.Payment_type


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    user = models.ForeignKey(members, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_amount = models.FloatField(default=0.0)  # Total cost of the order
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return f"Order {self.order_id} - {self.status}"

    def calculate_total(self):
        """
        Calculates the total amount of the order based on its items.
        """
        self.total_amount = sum(
            item.total_price for item in self.items.all()
        )  # Related name for OrderItem is 'items'
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.FloatField()  # Price of a single unit of the product
    total_price = models.FloatField()  # quantity * price



    def __str__(self):
        return f"Item {self.product.name} in Order {self.order.order_id}"

    def save(self, *args, **kwargs):
        """
        Automatically calculate total price before saving.
        """
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)
        # Update the related order's total amount
        self.order.calculate_total()

class Shipping(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="shipping")
    address = models.TextField()  # Remove ForeignKey if you prefer storing raw address data
    cost = models.FloatField(default=0.0)  # Shipping cost
    tracking_number = models.CharField(max_length=50, null=True, blank=True)  # Optional tracking
    shipped_at = models.DateTimeField(null=True, blank=True)  # When the order is shipped
    delivered_at = models.DateTimeField(null=True, blank=True)  # When the order is delivered



    def __str__(self):
        return f"Shipping for Order {self.order.order_id} - {self.shipping_method}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(members, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        default=5
    )  # Rating out of 5
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"

class AuditLog(models.Model):
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=50)
    user = models.ForeignKey(members, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    model_name = models.CharField(max_length=50)
    record_id = models.BigIntegerField()
    details = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"{self.action} by {self.members} on {self.model_name} ({self.record_id})"

class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="views")
    members = models.ForeignKey(members, on_delete=models.CASCADE, null=True, blank=True, related_name="viewed_products")
    viewed_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.members} viewed {self.product.name}" if self.members else f"Anonymous viewed {self.product.name}"
