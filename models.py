"""
SmartAvtoServis - Models
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import random, string


# ─── Uzbekistan Regions ───────────────────────────────────────────────────────

VILOYATLAR = [
    ('toshkent_sh', 'Toshkent shahri'),
    ('toshkent', 'Toshkent viloyati'),
    ('andijon', 'Andijon'),
    ('fargona', 'Farg\'ona'),
    ('namangan', 'Namangan'),
    ('samarqand', 'Samarqand'),
    ('buxoro', 'Buxoro'),
    ('qashqadaryo', 'Qashqadaryo'),
    ('surxondaryo', 'Surxondaryo'),
    ('jizzax', 'Jizzax'),
    ('sirdaryo', 'Sirdaryo'),
    ('xorazm', 'Xorazm'),
    ('navoiy', 'Navoiy'),
    ('qoraqalpogiston', 'Qoraqalpog\'iston'),
]

MUTAXASSISLIKLAR = [
    ('general', 'Umumiy ta\'mirlash'),
    ('engine', 'Dvigatel'),
    ('body', 'Kuzov'),
    ('electrical', 'Elektr tizimi'),
    ('tires', 'Shinalar va g\'ildiraklar'),
    ('ac', 'Konditsioner'),
    ('transmission', 'Transmissiya'),
    ('brake', 'Tormoz tizimi'),
    ('suspension', 'Osma tizimi'),
    ('painting', 'Bo\'yash'),
    ('washing', 'Avto yuvish'),
    ('diagnostics', 'Diagnostika'),
    ('oil_change', 'Moy almashtirish'),
    ('glass', 'Shisha'),
    ('exhaust', 'Egzoz tizimi'),
]

ROLE_CHOICES = [
    ('user', 'Foydalanuvchi'),
    ('service', 'Servis egasi'),
    ('admin', 'Admin'),
]


# ─── Custom User Manager ──────────────────────────────────────────────────────

class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError('Email yoki telefon raqam kerak')
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email=email, password=password, **extra_fields)


# ─── User Model ───────────────────────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    preferred_language = models.CharField(max_length=5, default='uz',
                                           choices=[('uz','UZ'),('ru','RU'),('en','EN')])
    theme = models.CharField(max_length=10, default='light',
                              choices=[('light','Light'),('dark','Dark')])
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = _('Foydalanuvchi')
        verbose_name_plural = _('Foydalanuvchilar')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


# ─── SMS Verification ─────────────────────────────────────────────────────────

class SMSVerification(models.Model):
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'sms_verifications'

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"{self.phone} - {self.code}"


# ─── Service Model ────────────────────────────────────────────────────────────

class Service(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE,
                                  related_name='service_profile')
    name = models.CharField(max_length=200)
    specializations = models.JSONField(default=list)  # list of MUTAXASSISLIKLAR keys
    description = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    # Location
    viloyat = models.CharField(max_length=50, choices=VILOYATLAR)
    tuman = models.CharField(max_length=100)
    shahar = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Working hours
    work_start = models.TimeField(default='08:00')
    work_end = models.TimeField(default='18:00')
    work_days = models.JSONField(default=list)  # ['Mon','Tue',...]
    is_24h = models.BooleanField(default=False)

    # Pricing
    price_from = models.PositiveIntegerField(default=0)
    price_to = models.PositiveIntegerField(default=0)
    price_description = models.TextField(blank=True)

    # Status
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    telegram = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        verbose_name = _('Servis')
        verbose_name_plural = _('Servislar')

    def __str__(self):
        return self.name

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return self.reviews.count()

    def get_specialization_labels(self):
        spec_dict = dict(MUTAXASSISLIKLAR)
        return [spec_dict.get(s, s) for s in self.specializations]


# ─── Service Images ───────────────────────────────────────────────────────────

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE,
                                 related_name='images')
    image = models.ImageField(upload_to='services/')
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'service_images'
        ordering = ['order']

    def __str__(self):
        return f"{self.service.name} - rasm {self.order}"


# ─── Review & Rating ──────────────────────────────────────────────────────────

class Review(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE,
                                 related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ('service', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.service.name}: {self.rating}⭐"


# ─── Favorites ────────────────────────────────────────────────────────────────

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='favorites')
    service = models.ForeignKey(Service, on_delete=models.CASCADE,
                                 related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites'
        unique_together = ('user', 'service')
