"""
SmartAvtoServis - Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import activate, gettext as _
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.conf import settings
from datetime import timedelta
import json, math

from .models import (User, SMSVerification, Service, ServiceImage,
                     Review, Favorite, VILOYATLAR, MUTAXASSISLIKLAR)
from .forms import (UserRegisterForm, ServiceRegisterForm, LoginForm,
                    ServiceProfileForm, ReviewForm, UserProfileForm)
from .utils import send_sms_code, haversine_distance


# ─── Home ─────────────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('service_list')
    return render(request, 'home.html')


# ─── Language Switch ──────────────────────────────────────────────────────────

def set_language_view(request, lang):
    if lang in ['uz', 'ru', 'en']:
        activate(lang)
        request.session['django_language'] = lang
        if request.user.is_authenticated:
            request.user.preferred_language = lang
            request.user.save(update_fields=['preferred_language'])
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ─── Theme Toggle ─────────────────────────────────────────────────────────────

@require_POST
def toggle_theme(request):
    theme = request.POST.get('theme', 'light')
    request.session['theme'] = theme
    if request.user.is_authenticated:
        request.user.theme = theme
        request.user.save(update_fields=['theme'])
    return JsonResponse({'status': 'ok', 'theme': theme})


# ─── Registration ─────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('service_list')

    role = request.GET.get('role', 'user')
    if request.method == 'POST':
        role = request.POST.get('role', 'user')
        if role == 'service':
            form = ServiceRegisterForm(request.POST)
        else:
            form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.role = role
            user.is_verified = False

            # If phone-based, send OTP
            if user.phone and not user.email:
                user.save()
                _send_otp(user.phone)
                request.session['verify_phone'] = user.phone
                request.session['verify_user_id'] = user.id
                return redirect('verify_phone')
            else:
                user.is_verified = True
                user.save()
                if role == 'service':
                    # Create service profile shell
                    Service.objects.create(
                        owner=user,
                        name=form.cleaned_data.get('service_name', ''),
                        phone=user.phone or '',
                        viloyat=form.cleaned_data.get('viloyat', 'toshkent_sh'),
                        tuman=form.cleaned_data.get('tuman', ''),
                        address=form.cleaned_data.get('address', ''),
                    )
                login(request, user,
                      backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, _('Muvaffaqiyatli ro\'yxatdan o\'tdingiz!'))
                return redirect('service_list')
    else:
        if role == 'service':
            form = ServiceRegisterForm()
        else:
            form = UserRegisterForm()

    return render(request, 'registration/register.html', {
        'form': form, 'role': role,
        'viloyatlar': VILOYATLAR,
        'mutaxassisliklar': MUTAXASSISLIKLAR,
    })


def _send_otp(phone):
    code = SMSVerification.generate_code()
    expires = timezone.now() + timedelta(minutes=10)
    SMSVerification.objects.filter(phone=phone, is_used=False).update(is_used=True)
    SMSVerification.objects.create(phone=phone, code=code, expires_at=expires)
    send_sms_code(phone, code)
    return code


def verify_phone_view(request):
    phone = request.session.get('verify_phone')
    user_id = request.session.get('verify_user_id')

    if not phone or not user_id:
        return redirect('register')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        verification = SMSVerification.objects.filter(
            phone=phone, code=code, is_used=False,
            expires_at__gte=timezone.now()
        ).first()

        if verification:
            verification.is_used = True
            verification.save()
            user = User.objects.get(id=user_id)
            user.is_verified = True
            user.save()
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            if user.role == 'service':
                Service.objects.get_or_create(owner=user, defaults={
                    'name': f"{user.first_name} Servis",
                    'phone': user.phone or '',
                    'viloyat': 'toshkent_sh',
                    'tuman': '',
                    'address': '',
                })
            messages.success(request, _('Telefon tasdiqlandi!'))
            return redirect('service_list')
        else:
            messages.error(request, _('Kod noto\'g\'ri yoki muddati o\'tgan!'))

    return render(request, 'registration/verify_phone.html', {'phone': phone})


def resend_otp(request):
    phone = request.session.get('verify_phone')
    if phone:
        _send_otp(phone)
        return JsonResponse({'status': 'sent'})
    return JsonResponse({'status': 'error'}, status=400)


# ─── Login / Logout ───────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('service_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']

            user = None
            # Try email
            try:
                u = User.objects.get(email=identifier)
                user = authenticate(request, username=u.email, password=password)
            except User.DoesNotExist:
                pass

            # Try phone
            if not user:
                try:
                    u = User.objects.get(phone=identifier)
                    user = authenticate(request, username=u.email or identifier,
                                        password=password)
                    if not user:
                        if u.check_password(password):
                            user = u
                except User.DoesNotExist:
                    pass

            if user and user.is_active:
                login(request, user,
                      backend='django.contrib.auth.backends.ModelBackend')
                activate(user.preferred_language)
                request.session['django_language'] = user.preferred_language
                request.session['theme'] = user.theme

                if user.role == 'admin' or user.is_staff:
                    return redirect('/admin/')
                return redirect('service_list')
            else:
                messages.error(request, _('Login yoki parol noto\'g\'ri!'))
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


# ─── Service List (main page after login) ────────────────────────────────────

@login_required
def service_list(request):
    services = Service.objects.filter(is_approved=True, is_active=True).prefetch_related('images', 'reviews')

    # Filters
    viloyat = request.GET.get('viloyat', '')
    tuman = request.GET.get('tuman', '')
    specialization = request.GET.get('specialization', '')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'newest')

    if viloyat:
        services = services.filter(viloyat=viloyat)
    if tuman:
        services = services.filter(tuman__icontains=tuman)
    if specialization:
        services = services.filter(specializations__contains=specialization)
    if search:
        services = services.filter(
            Q(name__icontains=search) |
            Q(address__icontains=search) |
            Q(description__icontains=search)
        )

    # Nearby filter
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    nearby_services = []

    if user_lat and user_lng and sort == 'nearest':
        try:
            ulat, ulng = float(user_lat), float(user_lng)
            svc_list = list(services.exclude(latitude=None))
            for s in svc_list:
                s.distance = haversine_distance(ulat, ulng,
                                                 float(s.latitude),
                                                 float(s.longitude))
            svc_list.sort(key=lambda x: x.distance)
            services = svc_list
        except (ValueError, TypeError):
            pass

    if sort == 'rating':
        services = sorted(services, key=lambda s: s.avg_rating, reverse=True) if not isinstance(services, list) else sorted(services, key=lambda s: s.avg_rating, reverse=True)
    elif sort == 'newest' and not isinstance(services, list):
        services = services.order_by('-created_at')

    # Favorites
    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(Favorite.objects.filter(user=request.user).values_list('service_id', flat=True))

    paginator = Paginator(services if isinstance(services, list) else list(services), 12)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'service/service_list.html', {
        'page': page,
        'viloyatlar': VILOYATLAR,
        'mutaxassisliklar': MUTAXASSISLIKLAR,
        'selected_viloyat': viloyat,
        'selected_tuman': tuman,
        'selected_spec': specialization,
        'search': search,
        'sort': sort,
        'fav_ids': fav_ids,
        'user_lat': user_lat,
        'user_lng': user_lng,
    })


# ─── Service Detail ───────────────────────────────────────────────────────────

@login_required
def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk, is_approved=True)
    reviews = service.reviews.select_related('user').order_by('-created_at')
    is_fav = Favorite.objects.filter(user=request.user, service=service).exists()
    user_review = reviews.filter(user=request.user).first()

    review_form = ReviewForm()

    if request.method == 'POST' and request.user.role == 'user':
        if user_review:
            review_form = ReviewForm(request.POST, instance=user_review)
        else:
            review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            rev = review_form.save(commit=False)
            rev.service = service
            rev.user = request.user
            rev.save()
            messages.success(request, _('Fikr qoldirildi!'))
            return redirect('service_detail', pk=pk)

    return render(request, 'service/service_detail.html', {
        'service': service,
        'reviews': reviews,
        'is_fav': is_fav,
        'review_form': review_form,
        'user_review': user_review,
        'mutaxassisliklar': dict(MUTAXASSISLIKLAR),
    })


# ─── Service Dashboard ────────────────────────────────────────────────────────

@login_required
def service_dashboard(request):
    if request.user.role != 'service':
        messages.error(request, _('Ruxsat yo\'q'))
        return redirect('service_list')

    service = get_object_or_404(Service, owner=request.user)
    images = service.images.all()
    reviews = service.reviews.select_related('user').order_by('-created_at')[:10]

    return render(request, 'dashboard/service_dashboard.html', {
        'service': service,
        'images': images,
        'reviews': reviews,
        'mutaxassisliklar': MUTAXASSISLIKLAR,
        'viloyatlar': VILOYATLAR,
        'image_count': images.count(),
    })


@login_required
def service_edit(request):
    if request.user.role != 'service':
        return redirect('service_list')

    service = get_object_or_404(Service, owner=request.user)

    if request.method == 'POST':
        form = ServiceProfileForm(request.POST, instance=service)
        if form.is_valid():
            svc = form.save()
            # Handle specializations (multiple checkboxes)
            specs = request.POST.getlist('specializations')
            svc.specializations = specs
            svc.save()

            # Handle image uploads (max 6)
            existing_count = service.images.count()
            uploaded = request.FILES.getlist('images')
            for i, img in enumerate(uploaded):
                if existing_count + i >= 6:
                    break
                ServiceImage.objects.create(service=svc, image=img, order=existing_count + i)

            messages.success(request, _('Ma\'lumotlar yangilandi!'))
            return redirect('service_dashboard')
    else:
        form = ServiceProfileForm(instance=service)

    return render(request, 'dashboard/service_edit.html', {
        'form': form,
        'service': service,
        'mutaxassisliklar': MUTAXASSISLIKLAR,
        'viloyatlar': VILOYATLAR,
        'images': service.images.all(),
    })


@login_required
@require_POST
def delete_service_image(request, img_id):
    if request.user.role != 'service':
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    img = get_object_or_404(ServiceImage, id=img_id, service__owner=request.user)
    img.image.delete(save=False)
    img.delete()
    return JsonResponse({'status': 'deleted'})


# ─── User Profile ─────────────────────────────────────────────────────────────

@login_required
def user_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profil yangilandi!'))
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=request.user)

    favorites = Favorite.objects.filter(user=request.user).select_related('service')
    reviews = Review.objects.filter(user=request.user).select_related('service')[:10]

    return render(request, 'dashboard/user_profile.html', {
        'form': form,
        'favorites': favorites,
        'reviews': reviews,
    })


# ─── Favorites ────────────────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_favorite(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, service=service)
    if not created:
        fav.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


# ─── API: Nearby Services ─────────────────────────────────────────────────────

@login_required
def api_nearby(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        radius = float(request.GET.get('radius', 10))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coords'}, status=400)

    services = Service.objects.filter(
        is_approved=True, is_active=True,
        latitude__isnull=False, longitude__isnull=False
    )

    result = []
    for s in services:
        dist = haversine_distance(lat, lng, float(s.latitude), float(s.longitude))
        if dist <= radius:
            img = s.images.first()
            result.append({
                'id': s.id,
                'name': s.name,
                'address': s.address,
                'rating': s.avg_rating,
                'distance': round(dist, 2),
                'lat': float(s.latitude),
                'lng': float(s.longitude),
                'image': img.image.url if img else '',
            })
    result.sort(key=lambda x: x['distance'])
    return JsonResponse({'services': result[:20]})


# ─── API: Get Tumans by Viloyat ───────────────────────────────────────────────

def api_tumans(request):
    viloyat = request.GET.get('viloyat', '')
    # Return list of tumans for given viloyat (hardcoded common ones)
    tumans_map = {
        'toshkent_sh': ['Yunusobod', 'Chilonzor', 'Mirzo Ulug\'bek', 'Shayxontohur',
                         'Olmosoy', 'Yakkasaroy', 'Uchtepa', 'Bektemir', 'Sergeli',
                         'Mirobod', 'Hamza', 'Yashnobod'],
        'toshkent': ['Zangiota', 'Qibray', 'Yuqorichirchiq', 'Ohangaron',
                      'Bo\'stonliq', 'Parkent', 'Piskent', 'O\'rtachirchiq',
                      'Chinoz', 'Toshkent tumani', 'Bo\'ka', 'Quyi Chirchiq'],
        'andijon': ['Andijon shahri', 'Asaka', 'Baliqchi', 'Bo\'z', 'Buloqboshi',
                     'Izboskan', 'Jalaquduq', 'Qo\'rg\'ontepa', 'Marhamat',
                     'Oltinko\'l', 'Paxtaobod', 'Shahrixon', 'Ulug\'nor', 'Xo\'jaobod'],
        'fargona': ['Farg\'ona shahri', 'Quva', 'Rishton', 'Bag\'dod', 'Beshariq',
                     'Buvayda', 'Dang\'ara', 'Furqat', 'Qo\'shtepa', 'Oltiariq',
                     'O\'zbekiston', 'Toshloq', 'Uchko\'prik', 'Yozyovon', 'Marg\'ilon'],
        'samarqand': ['Samarqand shahri', 'Urgut', 'Kattaqo\'rg\'on', 'Bulung\'ur',
                       'Ishtixon', 'Jomboy', 'Narpay', 'Nurobod', 'Oqdaryo',
                       'Pastdarg\'om', 'Payariq', 'Qo\'shrabot', 'Toyloq'],
    }
    tumans = tumans_map.get(viloyat, [])
    return JsonResponse({'tumans': tumans})
