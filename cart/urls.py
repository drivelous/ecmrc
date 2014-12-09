from django.conf import settings
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^$', 'cart.views.view_cart', name="view_cart"),
	url(r'^add$', 'cart.views.add_to_cart'),
	url(r'^update/$', 'cart.views.update_cart', name="update_cart")
)