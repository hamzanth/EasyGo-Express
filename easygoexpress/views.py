from django.http import HttpResponse, request
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse

from courier.models import Booking
from courier.serializers import (
    BookingCreateSerializer, 
    BookingSerializer, 
    ContactMessageSerializer,
    UpdateShipmentLocationSerializer
	)
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from rest_framework.authentication import SessionAuthentication
from courier.exceptions import custom_exception_handler
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone


from courier.google_routes import (
    get_route_info,
    RouteServiceError,
    RouteNotFoundError,
    get_coordinates_from_location
)

def index(request):
	return render(request, "index.html")

class AboutView(View):
	def get(self, request):
		return render(request, "about.html")
	
class ContactView(View):
	def get(self, request):
		return render(request, "contact.html")

class ServiceView(View):
	def get(self, request):
		return render(request, "services.html")

class BlogView(View):
	def get(self, request):
		return render(request, "blog.html")

class Read1(View):
	def get(self, request):
		return render(request, "read1.html")

class Read2(View):
	def get(self, request):
		return render(request, "read2.html")

class PricingView(View):
	def get(self, request):
		return render(request, "pricing.html")
	
class AboutUsView(View):
	def get(self, request):
		return render(request, "about.html")

class TrackView(View):
	def get(self, request):
		return render(request, "track.html")

class AdminLogin(View):
	def get(self, request):
		return render(request, "admin_login.html")
	
	def post(self, request):
		email = request.POST.get("email")
		password = request.POST.get("password")
		user = authenticate(email=email, password=password)
		if user is not None:
			login(request, user)
			return redirect("accounts:admin-dashboard")
		else:
			return redirect("admin-login")


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Pass without performing the CSRF check

class ShipmentTrackingView(APIView):

	authentication_classes = [CsrfExemptSessionAuthentication]

	def get(self, request, tracking_number):


		booking = Booking.objects.filter(tracking_number=tracking_number).first()
		if not booking:
			return JsonResponse(
				{"error": "Tracking number not found."}, status=404
			)

		booking_serializer = BookingSerializer(booking)
		return JsonResponse(booking_serializer.data, status=200)


		data = {
			"tracking_number": tracking_number,
			"status": "Out for delivery",
			"progress": 90,
			"sender": "Mile II, Benin",
			"destination": "Lugbe, Abuja",
			"estimated_arrival": "Today, 12:10 PM",
			"events": [
				{
				"title": "Parcel picked up",
				"location": "Mile II, Benin",
				"time": "Today, 10:24 AM",
				"completed": True
				},
				{
				"title": "Arrived at sorting hub",
				"location": "Benin Sorting Hub",
				"time": "Today, 11:05 AM",
				"completed": True
				},
				{
				"title": "Out for delivery",
				"location": "Lugbe, Abuja",
				"time": "Today, 11:50 AM",
				"completed": True
				},
				{
				"title": "Delivered",
				"location": "Lugbe, Abuja",
				"time": "Pending",
				"completed": False
				}
			]
		}
		return JsonResponse(data, status=200)



class GetQuoteView(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]

    SERVICE_CHARGES = {
        "Standard": 0,
        "Same-day": 50,
        "Next-day": 20,
        "Interstate": 100,
        "Business logistics": 300,
    }

    def post(self, request):
        pickup_address = request.data.get("pickup_city")
        destination_address = request.data.get("destination_city")
        service_type = request.data.get("service_type")

        try:
            weight_kg = float(request.data.get("parcel_weight", 0))
        except (TypeError, ValueError):
            return Response(
                {"error": "Parcel weight must be a number."},
                status=400,
            )

        if not pickup_address or not destination_address:
            return Response(
                {"error": "Pickup and destination addresses are required."},
                status=400,
            )

        if weight_kg <= 0:
            return Response(
                {"error": "Parcel weight must be greater than zero."},
                status=400,
            )

        if service_type not in self.SERVICE_CHARGES:
            return Response(
                {
                    "error": "Invalid service type.",
                    "allowed_service_types": list(self.SERVICE_CHARGES.keys()),
                },
                status=400,
            )

        print(
            f"Pickup: {pickup_address}, "
            f"Destination: {destination_address}, "
            f"Weight: {weight_kg} kg, "
            f"Service: {service_type}"
        )

        try:
            route = get_route_info(
                pickup_address,
                destination_address,
            )
        except RouteNotFoundError as exc:
            return Response(
                {"error": str(exc)},
                status=400,
            )
        except RouteServiceError as exc:
            return Response(
                {"error": str(exc)},
                status=503,
            )

        print(f"Route info: {route}")

        distance_km = route["distance_km"]

        base_price = 25
        price_per_km = 2
        price_per_extra_kg = 10

        extra_weight = max(0, weight_kg - 1)

        service_charge = self.SERVICE_CHARGES[service_type]

        estimated_price = (
            base_price
            + (distance_km * price_per_km)
            + (extra_weight * price_per_extra_kg)
            + service_charge
        )

        data = {
            "distance_km": distance_km,
            "estimated_delivery_time_minutes": route["duration_minutes"],
            "service_type": service_type,
            "service_charge": service_charge,
            "estimated_price": round(estimated_price, 2),
        }

        return JsonResponse(data, status=200)


class GetQuoteView2(APIView):
	def post(self, request):


		# distance_km = float(request.GET.get("distance_km", 0))
		# estimated_price = distance_km * 5.0  # Example: $5 per km

		pickup_address = request.data.get("pickup_city")
		destination_address = request.data.get("destination_city")
		weight_kg = float(request.data.get("parcel_weight", 0))
		service_type = request.data.get("service_type")

		print(f"Pickup: {pickup_address}, Destination: {destination_address}, Weight: {weight_kg} kg")
		
		try:
			route = get_route_info(
				pickup_address,
				destination_address,
			)
		except RouteNotFoundError as exc:
			return Response(
				{"error": str(exc)},
				status=400,
			)
		except RouteServiceError as exc:
			return Response(
				{"error": str(exc)},
				status=503,
			)


		print(f"Route info: {route}")

		distance_km = route["distance_km"]

		base_price = 2500
		price_per_km = 15
		price_per_extra_kg = 800

		extra_weight = max(0, weight_kg - 1)

		estimated_price = (
			base_price
			+ (distance_km * price_per_km)
			+ (extra_weight * price_per_extra_kg)
		)

		data = {
			"distance_km": distance_km,
			"estimated_delivery_time_minutes": route["duration_minutes"],
			"estimated_price": round(estimated_price, 2)
		}

		return JsonResponse(data, status=200)




class BookingView(View):
	def get(self, request):
		return render(request, "booking.html")



class CreateBookingAPIView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    BASE_PRICE = 25
    PRICE_PER_KM = 2
    PRICE_PER_EXTRA_KG = 10
    # Override the default exception handler for this class only
    def handle_exception(self, exc):
        context = self.get_exception_handler_context()
        response = custom_exception_handler(exc, context)

		
        print(f"handle_exception called with exc: {exc}, context: {context}, response: {response}")
        
        if response is not None:
            return response


    SERVICE_CHARGES = {
		"Standard": 0,
		"Same-day": 50,
		"Next-day": 20,
		"Interstate": 100,
		"Business logistics": 300,
	}

    def post(self, request):
		
        serializer = BookingCreateSerializer(data=request.data)
        print(f"Received booking data: {request.data}")


        # serializer.is_valid(raise_exception=True)
        # print(f"Validated booking data: {request.data}")

        if not serializer.is_valid():
            clean_errors = list(serializer.errors.values())[0][0] if serializer.errors else "Invalid data."
            print(f"Cleaned errors: {clean_errors}")
            return Response({"error": clean_errors}, status=status.HTTP_400_BAD_REQUEST)


        booking_data = serializer.validated_data
        print(f"Validated booking data: {booking_data}")

        try:
            route = get_route_info(
                booking_data["pickup_address"],
                booking_data["destination_address"],
            )
        except RouteNotFoundError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except RouteServiceError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

		# print("Received booking data:", request.data)  # Debugging line
		

        # Always calculate the final price on the backend.
        weight_kg = float(booking_data["weight_kg"])
        distance_km = route["distance_km"]
        service_type = booking_data["service_type"]

        extra_weight = max(0, weight_kg - 1)
        arrival_time_minutes = route["duration_minutes"]

        estimated_price = (
            self.BASE_PRICE
            + (distance_km * self.PRICE_PER_KM)
            + (extra_weight * self.PRICE_PER_EXTRA_KG)
            + self.SERVICE_CHARGES[service_type]
        )

		

        try:
            location = get_coordinates_from_location(booking_data["pickup_address"])
        except RouteNotFoundError as exc:
            return Response(
				{"error": str(exc)},
				status=status.HTTP_400_BAD_REQUEST,
			)
        except RouteServiceError as exc:
            return Response(
				{"error": str(exc)},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		
        # booking = Booking.objects.get(tracking_number="EZ-443D58B2")

        with transaction.atomic():
            booking = Booking.objects.create(
                pickup_address=booking_data["pickup_address"],
                destination_address=booking_data["destination_address"],
                sender_name=booking_data["sender_name"],
                sender_phone=booking_data["sender_phone"],
                receiver_name=booking_data["receiver_name"],
                receiver_phone=booking_data["receiver_phone"],
                parcel_description=booking_data["parcel_description"],
                weight_kg=booking_data["weight_kg"],
                service_type=service_type,
                distance_km=distance_km,
                estimated_price=estimated_price,
                arrival_time_minutes=arrival_time_minutes,
                pickup_date=booking_data["pickup_date"],
                pickup_time_window=booking_data["pickup_time_window"],
                status=Booking.BookingStatus.PENDING_PAYMENT,
                current_latitude = location["latitude"],
				current_longitude = location["longitude"],
				current_location_name = location["formatted_address"],
				location_updated_at = timezone.now()
            )


        return JsonResponse(
            {
                "id": booking.id,
                "tracking_number": booking.tracking_number,
                "status": booking.status,
                "distance_km": booking.distance_km,
                "estimated_price": booking.estimated_price,
                "estimated_delivery_time_minutes": booking.arrival_time_minutes,
                "payment_url": f"/booking/{booking.id}/payment/",
            },
            status=201,
        )


class BookingPaymentView(View):
	def get(self, request, booking_id):
		try:
			booking = Booking.objects.get(id=booking_id)
		except Booking.DoesNotExist:
			return HttpResponse("Booking not found.", status=404)

		return HttpResponse("Payment page for booking: " + booking.tracking_number)

		if booking.status != Booking.BookingStatus.PENDING_PAYMENT:
			return HttpResponse(
				"Payment has already been made or the booking is not in a payable state.",
				status=400,
			)

		# Here you would integrate with your payment gateway.
		# For demonstration, we'll just mark the booking as paid.
		booking.status = Booking.BookingStatus.PAID
		booking.save()

		return HttpResponse(
			f"Payment successful for booking {booking.tracking_number}.",
			status=200,
		)


class ContactMessageView(APIView):
	
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = serializer.validated_data["name"]
        email = serializer.validated_data["email"]
        message = serializer.validated_data["message"]

        subject = f"New contact message from {name}"

        email_body = (
            f"You have received a new contact message.\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n\n"
            f"Message:\n{message}\n"
        )

        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
        except Exception:
            return Response(
                {
                    "error": (
                        "We could not send your message right now. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return JsonResponse(
            {
                "success": True,
                "message": "Your message has been sent successfully.",
            },
            status=200,
        )


class Cordinate(LoginRequiredMixin ,View):
	login_url = "admin:login"
	redirect_field_name = "next"

	def get(self, request):
		if not request.user.is_superuser:
			return redirect("/")

		return render(request, "cord.html")


class UpdateShipmentLocationView(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        serializer = UpdateShipmentLocationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        tracking_number = serializer.validated_data["tracking_number"]
        location_name = serializer.validated_data["location_name"]

        try:
            booking = Booking.objects.get(
                tracking_number__iexact=tracking_number
            )
        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            location = get_coordinates_from_location(location_name)
        except RouteNotFoundError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except RouteServiceError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        booking.current_latitude = location["latitude"]
        booking.current_longitude = location["longitude"]
        booking.current_location_name = location["formatted_address"]
        booking.location_updated_at = timezone.now()
        booking.save(
            update_fields=[
                "current_latitude",
                "current_longitude",
                "current_location_name",
                "location_updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "tracking_number": booking.tracking_number,
                "current_location": {
                    "latitude": float(booking.current_latitude),
                    "longitude": float(booking.current_longitude),
                    "name": booking.current_location_name,
                    "updated_at": booking.location_updated_at,
                },
            },
            status=status.HTTP_200_OK,
        )