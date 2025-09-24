from django.urls import path
from .views import OrderNow, Payment, Track, Condition, Delivery

app_name = "courier"

urlpatterns = [
	path("order-now", OrderNow.as_view(), name="order-now"),
	path("payment", Payment.as_view(), name="payment"),
	path("track", Track.as_view(), name="track"),
	path("condition", Condition.as_view(), name="condition"),
	path("delivery", Delivery.as_view(), name="delivery"),
] 