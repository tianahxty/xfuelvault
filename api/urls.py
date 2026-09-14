from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.api_register, name='api-register'),
    path('login/', views.api_login, name='api-login'),
    path('dashboard/', views.api_dashboard, name='api-dashboard'),
    path('buy/litres/', views.api_buy_litres, name='api-buy-litres'),
    path('initiate-payment/', views.api_initiate_payment, name='api-initiate-payment'),
    path('verify-payment/', views.api_verify_payment, name='api-verify-payment'),
    path('litre-lots/', views.api_litre_lots, name='api-litre-lots'),
    path('wallet/', views.api_wallet, name='api-wallet'),
    path('redeem/', views.api_redeem_info, name='api-redeem'),
    path('generate-qr/', views.api_generate_qr, name='api-generate-qr'),
    path('qr-expired/<int:redemption_id>/', views.api_qr_expired, name='api-qr-expired'),
    path('attendant/', views.api_attendant_portal, name='api-attendant-portal'),
    path('attendant/confirm/<uuid:qr_code>/', views.api_attendant_confirm, name='api-attendant-confirm'),
    path('attendant/success/<int:redemption_id>/', views.api_attendant_success, name='api-attendant-success'),
    path('admin/price/', views.api_admin_price, name='api-admin-price'),
    path('admin/stations/', views.api_admin_stations, name='api-admin-stations'),
    path('admin/users/', views.api_admin_users, name='api-admin-users'),
]
