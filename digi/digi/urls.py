from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings
from django.http import JsonResponse
from .schema import SCHEMA

# Custom view to fall back to our manual schema if auto-generation fails
class SafeSchemaView(SpectacularAPIView):
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            return JsonResponse(SCHEMA)

urlpatterns = [
    path('admin/', admin.site.urls),  # Django Admin panel
    path('api/', include('api.urls')),  # Include app-level API routes
    
    # OpenAPI 3 documentation with fallback
    path('api/schema/', SafeSchemaView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health checks
    path('health/', include('health_check.urls')),
]

# Only enable admin and docs in debug mode
if not settings.DEBUG:
    urlpatterns = [path for path in urlpatterns if not any(x in str(path.pattern) for x in ['admin/', 'docs/', 'redoc/'])]



