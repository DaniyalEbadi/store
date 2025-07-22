from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from api.models import members

class Command(BaseCommand):
    help = 'Test authentication functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Testing Authentication ==='))
        
        # List all users
        all_users = members.objects.all()
        self.stdout.write(f"Total users in database: {all_users.count()}")
        
        for user in all_users:
            self.stdout.write(f"User ID: {user.id}, Username: {user.username}, Email: {user.email}, Is Active: {user.is_active}")
        
        # Try to find our test user
        username = "Danimeni"
        email = "danialebadi533@gmail.com"
        password = "Danial2017!"
        
        self.stdout.write("\nAttempting to create test user if it doesn't exist...")
        
        # Create test user if not exists
        if not members.objects.filter(username=username).exists():
            try:
                user = members.objects.create_user(
                    username=username,
                    email=email,
                    phone_number="1234567890",
                    password=password,
                    first_name="Test",
                    last_name="User",
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"Created test user: {user.username}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating user: {str(e)}"))
        else:
            self.stdout.write(f"Test user '{username}' already exists")
            
        # Test finding user by username
        self.stdout.write(f"\nSearching for user with username '{username}'...")
        try:
            user_by_username = members.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"Found user by username: {user_by_username.username}, {user_by_username.email}"))
            
            # Test password check
            password_valid = user_by_username.check_password(password)
            self.stdout.write(f"Password check result: {password_valid}")
            
            # Print password hash for debugging
            self.stdout.write(f"Password hash in database: {user_by_username.password}")
            
            # Manual password check using Django's check_password
            manual_check = check_password(password, user_by_username.password)
            self.stdout.write(f"Manual password check result: {manual_check}")
            
        except members.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No user found with username '{username}'"))
            
        # Test finding user by email
        self.stdout.write(f"\nSearching for user with email '{email}'...")
        try:
            user_by_email = members.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f"Found user by email: {user_by_email.username}, {user_by_email.email}"))
        except members.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No user found with email '{email}'"))
            
        # Test login with TokenObtainPairSerializer (manual test)
        self.stdout.write("\n=== Testing TokenObtainPairSerializer ===")
        from rest_framework.serializers import ValidationError
        from api.serializers import TokenObtainPairSerializer
        
        # Test with username
        try:
            serializer = TokenObtainPairSerializer(data={"login_id": username, "password": password})
            if serializer.is_valid():
                result = serializer.validated_data
                self.stdout.write(self.style.SUCCESS(f"Login successful with username. Access token: {result.get('access')[:20]}..."))
            else:
                self.stdout.write(self.style.ERROR(f"Login failed with username: {serializer.errors}"))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"Validation error with username: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error with username login: {str(e)}"))
            
        # Test with email
        try:
            serializer = TokenObtainPairSerializer(data={"login_id": email, "password": password})
            if serializer.is_valid():
                result = serializer.validated_data
                self.stdout.write(self.style.SUCCESS(f"Login successful with email. Access token: {result.get('access')[:20]}..."))
            else:
                self.stdout.write(self.style.ERROR(f"Login failed with email: {serializer.errors}"))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"Validation error with email: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error with email login: {str(e)}")) 