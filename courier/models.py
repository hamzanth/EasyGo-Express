from django.db import models
from datetime import datetime
from django.utils import timezone
import uuid
from django.utils import timezone
from courier.google_routes import (
    get_route_info,
    RouteServiceError,
    RouteNotFoundError,
    get_coordinates_from_location
)
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta


# Create your models here.
STATUS_CHOICES = (
    ("DV", "Delivered"),
    ("ND", "Could not be delivered"),
    ("AC", "Active"),
    ("IC", "Inactive"),
    ("PR", "Being processed"),
    ("OH", "On Hold"),
    ("AR", "Arrived at the desination country"),
)

SERVICE_TYPE_CHOICES = (
    ("standard", "Standard"),
    ("Same-day", "Same-day"),
    ("Interstate", "Interstate"),
    ("Business logistics", "Business logistics")
)

PICKUP_WINDOW_CHOICES = (
    ("09:00-12:00", "09:00-12:00"),
    ("12:00-15:00", "12:00-15:00"),
    ("15:00-18:00", "15:00-18:00"),
)



class Order(models.Model):
    status = models.CharField(max_length=2, default="PR", choices=STATUS_CHOICES)
    tracking_number = models.CharField(max_length=10, blank=True, null=True)
    sender = models.ForeignKey("TransPerson", blank=True, null=True, on_delete=models.SET_NULL, related_name="sorder")
    reciever = models.ForeignKey("TransPerson", blank=True, null=True, on_delete=models.SET_NULL, related_name="rorder")
    # price = models.DecimalField(max_digits= 20, decimal_places=2)
    delivery_address = models.ForeignKey("Address", blank=True, null=True, on_delete=models.SET_NULL, related_name="dorder")
    pickup_address = models.ForeignKey("Address", blank=True, null=True, on_delete=models.SET_NULL, related_name="porder")
    shipment_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(blank=True, null=True)

    def get_current_location(self):
        return self.current_location.last()
    
    def get_parcel(self):
        return self.parcel.first()

    # def save(self, *args, **kwargs):
    #     self.shipment_date = timezone.make_aware(self.shipment_date)
    #     self.delivery_date = timezone.make_aware(self.delivery_date)
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pk} - {self.tracking_number}"

class Address(models.Model):
    # user = models.ForeignKey(User, related_name="billing_address", on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100, blank=True, null=True)
    apartment_address = models.CharField(max_length=100, blank=True, null=True) 
    country = models.CharField(max_length=100, blank=True, null=True)
    zip = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.country}({self.zip})"
    
class CurrentLocation(models.Model):
    location_name = models.CharField(max_length=256, blank=True, null=True)
    latitude = models.CharField(max_length=256, blank=True, null=True)
    longitude = models.CharField(max_length=256, blank=True, null=True)
    order = models.ForeignKey("Order", blank=True, null=True, on_delete=models.CASCADE, related_name="current_location")

    def __str__(self):
        return self.location_name

class TransPerson(models.Model):
    name = models.CharField(max_length=256, blank=True, null=True)
    phone_number = models.CharField(max_length=256, blank=True, null=True)
    email = models.EmailField(max_length=256, blank=True, null=True)
    address = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Parcel(models.Model):
    name = models.CharField(max_length=256, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    length = models.DecimalField(max_digits=256, decimal_places=2, default=0)
    width = models.DecimalField(max_digits=256, decimal_places=2, default=0)
    height = models.DecimalField(max_digits=256, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    order = models.ForeignKey("Order", blank=True, null=True, on_delete=models.CASCADE, related_name="parcel")

    def __str__(self):
        return self.name


def get_tomorrow():
    return timezone.now().date() + timedelta(days=1)


class Booking(models.Model):


    BASE_PRICE = 25
    PRICE_PER_KM = 3
    PRICE_PER_EXTRA_KG = 10
    route = None
    location = None


    SERVICE_CHARGES = {
        "Standard": 0,
        "Same-day": 50,
        "Next-day": 20,
        "Interstate": 100,
        "Business logistics": 300,
    }

    class BookingStatus(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"
        AWAITING_PICKUP = "awaiting_pickup", "Awaiting pickup"
        PICKED_UP = "picked_up", "Picked up"
        IN_TRANSIT = "in_transit", "In transit"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    tracking_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Leave blank, It is autogenerated"
    )
    status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING_PAYMENT,
    )

    pickup_address = models.TextField()
    destination_address = models.TextField()

    sender_name = models.CharField(max_length=120)
    sender_phone = models.CharField(max_length=20)

    receiver_name = models.CharField(max_length=120)
    receiver_phone = models.CharField(max_length=20)

    parcel_description = models.TextField()
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)

    distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="If left blank, I will be auto generated"
    )
    estimated_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="If left blank, I will be auto generated",
        blank=True
    )
    arrival_time_minutes = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="If left blank, I will be auto generated"
    )

    pickup_date = models.DateField(default=get_tomorrow)
    pickup_time_window = models.CharField(max_length=50, choices=PICKUP_WINDOW_CHOICES, default=PICKUP_WINDOW_CHOICES[0][0])
    progress = models.PositiveBigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    current_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="If left blank, I will be auto generated"
    )

    current_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="If left blank, I will be auto generated"
    )

    current_location_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="If left blank, I will be auto generated"
    )

    location_updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def clean(self):
        """
        All validation checks for Django Admin must go here.
        """
        super().clean()
        
        try:
            # Your routing check
            self.route = get_route_info(self.pickup_address, self.destination_address)
            self.location = get_coordinates_from_location(self.pickup_address)
            # x = 2/0
            
        except RouteNotFoundError as exc:
            # This will show gracefully as a red banner in the Django Admin
            raise ValidationError(f"Route Not Found: {str(exc)}")
            
        except RouteServiceError as exc:
            raise ValidationError(f"Route Service Error: {str(exc)}")
        
        except Exception as exc:
            # Catching the 'Something went wrong' or other generic errors
            raise ValidationError(f"Validation failed: {str(exc)}")


    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f"EZ-{uuid.uuid4().hex[:8].upper()}"

        if not self.distance_km and not self.arrival_time_minutes and not self.estimated_price:

            self.current_latitude = self.location["latitude"]
            self.current_longitude = self.location["longitude"]
            self.current_location_name = self.location["formatted_address"]
            self.location_updated_at = timezone.now()

            distance_km = self.route["distance_km"]


            dec_base_price = Decimal(str(self.BASE_PRICE))
            dec_distance_km = Decimal(str(distance_km))
            dec_price_per_km = Decimal(str(self.PRICE_PER_KM))
            dec_weight_kg = Decimal(str(self.weight_kg))
            dec_price_per_extra_kg = Decimal(str(self.PRICE_PER_EXTRA_KG))
            dec_service_charge = Decimal(str(self.SERVICE_CHARGES[self.service_type]))

            # Now you can safely run the calculation without type errors
            estimated_price = (
                dec_base_price
                + (dec_distance_km * dec_price_per_km)
                + (dec_weight_kg * dec_price_per_extra_kg)
                + dec_service_charge
            )

            # estimated_price = (
            #     self.BASE_PRICE
            #     + (distance_km * self.PRICE_PER_KM)
            #     + (self.weight_kg * self.PRICE_PER_EXTRA_KG)
            #     + self.SERVICE_CHARGES[self.service_type]
            # )

            self.distance_km=distance_km
            self.estimated_price=estimated_price
            self.arrival_time_minutes=self.route["duration_minutes"]

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.tracking_number} - {self.status}"



class Event(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    time = models.DateTimeField(default=timezone.now)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
