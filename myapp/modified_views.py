from decimal import Decimal, InvalidOperation
import uuid

from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import redirect, render


from datetime import timedelta
from django.shortcuts import redirect
from django.utils import timezone

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


'''
                  PAYMENT SIDE
                      │
                      ▼
        InitializePaymentRecord
        ┌─────────────────────────┐
        │ user                    │
        │ reference               │
        │ litres                  │
        │ price                   │
        │ total                   │
        │ used                    │
        │ status                  │
        └────────────┬────────────┘
                     │
                     │ Paystack verifies
                     ▼
              LitrePurchase
        ┌─────────────────────────┐
        │ user                    │
        │ litres_bought           │
        │ price_per_litre         │
        │ total_amount            │
        │ payment_reference       │
        └────────────┬────────────┘
                     │
                     ▼
                 LitreLot
        ┌─────────────────────────┐
        │ litres_purchased        │
        │ litres_remaining        │
        │ price_per_litre         │
        │ expires_at              │
        │ status                  │
        └────────────┬────────────┘
                     │
                     ▼
             AVAILABLE LITRES
           = SUM(litres_remaining
             from valid active lots)



'''
