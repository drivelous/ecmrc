from django.conf import settings
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^shipping/$', 'orders.views.choose_shipping', name="order_shipping"),
	url(r'^payment/$', 'orders.views.choose_payment', name="order_payment"),
	url(r'^checkout/$', 'orders.views.checkout', name="checkout"),
)