from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .models import FuelPrice, Station, LitrePurchase, LitreLot, LitreWallet, InitializePaymentRecord, fuelRedemption
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
import uuid
from .utils_pay import initializePaystackPayment,verifyPayment
import traceback
import qrcode
import base64
from io import BytesIO

def aboutView(request: HttpRequest) -> HttpResponse:
    try :
        c = 'tyu'
        int(c)
        return HttpResponse("<h2>hello world</h2>")
    except TypeError : 
        return redirect('/error/')
    except Exception :
        return redirect("/failure/")
# Create your views here.
def registerView(request):
    # get request, post request
    if request.method == "POST":
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # validate the data 
        if not email or not password1 or not password2:
                # prevent them from signing up etc
            error = "all details must be provided"
            return render(request, 'register.html', {"error": error, 'success':None})

        if len(password1)< 6:
            error1 = 'password is too short'
            return render(request, 'register.html', {"error1": error1, 'success':None})
        
        if password1 != password2:
            error2 = 'password does not match'
            return render(request, 'register.html', {"error2": error2, 'success':None})
        
        if username and User.objects.filter(username=username).exists():
            error3 = 'username already exists'
            return render(request, 'register.html', {"error3": error3, 'success':None})
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password1, first_name=first_name, last_name=last_name)
            user.save()
            print(user)
            return redirect('user-login')
        except Exception as e :
                print(e)
    return render(request, 'register.html', {})


def registerTesting(request):
    # get request, post request
        if request.method == "POST":
            first_name = request.POST.get('firstname')
            last_name = request.POST.get('lastname')
            username = request.POST.get('username')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            # validate the data 
            if not email or not password1 or not password2:
                    # prevent them from signing up etc
                error = "all details must be provided"
                return render(request, 'registerTest.html', {"error": error, 'success':None})
    
            if len(password1)< 6:
                error1 = 'password is too short'
                return render(request, 'registerTest.html', {"error1": error1, 'success':None})
            
            if password1 != password2:
                error2 = 'password does not match'
                return render(request, 'registerTest.html', {"error2": error2, 'success':None})
            
            if username and User.objects.filter(username=username).exists():
                error3 = 'username already exists'
                return render(request, 'registerTest.html', {"error3": error3, 'success':None})
            
            try:
                user = User.objects.create_user(username=username, email=email, password=password1, first_name=first_name, last_name=last_name)
                user.save()
                print(user)
                return redirect('user-login')
            except Exception as e :
                    print(e)
        return render(request, 'registerTest.html', {})
    
    
    

# @login_required(login_url='user-login')
# def dashboardView(request:HttpRequest):
#     if request.user.is_superuser:
#         return redirect('/staff/pricemanage/')
#     return render(request,"dashboard.html",{})

# login view to authenticate the user and log them in
def loginView(request:HttpRequest):
    # authenticate the user and log them in
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('userdashboard')
        else:
            error = "Invalid username or password"
            return render(request, 'login.html', {"error": error})
    
    return render(request, 'login.html', {})

def loginTesting(request):
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                    login(request, user)
                    return redirect('userdashboard')
            else:
                error = "Invalid username or password"
                return render(request, 'logTest.html', {"error": error})
        return render(request,'logTest.html',{})

# for user
@login_required(login_url='user-login')
def mydashboardView (request:HttpRequest):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')

    price = FuelPrice.objects.first()
    username = request.user.username

    # Wallet is created lazily the first time someone visits their
    # dashboard, in case a wallet row wasn't created at signup.
    wallet, _ = LitreWallet.objects.get_or_create(user=request.user)
    available_litres = wallet.available_litres

    estimated_value = None
    if price:
        estimated_value = available_litres * price.price_per_litre

    # FIX: this used to be LitrePurchase.objects.all(), which showed
    # every user's purchases on every dashboard. Now scoped to request.user.
    purchase_history = LitrePurchase.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Soonest-expiring active lot, used for the "Expiring soon" banner.
    expiring_lot = (
        LitreLot.objects
        .filter(user=request.user, status="ACTIVE", expires_at__gt=timezone.now())
        .order_by('expires_at')
        .first()
    )

    context = {
        'price': price,
        'wallet': wallet,
        'available_litres': available_litres,
        'estimated_value': estimated_value,
        'purchase_history': purchase_history,
        'expiring_lot': expiring_lot,
        'username': username,
    }
    return render(request,"user/mydashboard.html", context)


@login_required(login_url='user-login')
def buylitreView (request:HttpRequest):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')
    price = FuelPrice.objects.first()
    return render(request,"user/buylitres.html",{'price': price}) 


@login_required(login_url="user-login")
def proceedToPaystack(request: HttpRequest):
    if request.user.is_superuser:
        return redirect("/staff/pricemanage/")

    if request.method != "POST":
        return redirect("user-buylitre")

    # -----------------------------------------
    # Get litres from the user
    # -----------------------------------------
    litres_raw = request.POST.get("litres")

    try:
        litres = Decimal(litres_raw)
    except (TypeError, InvalidOperation):
        return render(request, "user/buylitres.html", {
            "price": FuelPrice.objects.first(),
            "error": "Enter a valid number of litres.",
        })

    if litres <= 0:
        return render(request, "user/buylitres.html", {
            "price": FuelPrice.objects.first(),
            "error": "Litres must be greater than zero.",
        })

    # -----------------------------------------
    # Get the CURRENT price from our database
    # Never trust price submitted by browser
    # -----------------------------------------
    fuel_price = FuelPrice.objects.first()

    if fuel_price is None:
        return render(request, "user/buylitres.html", {
            "price": None,
            "error": "Fuel price is currently unavailable.",
        })

    price_per_litre = fuel_price.price_per_litre

    # -----------------------------------------
    # Calculate total
    # -----------------------------------------
    total_amount = litres * price_per_litre

    # Paystack expects amount in kobo
    paystack_amount = int(total_amount * Decimal("100"))

    # -----------------------------------------
    # Generate our transaction reference
    # -----------------------------------------
    payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"

    try:
        # -----------------------------------------
        # Initialize Paystack transaction
        # -----------------------------------------
        payment = initializePaystackPayment(
            request.user.email or request.user.username,
            paystack_amount,
            payment_reference,
        )

        if not payment:
            return redirect("user-buylitre")

        # -----------------------------------------
        # Save what we expected to be paid
        # -----------------------------------------
        InitializePaymentRecord.objects.create(
            user=request.user,
            reference=payment_reference,
            litres_to_purchase=litres,
            price_per_litre=price_per_litre,
            total_amount_to_pay=total_amount,
        )

        # -----------------------------------------
        # Send user to Paystack
        # -----------------------------------------
        return redirect(payment["payment_url"])

    except Exception as e:
        print("PAYMENT INITIALIZATION ERROR:", e)
        return redirect("user-buylitre")
       

@login_required(login_url="user-login")
def purchaseCreateView(request: HttpRequest):

    if request.user.is_superuser:
        return redirect("/staff/pricemanage/")

    reference = request.GET.get("reference")

    if not reference:
        return redirect("/failure/")

    try:
        # =====================================================
        # 1. Find payment record belonging to THIS USER
        # =====================================================
        payment_record = InitializePaymentRecord.objects.get(
            reference=reference,
            user=request.user,
        )

        # =====================================================
        # 2. Prevent the same payment from being used twice
        # =====================================================
        if payment_record.used:
            print("PAYMENT ALREADY USED")
            return redirect("/failure/")

        # =====================================================
        # 3. Verify payment with Paystack
        # =====================================================
        response = verifyPayment(reference)

        if not response:
            print("PAYSTACK VERIFICATION FAILED")
            return redirect("/failure/")

        if not response.get("success"):
            print("PAYSTACK PAYMENT NOT SUCCESSFUL")
            return redirect("/failure/")

        # =====================================================
        # 4. Compare Paystack amount with our expected amount
        # =====================================================
        paystack_amount = response["amount"]

        expected_amount_in_kobo = int(
            payment_record.total_amount_to_pay * Decimal("100")
        )

        if paystack_amount != expected_amount_in_kobo:
            print(
                "PAYMENT AMOUNT MISMATCH:",
                paystack_amount,
                expected_amount_in_kobo,
            )
            return redirect("/failure/")

        # =====================================================
        # 5. Make sure this reference hasn't already created
        #    a purchase
        # =====================================================
        if LitrePurchase.objects.filter(
            payment_reference=reference
        ).exists():
            print("PURCHASE ALREADY EXISTS")
            return redirect("/failure/")

        # =====================================================
        # 6. Create purchase + lot atomically
        # =====================================================
        with transaction.atomic():

            purchase = LitrePurchase.objects.create(
                user=request.user,
                litres_bought=payment_record.litres_to_purchase,
                price_per_litre=payment_record.price_per_litre,
                payment_reference=payment_record.reference,
            )

            litre_lot = LitreLot.objects.create(
                user=request.user,
                purchase=purchase,
                litres_purchased=payment_record.litres_to_purchase,
                litres_remaining=payment_record.litres_to_purchase,
                price_per_litre=payment_record.price_per_litre,
                expires_at=timezone.now() + timedelta(days=90),
                status="ACTIVE",
            )

            # Mark payment as consumed only after
            # purchase + lot have successfully been created.
            payment_record.used = True
            payment_record.status = "SUCCESS"
            payment_record.save(
                update_fields=["used", "status"]
            )

        # =====================================================
        # 7. Redirect to success page
        # =====================================================
        return redirect(
            f"/successview/{litre_lot.id}"
        )

    except InitializePaymentRecord.DoesNotExist:
        print("PAYMENT RECORD NOT FOUND")
        return redirect("/failure/")

    except Exception as e:
        print("========== PURCHASE ERROR ==========")
        print("ERROR:", e)
        traceback.print_exc()
        print("====================================")
        return redirect("/error/")



@login_required(login_url='user-login')
def litrelotsView (request:HttpRequest):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')

    now = timezone.now()

    active_lots = list(
        LitreLot.objects
        .filter(user=request.user, status="ACTIVE", expires_at__gt=now, litres_remaining__gt=0)
        .select_related('purchase')
        .order_by('expires_at')
    )
    expired_lots = list(
        LitreLot.objects
        .filter(user=request.user)
        .filter(Q(status="EXPIRED") | Q(status="EXHAUSTED") | Q(expires_at__lte=now) | Q(litres_remaining=0))
        .select_related('purchase')
        .order_by('-expires_at')
    )

    # Attach a couple of display-only attributes the template needs.
    # These aren't model fields - they're just computed per-request.
    for lot in active_lots:
        days_left = (lot.expires_at - now).days
        lot.days_left = max(days_left, 0)
        lot.badge_level = "warning" if lot.days_left <= 14 else "healthy"
        lot.percent_remaining = (
            int((lot.litres_remaining / lot.litres_purchased) * 100)
            if lot.litres_purchased else 0
        )

    for lot in expired_lots:
        lot.percent_remaining = (
            int((lot.litres_remaining / lot.litres_purchased) * 100)
            if lot.litres_purchased else 0
        )

    wallet, _ = LitreWallet.objects.get_or_create(user=request.user)

    context = {
        'active_lots': active_lots,
        'expired_lots': expired_lots,
        'wallet': wallet,
        'available_litres': wallet.available_litres,
        'active_lot_count': len(active_lots),
    }
    return render(request,"user/litrelots.html", context)


@login_required(login_url='user-login')
def fromPaystackRedirectView(request:HttpRequest):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')
    # price = FuelPrice.objects.first()
    
    return render(request,"user/purchasesuccess.html",{"user_lot_purchased":None})  


@login_required(login_url='user-login')
def purchasesuccessView (request:HttpRequest,pid):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')
    # price = FuelPrice.objects.first()
    try : 
        user_litre_lot = LitreLot.objects.get(pk=pid)
        return render(request,"user/purchasesuccess.html",{"user_lot_purchased":user_litre_lot})
    except LitreLot.DoesNotExist :
        return redirect('/error/?error=litre does not exist')  
    except Exception as e :
        return redirect('/error/?error=page not found')



@login_required(login_url='user-login')
def walletView (request:HttpRequest):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')
    wallet, _ = LitreWallet.objects.get_or_create(user=request.user)
    return render(request,"user/mydashboard.html",{'wallet': wallet, 'available_litres': wallet.available_litres})
    



# for admin
@staff_member_required
def pricemanageView(request:HttpRequest):
    if not request.user.is_superuser:
        return redirect('user_dashboard')
    error = None
    success = None
    if request.method == "POST":
        new_price = request.POST.get('price_per_litre')
        if not new_price:
            error = "Price must be provided."
        elif not new_price.isdigit:
            error = "Price must be a valid number."
        else:
            try:
                FuelPrice.objects.create(price_per_litre=Decimal(new_price), set_by=request.user)
                success = "Price updated successfully."
            except Exception as e:
                error = "An error occurred while updating the price."
    price = FuelPrice.objects.first()
    price_history = FuelPrice.objects.all()
    return render(request, 'admin/priceManage.html', {'price': price, 'error': error, 'success': success, "price_history": price_history})


@staff_member_required
def stationView(request):
    if not request.user.is_superuser:
        return redirect('user-dashboard')
    error = None
    success = None
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle':
            station_id = request.POST.get('station_id')
            station = Station.objects.filter(id=station_id).first()
            if station:
                station.is_active = not station.is_active
                station.save()
                success = f'"{station.name}" is now {"active" if station.is_active else "inactive"}.'

        else:
            new_station = request.POST.get('name')
            if not new_station:
                error1 = 'new station has to be set'
                return render(request, 'admin/station.html', {'error1': error1})
            new_address = request.POST.get('address')
            new_code = request.POST.get('code')
            if not new_code.isdigit:
                error3 = 'please enter a valid code'
                return render(request, 'admin/station.html', {'error3': error3,})
            try:
                brand_new_station = Station.objects.create(name=new_station, code=new_code, address= new_address)
                brand_new_station.save()
                success = 'station updated successfully'
            except Exception as e:
                error = 'An error occured while adding station'
                print(e)
    stations = Station.objects.first()
    station_history = Station.objects.all()
    return render(request, 'admin/station.html', {'error': error, 'success': success, 'stations': stations, 'station_history': station_history})


@staff_member_required
def user_management(request):
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)

    all_users = User.objects.all().order_by("-date_joined")

    paginator = Paginator(all_users, 15)  # 15 users per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "users": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "staff_users": User.objects.filter(is_staff=True).count(),
        "new_users_this_month": User.objects.filter(date_joined__gte=start_of_month).count(),
    }
    return render(request, "admin/users.html", context)


def errorView(request):
    error = request.GET.get('error')
    return render(request,'user/error-page.html', {'error':error})

def failureView(request):
    return render(request,'user/purchase-failed.html', {})

# @staff_member_required
def attendantConfirm(request, qr_code):
    redemption = fuelRedemption.objects.filter(qr_code=qr_code).first()

    if not redemption:
        return render(request, 'user/attendant-confirm.html', {
            'redemption': None,
            'error': 'This redemption code was not found.',
        })

    error = None

    # If it's still PENDING but the expiry already passed, mark it EXPIRED
    # now rather than letting an attendant confirm a stale code.
    if redemption.status == "PENDING" and redemption.is_expired:
        redemption.status = "EXPIRED"
        redemption.save(update_fields=["status"])

    if redemption.status != "PENDING":
        error = f"This redemption is {redemption.get_status_display()} and can no longer be confirmed."

    if request.method == "POST" and redemption.status == "PENDING":
        litres_to_deduct = redemption.litres_redeemed
        now = timezone.now()

        try:
            with transaction.atomic():
                active_lots = (
                    LitreLot.objects
                    .select_for_update()
                    .filter(user=redemption.user, status="ACTIVE", expires_at__gt=now, litres_remaining__gt=0)
                    .order_by('expires_at')
                )

                remaining = litres_to_deduct
                for lot in active_lots:
                    if remaining <= 0:
                        break
                    deduct = min(lot.litres_remaining, remaining)
                    lot.litres_remaining -= deduct
                    remaining -= deduct
                    if lot.litres_remaining <= 0:
                        lot.status = "EXHAUSTED"
                    lot.save(update_fields=["litres_remaining", "status"])

                if remaining > 0:
                    raise ValueError("User no longer has enough litres available.")

                redemption.status = "REDEEMED"
                redemption.redeemed_by = request.user
                redemption.redeemed_at = now
                redemption.save(update_fields=["status", "redeemed_by", "redeemed_at"])

        except ValueError as e:
            error = str(e)
        else:
            return redirect('attendantsuccess', redemption_id=redemption.id)

    return render(request, 'user/attendant-confirm.html', {
        'redemption': redemption,
        'error': error,
    })

# @staff_member_required
def attendantSuccess(request, redemption_id):
    redemption = fuelRedemption.objects.filter(id=redemption_id).first()
    return render(request, 'user/attendant-success.html', {'redemption': redemption})



@login_required(login_url='user-login')
def redeemfuel(request: HttpRequest):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')

    wallet, _ = LitreWallet.objects.get_or_create(user=request.user)
    stations = Station.objects.filter(is_active=True).order_by('name')

    return render(request, 'user/redeem-fuel.html', {
        'wallet': wallet,
        'available_litres': wallet.available_litres,
        'stations': stations,
    })

@login_required(login_url='user-login')
def qrgenerateView(request: HttpRequest):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')

    if request.method != "POST":
        return redirect('redeem-fuel')

    wallet, _ = LitreWallet.objects.get_or_create(user=request.user)
    stations = Station.objects.filter(is_active=True).order_by('name')

    litres_raw = request.POST.get('litres')
    station_id = request.POST.get('station')

    try:
        litres_to_redeem = Decimal(litres_raw)
    except (TypeError, InvalidOperation):
        return render(request, 'user/redeem-fuel.html', {
            'wallet': wallet, 'available_litres': wallet.available_litres,
            'stations': stations, 'error': 'Enter a valid number of litres.',
        })

    if litres_to_redeem <= 0:
        return render(request, 'user/redeem-fuel.html', {
            'wallet': wallet, 'available_litres': wallet.available_litres,
            'stations': stations, 'error': 'Litres must be greater than zero.',
        })

    if litres_to_redeem > wallet.available_litres:
        return render(request, 'user/redeem-fuel.html', {
            'wallet': wallet, 'available_litres': wallet.available_litres,
            'stations': stations,
            'error': f'You only have {wallet.available_litres}L available.',
        })

    station = Station.objects.filter(id=station_id, is_active=True).first()
    if not station:
        return render(request, 'user/redeem-fuel.html', {
            'wallet': wallet, 'available_litres': wallet.available_litres,
            'stations': stations, 'error': 'Please select a valid station.',
        })

    # Nothing is deducted here — this is only a reservation request.
    # Litres leave the wallet later, when an attendant confirms redemption.
    redemption = fuelRedemption.objects.create(
        user=request.user,
        station=station,
        litres_redeemed=litres_to_redeem,
        qr_expires_at=timezone.now() + timedelta(minutes=10),
        status="PENDING",
    )
    seconds_remaining = int((redemption.qr_expires_at - timezone.now()).total_seconds())
    
    confirm_url = request.build_absolute_uri(
        reverse('attendant-confirm', args=[redemption.qr_code])
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(confirm_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0B3D2E", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render(request, 'user/redemption.html', {
        'redemption': redemption,
        'seconds_remaining': seconds_remaining,
        'qr_base64': qr_base64,   # <- this is what your template's data:image/png;base64,{{ qr_base64 }} expects
    })

@login_required(login_url='user-login')
def qrexpired(request: HttpRequest, redemption_id=None):
    if request.user.is_superuser:
        return redirect('/staff/pricemanage/')

    redemption = None
    if redemption_id:
        redemption = fuelRedemption.objects.filter(id=redemption_id, user=request.user).first()
        if redemption and redemption.status == "PENDING" and redemption.is_expired:
            redemption.status = "EXPIRED"
            redemption.save(update_fields=["status"])

    return render(request, 'user/qrRedemption-expired.html', {'redemption': redemption})

# @staff_member_required
def attendantPortal(request):
    error = None

    if request.method == "POST":
        code = request.POST.get('verification_code', '').strip()

        if not code:
            error = "Enter a verification code."
        else:
            # verificaton_code isn't a real database column - it's
            # recalculated from qr_code every time it's accessed - so it
            # can't be filtered with .filter(verificaton_code=code).
            # We only search PENDING, unexpired redemptions, since a code
            # only means anything for a redemption still waiting to be
            # confirmed - this keeps the search space small in practice.
            now = timezone.now()
            candidates = fuelRedemption.objects.filter(status="PENDING", qr_expires_at__gt=now)

            match = None
            for redemption in candidates:
                if redemption.verificaton_code == code:
                    match = redemption
                    break

            if match:
                return redirect('attendant-confirm', qr_code=match.qr_code)
            else:
                error = "No matching pending redemption found for that code."

    recent_redemptions = fuelRedemption.objects.filter(
        redeemed_by=request.user, status="REDEEMED"
    ).order_by('-redeemed_at')[:5]

    return render(request, 'user/attendant-portal.html', {
        'error': error,
        'recent_redemptions': recent_redemptions,
    })