from decimal import Decimal
from django.utils import timezone

def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }

def serialize_fuel_price(price):
    if not price:
        return None
    return {
        'price_per_litre': str(price.price_per_litre),
        'effective_from': price.effective_from.isoformat(),
        'set_by': price.set_by.username if price.set_by else None,
    }

def serialize_wallet(wallet):
    return {
        # 'balance': str(wallet.balance),
        'available_litres': str(wallet.available_litres),
    }

def serialize_purchase(purchase):
    return {
        'id': purchase.id,
        'litres_bought': str(purchase.litres_bought),
        'price_per_litre': str(purchase.price_per_litre),
        'total_amount': str(purchase.total_amount),
        'payment_reference': purchase.payment_reference,
        'created_at': purchase.created_at.isoformat(),
    }

def serialize_litre_lot(lot):
    if not lot:
        return None
    return {
        'id': lot.id,
        'litres_purchased': str(lot.litres_purchased),
        'litres_remaining': str(lot.litres_remaining),
        'price_per_litre': str(lot.price_per_litre),
        'expires_at': lot.expires_at.isoformat(),
        'status': lot.status,
        'days_left': max((lot.expires_at - timezone.now()).days, 0),
        'percent_remaining': int((lot.litres_remaining / lot.litres_purchased) * 100) if lot.litres_purchased else 0,
    }

def serialize_redemption(redemption):
    return {
        'id': redemption.id,
        'litres_redeemed': str(redemption.litres_redeemed),
        'qr_code': str(redemption.qr_code),
        'qr_expires_at': redemption.qr_expires_at.isoformat(),
        'status': redemption.status,
        'created_at': redemption.created_at.isoformat(),
        'redeemed_at': redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
        'station': redemption.station.name,
        'station_code': redemption.station.code,
        'verification_code': redemption.verificaton_code,
        'is_expired': redemption.is_expired,
    }

def serialize_station(station):
    return {
        'id': station.id,
        'name': station.name,
        'address': station.address,
        'code': station.code,
        'is_active': station.is_active,
        'created_at': station.created_at.isoformat(),
    }


# curl -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: X-Requested-With" -X OPTIONS --verbose http://127.0.0.1:8000/api/