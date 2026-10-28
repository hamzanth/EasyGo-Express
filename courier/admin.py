from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .sites import custom_admin_site

# Register your models here.
# @admin.register(Order)
# class OrderAdmin(UnfoldModelAdmin):
# 	list_display = ["tracking_number", "status"]
	
# @admin.register(CurrentLocation)
# class OrderAdmin(UnfoldModelAdmin):
# 	list_display = ["location_name"]

# @admin.register(Parcel)
# class OrderAdmin(UnfoldModelAdmin):
# 	list_display = ["name"]

# @admin.register(TransPerson)
# class OrderAdmin(UnfoldModelAdmin):
# 	list_display = ["name", "phone_number", "email", "address"]

# @admin.register(Address)
# class OrderAdmin(UnfoldModelAdmin):
# 	list_display = ["street_address", "apartment_address", "country", "zip"]

@admin.register(Booking)
class OrderAdmin(UnfoldModelAdmin):
	# list_display = ["pickup_address", "destination_address", "status"]
	readonly_fields = ('tracking_number',)

	list_display = (
        "tracking_number",
        "status",
        "current_location_name",
        "location_updated_at",
    )

	search_fields = (
		"tracking_number",
		"sender_name",
		"receiver_name",
	)

	fieldsets = (
		(
			"Shipment",
			{
				"fields": (
					"tracking_number",
					"status",
					"progress",
					"pickup_address",
					"destination_address",
					
				)
			},
		),
		(
			"Sender & Reciever",
			{
				"fields": (
					"sender_name",
					"sender_phone",
					"receiver_name",
					"receiver_phone",

				)
			},
		),
		(
			"Parcel",
			{
				"fields": (
					"parcel_description",
					"weight_kg",
					"pickup_date",
					"pickup_time_window",
					"service_type",
					"distance_km",
					"arrival_time_minutes",
					"estimated_price"
				)
			},
		),
		(
			"Current location",
			{
				"fields": (
					"current_latitude",
					"current_longitude",
					"current_location_name",
					"location_updated_at",
				)
			},
		),
	)


@admin.register(Event)
class OrderAdmin(UnfoldModelAdmin):
	list_display = ["title", "location", "time", "completed"]

# admin.site.register(Order)