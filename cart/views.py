from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, Http404
from django.template.response import TemplateResponse

from accounts.models import Profile
from albums.models import Album
from orders.custom import create_or_retrieve_order
from all_products.models import Product, ProductType

from .custom import create_or_retrieve_cart
from .forms import ShirtQtyForm, AlbumQtyForm, DeleteItemForm, UpdateItemForm
from .formutils import CartQuery
from .models import Cart, CartItem

import stripe
stripe.api_key = settings.STRIPE_API_KEY

def view_cart(request):
	"""View contents of current, active shopping cart"""

	cart = create_or_retrieve_cart(request)
	delete_form = DeleteItemForm()
	number_items = cart.size()
	CartItemSet = formset_factory(UpdateItemForm, extra=number_items)

	return render(request, 'cart/cart.html', {
		'cart': cart,
		'delete_form': delete_form,
		'CartItemSet': CartItemSet,
	})

def add_to_cart(request):
	"""Adds specified product to cart. If user is anonymous, saves that
	cart to an anonymous session and is still accessible without an account
	"""

	if request.method == 'POST':
		s = request.session
		s.save()
		view_name = request.resolver_match.url_name

		cart = create_or_retrieve_cart(request)
		form, product_type = bind_correct_form(request.POST)
		if form.is_valid():
			cart_query = CartQuery(request=request, cart=cart, cleaned_data=form.cleaned_data)
			cart_query.add_to_cart(product_type)
		else:
			raise Http404

		return HttpResponseRedirect(reverse('view_cart'))

def update_cart(request):
	"""Updates quantity of all items in cart that have changed"""

	cart = create_or_retrieve_cart(request)
	number_items = cart.size()
	CartItemSet = formset_factory(UpdateItemForm, extra=number_items)

	if request.method == 'POST':

		# Executes if user is deleting an item from cart
		if 'delete' in request.POST:
			delete_form = DeleteItemForm(request.POST)
			if delete_form.is_valid():
				cart_query = CartQuery(request=request, cart=cart, cleaned_data=delete_form.cleaned_data)
				cart_query.delete_item()

		# Executes if user clicks 'update cart'
		# Goes item by item in cart and checks to see which quantities user updated
		elif 'update' in request.POST:
			cartitemset = CartItemSet(request.POST)
			if cartitemset.is_valid():
				cart_query = CartQuery(request=request, cart=cart, cleaned_data=cartitemset.cleaned_data)
				cart_query.update_cart()
	
	return HttpResponseRedirect(reverse('view_cart'))