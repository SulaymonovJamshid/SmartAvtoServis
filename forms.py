"""
SmartAvtoServis - Forms
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
import bleach

from .models import User, Service, Review, VILOYATLAR, MUTAXASSISLIKLAR


class UserRegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Parol'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Parol')}),
        min_length=8
    )
    password2 = forms.CharField(
        label=_('Parolni tasdiqlang'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Parolni tasdiqlang')})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ism')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Familiya')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998901234567'}),
        }

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        phone = cleaned.get('phone')
        if not email and not phone:
            raise forms.ValidationError(_('Email yoki telefon raqam kiritilishi shart!'))
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('Parollar mos kelmadi!'))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ServiceRegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Parol'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label=_('Parolni tasdiqlang'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    service_name = forms.CharField(
        label=_('Servis nomi'),
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    viloyat = forms.ChoiceField(
        label=_('Viloyat'),
        choices=VILOYATLAR,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tuman = forms.CharField(
        label=_('Tuman'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        label=_('Manzil'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ism')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Familiya')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998901234567', 'required': 'required'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('Parollar mos kelmadi!'))
        if not cleaned.get('phone'):
            raise forms.ValidationError(_('Servis uchun telefon raqam majburiy!'))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = 'service'
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    identifier = forms.CharField(
        label=_('Email yoki telefon'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email yoki +998...')
        })
    )
    password = forms.CharField(
        label=_('Parol'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Parolingiz')
        })
    )


class ServiceProfileForm(forms.ModelForm):
    work_days = forms.MultipleChoiceField(
        choices=[
            ('Mon', _('Dushanba')),
            ('Tue', _('Seshanba')),
            ('Wed', _('Chorshanba')),
            ('Thu', _('Payshanba')),
            ('Fri', _('Juma')),
            ('Sat', _('Shanba')),
            ('Sun', _('Yakshanba')),
        ],
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    class Meta:
        model = Service
        fields = [
            'name', 'description', 'experience_years',
            'viloyat', 'tuman', 'shahar', 'address',
            'latitude', 'longitude',
            'work_start', 'work_end', 'work_days', 'is_24h',
            'price_from', 'price_to', 'price_description',
            'phone', 'website', 'telegram',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'viloyat': forms.Select(choices=VILOYATLAR, attrs={'class': 'form-select'}),
            'tuman': forms.TextInput(attrs={'class': 'form-control'}),
            'shahar': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'work_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'work_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_24h': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'price_from': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_to': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_description(self):
        desc = self.cleaned_data.get('description', '')
        return bleach.clean(desc, tags=[], strip=True)

    def save(self, commit=True):
        svc = super().save(commit=False)
        work_days = self.cleaned_data.get('work_days', [])
        svc.work_days = list(work_days)
        if commit:
            svc.save()
        return svc


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(attrs={'id': 'rating-input'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Izohingizni yozing...')
            }),
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')
        return bleach.clean(comment, tags=[], strip=True)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar',
                  'preferred_language', 'theme']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
        }
