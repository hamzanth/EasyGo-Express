
from datetime import date

from rest_framework import serializers

from .models import Booking, Event


class BookingCreateSerializer(serializers.Serializer):
    pickup_address = serializers.CharField(max_length=500)
    destination_address = serializers.CharField(max_length=500)

    sender_name = serializers.CharField(max_length=120)
    sender_phone = serializers.CharField(max_length=20)

    receiver_name = serializers.CharField(max_length=120)
    receiver_phone = serializers.CharField(max_length=20)

    parcel_description = serializers.CharField(max_length=1000)
    weight_kg = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0.1,
    )

    service_type = serializers.ChoiceField(
        choices=[
            "Standard",
            "Same-day",
            "Next-day",
            "Interstate",
            "Business logistics",
        ]
    )

    pickup_date = serializers.DateField()
    pickup_time_window = serializers.ChoiceField(
        choices=[
            "09:00-12:00",
            "12:00-15:00",
            "15:00-18:00",
        ]
    )

    def validate_pickup_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                "Pickup date cannot be in the past."
            )

        return value

    def validate(self, data):
        if (
            data["pickup_address"].strip().lower()
            == data["destination_address"].strip().lower()
        ):
            raise serializers.ValidationError(
                "Pickup and destination addresses cannot be the same."
            )

        return data


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["title", "location", "time", "completed"]


class CurrentLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    name = serializers.CharField()
    updated_at = serializers.DateTimeField()


class BookingSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(
        source="pickup_address",
        read_only=True,
    )

    destination = serializers.CharField(
        source="destination_address",
        read_only=True,
    )

    estimated_arrival = serializers.IntegerField(
        source="arrival_time_minutes",
        read_only=True,
    )

    progress = serializers.IntegerField(read_only=True)
    events = EventSerializer(many=True, read_only=True)

    current_location = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "tracking_number",
            "status",
            "sender",
            "destination",
            "estimated_arrival",
            "progress",
            "events",
            "current_location",
        ]

    def get_current_location(self, obj):
        if (
            obj.current_latitude is None
            or obj.current_longitude is None
        ):
            return {
                "latitude": None,
                "longitude": None,
                "name": None,
                "updated_at": None,
            }

        return {
            "latitude": float(obj.current_latitude),
            "longitude": float(obj.current_longitude),
            "name": obj.current_location_name,
            "updated_at": obj.location_updated_at,
        }

        # "tracking_number": tracking_number,
        # "status": "Out for delivery",
        # "progress": 90,
        # "sender": "Mile II, Benin",
        # "destination": "Lugbe, Abuja",
        # "estimated_arrival": "Today, 12:10 PM",


class ContactMessageSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    message = serializers.CharField(max_length=2000)


class UpdateShipmentLocationSerializer(serializers.Serializer):
    tracking_number = serializers.CharField(max_length=20)
    location_name = serializers.CharField(max_length=255)

    def validate_tracking_number(self, value):
        return value.strip().upper()

    def validate_location_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Please enter the current shipment location."
            )

        return value