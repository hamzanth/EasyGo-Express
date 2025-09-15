from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .sites import custom_admin_site

# Register your models here.
@admin.register(Order)
class OrderAdmin(UnfoldModelAdmin):
	list_display = ["tracking_number", "status"]
	
@admin.register(CurrentLocation)
class OrderAdmin(UnfoldModelAdmin):
	list_display = ["location_name"]

@admin.register(Parcel)
class OrderAdmin(UnfoldModelAdmin):
	list_display = ["name"]

@admin.register(TransPerson)
class OrderAdmin(UnfoldModelAdmin):
	list_display = ["name", "phone_number", "email", "address"]

@admin.register(Address)
class OrderAdmin(UnfoldModelAdmin):
	list_display = ["street_address", "apartment_address", "country", "zip"]

# admin.site.register(Order)