import collections

<<<<<<< HEAD
=======
from django.contrib import messages
>>>>>>> postgres
from django.contrib.sessions.models import Session
from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import Http404

from accounts.models import Profile
from albums.models import Album
from all_products.models import Product

from .models import Cart, CartItem

<<<<<<< HEAD

=======
>>>>>>> postgres
def retrieve_anon_cart(request):
	"""If anon user previously created cart,
	retrieve cart by their anon session id,
	which was saved in create_anon_cart
	"""

	session_key = request.session.session_key
	cart = Cart.objects.get(session=session_key)
	return cart

def create_anon_user_cart(request):
	"""If user is anon and did not previously
	create cart, save session and create cart
	tied to that session
	"""

	anon_cart_id = request.session.session_key
	cart = Cart(session=anon_cart_id)
	cart.save()
	request.session['carry_over_cart'] = True
	request.session['anon_cart_id'] = anon_cart_id
	return cart

def assign_anon_cart_to_user(request):
	"""If request.session has anon carry_over_cart
	and auth user has no cart, assign user ownership
	of carried over cart
	"""

	try:
		cart = Cart.objects.get(session=request.session['anon_cart_id'])
		if cart.user is None and request.user.is_authenticated() and request.session['carry_over_cart'] is True:
			profile = Profile.objects.get(user=request.user)
			cart.user = profile
			del request.session['carry_over_cart']
			del request.session['anon_cart_id']
			cart.save()
	except KeyError:
		print "Passing. Cart does not exist."
		raise Http404

def retrieve_auth_user_cart(request):
	"""If user is authenticated and is tied to
	cart, then retrieve that cart
	"""

	profile = Profile.objects.get(user=request.user)
	cart = Cart.objects.get(user=profile, active=True)
	return cart

def create_auth_user_cart(request):
	"""If user is authorized and has no cart tied to account,
	create cart and set authorized user as owner of cart
	"""

	cart = Cart(session=request.session.session_key)
	profile = Profile.objects.get(user=request.user)
	cart.user = profile
	cart.save()
	return cart

def create_combined_cart(request):
	"""Retrieves active carts and combines them
	into a new cart. Sets old carts inactive.
	"""

	profile = Profile.objects.get(user=request.user)
	cart_list = profile.retrieve_active_carts()
	profile.set_carts_inactive(cart_list)
	new_cart = create_auth_user_cart(request)

	for cart in cart_list:
		for cartitem in cart.get_cart_items():
			new_cartitem = new_cart.create_or_update_cart_item(request=request,
													product_pk=cartitem.product.pk,
													size=cartitem.size,
													quantity=cartitem.quantity)
	new_cart.save()
	return new_cart

def create_or_retrieve_cart(request):
	"""Creates or retrieves carts by going through all possible scenarios of
	creation for an authenticated or non-authenticated user
	"""
<<<<<<< HEAD

	if request.user.is_anonymous():
		try:
			cart = retrieve_anon_cart(request)
		except Cart.DoesNotExist:
			cart = create_anon_user_cart(request)
	elif request.user.is_authenticated():
=======
	if request.user.is_authenticated():
>>>>>>> postgres
		try:
			cart = retrieve_auth_user_cart(request)
		except Cart.DoesNotExist:
			cart = create_auth_user_cart(request)
		except MultipleObjectsReturned:
			cart = create_combined_cart(request)
<<<<<<< HEAD
=======
	elif request.user.is_anonymous():
		try:
			cart = retrieve_anon_cart(request)
		except Cart.DoesNotExist:
			cart = create_anon_user_cart(request)
>>>>>>> postgres
	return cart
