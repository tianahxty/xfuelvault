from django.db import models
import uuid
from django.contrib.auth.models import User
from django.utils import timezone 
# models is defined as a class that is used to define the structure of the database tables and their relationships. It is a way to define the data that will be stored in the database and how it will be accessed and manipulated. 
# Create your models here.
# station, fuelprice, litrevault, litrepurchase, litrelot, fuelredemption

'''
NAME ADDRESS STATIONCODE, created at, is active
'''

class Station(models.Model):
    # start adding prespection for the station
    # name : str
    # address : str
    name = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
class FuelPrice(models.Model):
    price_per_litre = models.DecimalField(max_digits=8, decimal_places=2)
    effective_from = models.DateTimeField(auto_now_add=True)
    set_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_prices_set'
    )

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f"₦{self.price_per_litre} / L"
    
class LitrePurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    # will still add from_which_station
    litres_bought = models.DecimalField(max_digits=10, decimal_places=3)
    price_per_litre = models.DecimalField(max_digits=8, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_reference = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.user.username} bought {self.litres_bought}L for a total of ₦{self.total_amount} at ₦{self.price_per_litre}/L"
            )
    
    def save(self, *args, **kwargs):
        # Calculate total_amount before saving
        self.total_amount = self.litres_bought * self.price_per_litre
        super().save(*args, **kwargs)


class LitreWallet(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='litre_wallet'
        )
    # balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Litre Wallet"
    
    @property
    def available_litres(self):
        # FIX: this used to call self.user.litre_lots, but LitreLot's
        # related_name below was "litre_lot" (singular) - a straight
        # mismatch that would raise AttributeError the first time this
        # property was ever touched. related_name is now "litre_lots".
        lots = self.user.litre_lots.filter(
            status='ACTIVE',
            expires_at__gt=timezone.now(),
            litres_remaining__gt=0
        )
        return sum(
            (lot.litres_remaining for lot in lots),
            0
        )
        
class LitreLot(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "active"),
        ("EXHAUSTED", "exhausted"),
        ("EXPIRED", "expired"),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="litre_lots"
    )
    purchase = models.OneToOneField(
        LitrePurchase,
        on_delete=models.CASCADE,
        related_name="litre_lot"  
    )
    litres_purchased = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )
    litres_remaining = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )
    price_per_litre = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )
    expires_at = models.DateTimeField()
    
    status = models.CharField(
        max_length=20,
        choices= STATUS_CHOICES,
        default="ACTIVE"
    )

    class Meta:
        ordering = ['expires_at']
    
    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.litres_remaining}L remaining"
        )
        
    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
    

class fuelRedemption(models.Model):
    
    STATUS_CHOICES = [
        ("PENDING", "pending"),
        ("REDEEMED", "redeemed"),
        ("EXPIRED", "expired"),
        ("CANCELLED", "cancelled"),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="fuel_redemption"
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="redemptions"
    )
    litres_redeemed = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )
    qr_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    qr_expires_at = models.DateTimeField()
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )
    
    redeemed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        
        related_name="attendant_redemption"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    redeemed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.litres_redeemed} - "
            f"{self.status}"
        )
        
    @property
    def is_expired(self):
        return timezone.now() >= self.qr_expires_at
    
    @property
    def verificaton_code(self):
        '''
        a short, human-typable 6-digit code derived fromm the QR UUID
        This isn't stored anywhere - it's calculated the same way every time from 'qr_code', so an attendant can type it in by hand and we can look the redemption back up by recalculating the same code for pending redemptions.
        '''
        return str(int(self.qr_code.hex[:6], 16) % 1000000).zfill(6)
    

class InitializePaymentRecord(models.Model):
    """_summary_
        this model is used to record when a user tries to initialize payment for purchasing fuel using our external payment gateway
    Args:
        models (_type_): _description_
        user : This associates the person that initializes the transaction
        reference : This is the payment unique reference that would be documented over by the payment gateway as their unique means of identifying this transaction
        used : This is used in app to know if a successful payment been intialized has been used otherwise not used which might be due to any of the status value 
    """
    STATUS_CHOICES = [
            ("PENDING", "pending"),
            ("SUCCESS", "success"),
            ("EXPIRED", "expired"),
            ("CANCELLED", "cancelled"),
        ]
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100,unique=True)
    used = models.BooleanField(default=False)
    litres_to_purchase = models.DecimalField(max_digits=10, decimal_places=3)
    price_per_litre = models.DecimalField(max_digits=8, decimal_places=2)
    total_amount_to_pay = models.DecimalField(max_digits=10, decimal_places=3) 
    status = models.CharField(choices=STATUS_CHOICES,max_length=10, default='PENDING')
    
    