from django.urls import path
from .views import aboutView, attendantPortal, loginView, registerView, pricemanageView, stationView, litrelotsView, buylitreView, mydashboardView, purchasesuccessView, user_management, purchaseCreateView,fromPaystackRedirectView,proceedToPaystack, errorView,failureView, attendantConfirm, attendantSuccess, qrexpired, redeemfuel, qrgenerateView,loginTesting, registerTesting

urlpatterns = [
    path('', aboutView, name='home'),
    # path('dashboard/', dashboardView, name='dashboard'),
    path('login/', loginView, name='user-login'),
    path('register/', registerView, name='user-register'),
    path('staff/pricemanage/', pricemanageView, name='user-pricemanage'),
    path('staff/station/', stationView, name='user-station'),
    path('litrelots/', litrelotsView, name='user-litre'),
    path('buylitre/', buylitreView, name='user-buylitre'),
    path('userdashboard/', mydashboardView, name='userdashboard'),
    path('paystack-success-redirect/', fromPaystackRedirectView, name='paystack-redirect'),
    path('successview/<int:pid>/', purchasesuccessView, name='successview'),
    path("staff/users/", user_management, name="user_management"),
    path('purchase/create/', purchaseCreateView, name="purchase-create"),
    path('initialize-payment/', proceedToPaystack, name="payment-initialize"),
    path('error/', errorView, name="error-page"),
    path('failure/', failureView, name="failure-page"),
    path('attendantconfirm/<uuid:qr_code>/', attendantConfirm, name="attendant-confirm"),
    path('attendantsuccess/<int:redemption_id>/', attendantSuccess, name="attendantsuccess"),
    path('qrexpired/<int:redemption_id>/', qrexpired, name="qr-expired"),
    path('redeemfuel/', redeemfuel, name="redeem-fuel"),
    path('qrgenerate/', qrgenerateView, name="qr-generate"),
    path('attendant/', attendantPortal, name='attendant-portal'),
    path('logTest/', loginTesting, name='user-login-test'),
    path('registerTest/', registerTesting, name='user-register-test'),

]
