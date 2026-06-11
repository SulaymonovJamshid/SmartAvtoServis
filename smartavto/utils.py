"""
SmartAvtoServis - Utilities
"""
import math
from django.conf import settings


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lon points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def send_sms_code(phone, code):
    """Send 6-digit SMS verification code."""
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"SmartAvtoServis: Tasdiqlash kodingiz: {code}. Kod 10 daqiqa amal qiladi.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )
        return message.sid
    except Exception as e:
        # In development, print the code
        print(f"[SMS DEBUG] Phone: {phone}, Code: {code}")
        return None


def format_phone(phone):
    """Normalize Uzbek phone number."""
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) == 9:
        return f'+998{phone}'
    if len(phone) == 12 and phone.startswith('998'):
        return f'+{phone}'
    return f'+{phone}' if not phone.startswith('+') else phone
