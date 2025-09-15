from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from .models import Order, TransPerson, Parcel, CurrentLocation, Address
import random, string

# Create your views here.
class OrderNow(View):
	def get(self, request):
		return render(request, "shipping/order_now.html")
	
	def post(self, request):
		print(request.POST)
		sender_name = request.POST.get("sendername")
		sender_number = request.POST.get("sendernumber")
		reciever_name = request.POST.get("recievername")
		reciever_number = request.POST.get("recievernumber")

		parcel_name = request.POST.get("parcelname")
		parcel_description = request.POST.get("parceldescription")
		parcel_weight = request.POST.get("parcelweight")
		parcel_length = request.POST.get("parcellength")
		parcel_width = request.POST.get("parcelwidth")
		parcel_height = request.POST.get("parcelheight")
		parcel_quantity = request.POST.get("parcelquantity")

		p_street_address = request.POST.get("pstreetaddress")
		p_apartment_address = request.POST.get("papartaddress")
		p_country = request.POST.get("pcountry")
		p_zipcode = request.POST.get("pzipcode")

		d_street_address = request.POST.get("dstreetaddress")
		d_apartment_address = request.POST.get("dapartaddress")
		d_country = request.POST.get("dcountry")
		d_zipcode = request.POST.get("dzipcode")

		price = request.POST.get("amount")
		delivery_date = request.POST.get("date")


		sender_dict = {
			"name": sender_name,
			"phone_number": sender_number
		}
		reciever_dict = {
			"name": reciever_name,
			"phone_number": reciever_number
		}
		pickup_dict = {
			"street_address": p_street_address,
			"apartment_address": p_apartment_address,
			"country": p_country,
			"zip": p_zipcode
		}
		delivery_dict = {
			"street_address": d_street_address,
			"apartment_address": d_apartment_address,
			"country": d_country,
			"zip": d_zipcode
		}
		sender_obj = TransPerson.objects.create(**sender_dict)
		reciever_obj = TransPerson.objects.create(**reciever_dict)
		pickup_obj = Address.objects.create(**pickup_dict)
		delivery_obj = Address.objects.create(**delivery_dict)

		# status = models.CharField(max_length=2, default="PR", choices=STATUS_CHOICES)
		# tracking_number = models.CharField(max_length=10, blank=True, null=True)
		# sender = models.ForeignKey("TransPerson", blank=True, null=True, on_delete=models.SET_NULL, related_name="sorder")
		# reciever = models.ForeignKey("TransPerson", blank=True, null=True, on_delete=models.SET_NULL, related_name="rorder")
		# price = models.DecimalField(max_digits= 20, decimal_places=2)
		# delivery_address = models.ForeignKey("Address", blank=True, null=True, on_delete=models.SET_NULL, related_name="dorder")
		# pickup_address = models.ForeignKey("Address", blank=True, null=True, on_delete=models.SET_NULL, related_name="porder")
		# shipment_date = models.DateTimeField(default=datetime.now())
		# delivery_date = models.DateTimeField(blank=True, null=True)

		tracking_number = "".join(random.choices(string.digits, k=10))
		order = Order()
		order.tracking_number = tracking_number
		order.sender = sender_obj
		order.reciever = reciever_obj
		order.pickup_address = pickup_obj
		order.delivery_address = delivery_obj
		order.price = price
		order.delivery_date = delivery_date

		order.save()

		parcel = Parcel()
		parcel.name = parcel_name
		parcel.description = parcel_description
		parcel.weight = parcel_weight
		parcel.length = parcel_length
		parcel.width = parcel_width
		parcel.height = parcel_height
		parcel.quantity = parcel_quantity
		parcel.order = order

		parcel.save()
		return redirect("shipping:payment")
	

class Payment(View):
	def get(self, request):
		return render(request, "shipping/payment.html")
	
	def post(self, request):
		print(request.POST)
		return redirect("shipping:payment")

class Track(View):
	def get(self, request):
		return render(request, "courier/tracking.html")
	
	def post(self, request):
		tracking_number = request.POST.get("tracking-number")
		print(f"The tracking number is {tracking_number}")
		order_qs = Order.objects.filter(tracking_number=tracking_number)
		if order_qs.exists():
			order = order_qs.first()
			# print(order.current_location.last())
			return render(request, "courier/tracking.html", {"order": order})
		else:
			return render(request, "courier/tracking.html", {"order": "not valid"})
