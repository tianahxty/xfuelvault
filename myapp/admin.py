from django.contrib import admin
from .models import Station, FuelPrice, LitrePurchase, LitreWallet, LitreLot, fuelRedemption,InitializePaymentRecord
# after creating the model we need to register it in the admin panel so that we can see it in the admin panel and also migrate it

# Register your models here.
admin.site.register(Station)
admin.site.register(InitializePaymentRecord)

@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
    list_display = ('price_per_litre', 'effective_from', 'set_by')


@admin.register(LitrePurchase)
class LitrePurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'litres_bought', 'price_per_litre', 'total_amount', 'created_at')
    
@admin.register(LitreWallet)
class LitreWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    
@admin.register(LitreLot)
class LitrelotAdmin(admin.ModelAdmin):
    list_display = ('user', 'purchase', 'litres_purchased', 'litres_remaining', 'price_per_litre', 'expires_at', 'status')
@admin.register(fuelRedemption)
class fuelRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'litres_redeemed', 'qr_code', 'qr_expires_at', 'status', 'redeemed_by', 'created_at', 'redeemed_at')