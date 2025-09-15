from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout

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