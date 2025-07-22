from drf_spectacular.plumbing import build_bearer_security_scheme_object
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = JWTAuthentication
    name = 'JWT'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Enter your JWT token in the format: Bearer <token>'
        }

def preprocessing_hook(endpoints, **kwargs):
    """Simple pass-through function."""
    return endpoints

def postprocessing_hook(result, generator, **kwargs):
    """Add security schemes to the schema."""
    # Add security schemes
    if "components" not in result:
        result["components"] = {}
    if "securitySchemes" not in result["components"]:
        result["components"]["securitySchemes"] = {}

    # Add Bearer authentication
    result["components"]["securitySchemes"]["Bearer"] = build_bearer_security_scheme_object()

    # Add global security requirement
    result["security"] = [{"Bearer": []}]

    return result

# Fallback manual schema with multiple tags and detailed descriptions
SCHEMA = {
    "openapi": "3.0.3",
    "info": {
        "title": "Digikala API",
        "version": "1.0.0",
        "description": "Professional e-commerce platform API documentation",
        "contact": {
            "name": "API Support",
            "email": "support@digikala.com",
            "url": "https://digikala.com/support"
        },
        "termsOfService": "https://digikala.com/terms/",
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "tags": [
        {
            "name": "Authentication",
            "description": "Authentication related endpoints for login, registration, and token management"
        },
        {
            "name": "User Profile",
            "description": "User profiles, addresses, and personal settings management"
        },
        {
            "name": "Users",
            "description": "User profile and account management"
        },
        {
            "name": "Products",
            "description": "Operations related to product listing, details, and management"
        },
        {
            "name": "Orders",
            "description": "Shopping cart, checkout, and order management"
        },
        {
            "name": "Categories",
            "description": "Product category related operations"
        },
        {
            "name": "System",
            "description": "System health, monitoring, and diagnostics"
        }
    ],
    "paths": {
        "/api/auth/register/": {
            "post": {
                "operationId": "register",
                "summary": "Register a new user account",
                "description": "Create a new user account and receive authentication tokens. Required fields include username, email, password, and phone_number.",
                "tags": ["Authentication"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "username": {
                                        "type": "string",
                                        "description": "Unique username for the account"
                                    },
                                    "email": {
                                        "type": "string",
                                        "format": "email",
                                        "description": "Valid email address, will need verification"
                                    },
                                    "password": {
                                        "type": "string",
                                        "format": "password",
                                        "description": "Strong password (min 8 characters)"
                                    },
                                    "phone_number": {
                                        "type": "string",
                                        "description": "Valid phone number, will need verification"
                                    },
                                    "first_name": {
                                        "type": "string",
                                        "description": "User's first name"
                                    },
                                    "last_name": {
                                        "type": "string",
                                        "description": "User's last name"
                                    }
                                },
                                "required": ["username", "email", "password", "phone_number"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User successfully registered",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "username": {"type": "string"},
                                        "email": {"type": "string"},
                                        "access": {"type": "string"},
                                        "refresh": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid input data"
                    }
                }
            }
        },
        "/api/auth/login/": {
            "post": {
                "operationId": "login",
                "summary": "Login and obtain tokens",
                "description": "Authenticate using username and password to receive JWT access and refresh tokens for API access.",
                "tags": ["Authentication"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "username": {
                                        "type": "string",
                                        "description": "Username for authentication"
                                    },
                                    "password": {
                                        "type": "string",
                                        "format": "password",
                                        "description": "User password"
                                    }
                                },
                                "required": ["username", "password"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful login",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "access": {
                                            "type": "string",
                                            "description": "JWT access token, valid for 15 minutes"
                                        },
                                        "refresh": {
                                            "type": "string",
                                            "description": "JWT refresh token, valid for 1 day"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Invalid credentials"
                    }
                }
            }
        },
        "/api/auth/token/refresh/": {
            "post": {
                "operationId": "token_refresh",
                "summary": "Refresh access token",
                "description": "Use a valid refresh token to obtain a new access token when the original expires.",
                "tags": ["Authentication"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "refresh": {
                                        "type": "string",
                                        "description": "Valid refresh token"
                                    }
                                },
                                "required": ["refresh"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "New access token generated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "access": {
                                            "type": "string",
                                            "description": "New JWT access token"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Invalid or expired refresh token"
                    }
                }
            }
        },
        "/api/products/": {
            "get": {
                "operationId": "list_products",
                "summary": "List all products",
                "description": "Retrieve a paginated list of all available products with optional filtering.",
                "tags": ["Products"],
                "parameters": [
                    {
                        "name": "category",
                        "in": "query",
                        "description": "Filter by category ID",
                        "schema": {"type": "integer"}
                    },
                    {
                        "name": "search",
                        "in": "query",
                        "description": "Search term to filter products by name or description",
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "min_price",
                        "in": "query",
                        "description": "Minimum price filter",
                        "schema": {"type": "number"}
                    },
                    {
                        "name": "max_price",
                        "in": "query",
                        "description": "Maximum price filter",
                        "schema": {"type": "number"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of products",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "count": {"type": "integer"},
                                        "next": {"type": "string", "format": "uri", "nullable": True},
                                        "previous": {"type": "string", "format": "uri", "nullable": True},
                                        "results": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"},
                                                    "price": {"type": "number"},
                                                    "description": {"type": "string"},
                                                    "category": {"type": "integer"},
                                                    "image": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "operationId": "create_product",
                "summary": "Create a new product",
                "description": "Add a new product to the catalog. Admin access required.",
                "tags": ["Products"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "price": {"type": "number"},
                                    "category": {"type": "integer"},
                                    "sub_category": {"type": "integer"},
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["name", "price", "category", "sub_category"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Product created successfully"
                    },
                    "400": {
                        "description": "Invalid input data"
                    },
                    "403": {
                        "description": "Permission denied, admin access required"
                    }
                }
            }
        },
        "/api/categories/": {
            "get": {
                "operationId": "list_categories",
                "summary": "List all product categories",
                "description": "Retrieve all available product categories with their subcategories.",
                "tags": ["Categories"],
                "responses": {
                    "200": {
                        "description": "List of categories",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "slug": {"type": "string"},
                                            "description": {"type": "string"},
                                            "subcategories": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/orders/": {
            "get": {
                "operationId": "list_orders",
                "summary": "List user orders",
                "description": "Retrieve all orders placed by the authenticated user.",
                "tags": ["Orders"],
                "responses": {
                    "200": {
                        "description": "List of user orders",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "status": {"type": "string"},
                                            "total_amount": {"type": "number"},
                                            "created_at": {"type": "string", "format": "date-time"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "operationId": "create_order",
                "summary": "Create a new order",
                "description": "Place a new order with items from the user's cart.",
                "tags": ["Orders"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "items": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "product": {"type": "integer"},
                                                "quantity": {"type": "integer"}
                                            },
                                            "required": ["product", "quantity"]
                                        }
                                    }
                                },
                                "required": ["items"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Order created successfully"
                    },
                    "400": {
                        "description": "Invalid input data"
                    }
                }
            }
        },
        "/api/health/detailed/": {
            "get": {
                "operationId": "health_check",
                "summary": "System Health Check",
                "description": "Get detailed system health information including Python, Django, database, and system resources. Used for monitoring and diagnostics.",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "System health information",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "system": {"type": "object"},
                                        "cpu": {"type": "object"},
                                        "memory": {"type": "object"},
                                        "disk": {"type": "object"},
                                        "database": {"type": "object"},
                                        "storage": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "security": [{"Bearer": []}]
} 