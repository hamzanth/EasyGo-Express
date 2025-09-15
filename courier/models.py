from django.db import models
from datetime import datetime
from django.utils import timezone

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

class Order(models.Model):
    status = models.CharField(max_length=2, default="PR", choices=STATUS_CHOICES)
    tracking_number = models.CharField(max_length=10, blank=True, null=True)
    sender = models.ForeignKey("TransPerson", blank=True, null=True, on_delete=models.SET_NULL, related_name="sorder")
    reciever = models.ForeignKey("TransPerson", blank=True, null=True, on_delete=models.SET_NULL, related_name="rorder")
    price = models.DecimalField(max_digits= 20, decimal_places=2)
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
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100) 
    country = models.CharField(max_length=100)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.country}({self.zip})"
    
class CurrentLocation(models.Model):
    location_name = models.CharField(max_length=256)
    latitude = models.CharField(max_length=256)
    longitude = models.CharField(max_length=256)
    order = models.ForeignKey("Order", blank=True, null=True, on_delete=models.CASCADE, related_name="current_location")

    def __str__(self):
        return self.location_name

class TransPerson(models.Model):
    name = models.CharField(max_length=256)
    phone_number = models.CharField(max_length=256)
    email = models.EmailField(max_length=256, blank=True, null=True)
    address = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Parcel(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    weight = models.DecimalField(max_digits=7, decimal_places=2)
    length = models.DecimalField(max_digits=256, decimal_places=2, default=0)
    width = models.DecimalField(max_digits=256, decimal_places=2, default=0)
    height = models.DecimalField(max_digits=256, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    order = models.ForeignKey("Order", blank=True, null=True, on_delete=models.CASCADE, related_name="parcel")

    def __str__(self):
        return self.name