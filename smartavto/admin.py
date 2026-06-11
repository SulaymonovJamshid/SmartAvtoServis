"""
SmartAvtoServis - Admin Configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, Service, ServiceImage, Review, Favorite, SMSVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['get_full_name', 'email', 'phone', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering = ['-created_at']
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        (_('Shaxsiy ma\'lumot'), {'fields': ('first_name', 'last_name', 'avatar')}),
        (_('Sozlamalar'), {'fields': ('role', 'is_verified', 'preferred_language', 'theme')}),
        (_('Ruxsatlar'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Vaqt'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 0
    fields = ['image', 'order']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'viloyat', 'tuman', 'is_approved', 'is_active', 'avg_rating_display', 'created_at']
    list_filter = ['is_approved', 'is_active', 'viloyat']
    search_fields = ['name', 'owner__first_name', 'owner__last_name', 'address']
    ordering = ['-created_at']
    inlines = [ServiceImageInline]
    actions = ['approve_services', 'disapprove_services']

    def avg_rating_display(self, obj):
        return f"{obj.avg_rating} ⭐ ({obj.review_count})"
    avg_rating_display.short_description = _('Reyting')

    def approve_services(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} servis tasdiqlandi.")
    approve_services.short_description = _('Tasdiqlash')

    def disapprove_services(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_services.short_description = _('Tasdiqni bekor qilish')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['user__first_name', 'service__name', 'comment']


@admin.register(SMSVerification)
class SMSVerificationAdmin(admin.ModelAdmin):
    list_display = ['phone', 'code', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used']


admin.site.site_header = "SmartAvtoServis Admin"
admin.site.site_title = "SmartAvtoServis"
admin.site.index_title = "Boshqaruv paneli"
