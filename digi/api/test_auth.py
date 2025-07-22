import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digi.digi.settings')
django.setup()

from django.contrib.auth import get_user_model
from .models import members

def test_user_exists():
    """Test if the user exists in the database"""
    print("=== Testing User Existence ===")
    
    # List all users
    all_users = members.objects.all()
    print(f"Total users in database: {all_users.count()}")
    
    for user in all_users:
        print(f"User ID: {user.id}, Username: {user.username}, Email: {user.email}, Is Active: {user.is_active}")
    
    # Look for specific test user
    username = "Danimeni"
    email = "danialebadi533@gmail.com"
    
    print(f"\nSearching for user with username '{username}'...")
    try:
        user_by_username = members.objects.get(username=username)
        print(f"Found user by username: {user_by_username.username}, {user_by_username.email}")
    except members.DoesNotExist:
        print(f"No user found with username '{username}'")
    except Exception as e:
        print(f"Error finding user by username: {str(e)}")
    
    print(f"\nSearching for user with username (case-insensitive) '{username}'...")
    try:
        user_by_username_iexact = members.objects.get(username__iexact=username)
        print(f"Found user by username (case-insensitive): {user_by_username_iexact.username}, {user_by_username_iexact.email}")
    except members.DoesNotExist:
        print(f"No user found with username (case-insensitive) '{username}'")
    except Exception as e:
        print(f"Error finding user by username (case-insensitive): {str(e)}")
    
    print(f"\nSearching for user with email '{email}'...")
    try:
        user_by_email = members.objects.get(email=email)
        print(f"Found user by email: {user_by_email.username}, {user_by_email.email}")
    except members.DoesNotExist:
        print(f"No user found with email '{email}'")
    except Exception as e:
        print(f"Error finding user by email: {str(e)}")

def test_password_check():
    """Test if the password hash is correct and can be verified"""
    print("\n=== Testing Password Check ===")
    
    # Try to find our test user
    username = "Danimeni"
    correct_password = "Danial2017!"
    
    try:
        user = members.objects.get(username__iexact=username)
        print(f"Found user: {user.username}, {user.email}")
        
        # Test password check
        password_valid = user.check_password(correct_password)
        print(f"Password check result: {password_valid}")
        
        # Print password hash (not the actual password) for debugging
        print(f"Password hash in database: {user.password}")
        
    except members.DoesNotExist:
        print(f"No user found with username '{username}'")
    except Exception as e:
        print(f"Error: {str(e)}")

def create_test_user():
    """Create a test user in the database"""
    print("\n=== Creating Test User ===")
    
    username = "Danimeni"
    email = "danialebadi533@gmail.com"
    password = "Danial2017!"
    
    # Check if user already exists
    if members.objects.filter(username=username).exists():
        print(f"User '{username}' already exists.")
        return
    
    # Create the user
    try:
        user = members.objects.create_user(
            username=username,
            email=email,
            phone_number="1234567890",  # Sample phone number
            password=password,
            first_name="Test",
            last_name="User",
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        print(f"User created: {user.username}, {user.email}")
    except Exception as e:
        print(f"Error creating user: {str(e)}")

if __name__ == "__main__":
    # Uncomment to create a test user
    # create_test_user()
    
    test_user_exists()
    test_password_check() 