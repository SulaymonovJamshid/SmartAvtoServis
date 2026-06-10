"""
SmartAvtoServis - URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
import smartavto.views as views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),

    # Language switch
    path('lang/<str:lang>/', views.set_language_view, name='set_language'),

    # Auth
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('verify-phone/', views.verify_phone_view, name='verify_phone'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Services
    path('services/', views.service_list, name='service_list'),
    path('services/<int:pk>/', views.service_detail, name='service_detail'),

    # Service Dashboard
    path('dashboard/', views.service_dashboard, name='service_dashboard'),
    path('dashboard/edit/', views.service_edit, name='service_edit'),
    path('dashboard/image/<int:img_id>/delete/', views.delete_service_image, name='delete_service_image'),

    # User Profile
    path('profile/', views.user_profile, name='user_profile'),

    # Favorites
    path('favorites/<int:service_id>/toggle/', views.toggle_favorite, name='toggle_favorite'),

    # API
    path('api/nearby/', views.api_nearby, name='api_nearby'),
    path('api/tumans/', views.api_tumans, name='api_tumans'),

    # Theme
    path('theme/toggle/', views.toggle_theme, name='toggle_theme'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
