from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, resolve_url, get_object_or_404, HttpResponseRedirect
from django.utils.http import is_safe_url

import stripe
stripe.api_key = settings.STRIPE_API_KEY

from cart.custom import create_or_retrieve_cart, assign_anon_cart_to_user
from orders.custom import create_or_retrieve_order
from orders.models import Order

from .forms import UserCreationForm, ShippingAddressForm, AddPaymentForm, NewCardDefaultForm, MakeDefaultShippingForm, DeleteShippingForm, UseShippingAsBillingForm, MakeDefaultCardForm, DeleteCardForm
from .models import Customer, Profile, ShippingAddress, DefaultBilling
from .stripeutils import StripeContinuity

def create_account(request):
	"""Displays user signup form"""

	# Don't allow logged in users to acces login_view
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('profile'))

	form = UserCreationForm(request.POST or None)

	if request.POST and form.is_valid():
		form.save()
		messages.info(request, "You're signed up! Use the login form below to get started." )
		return HttpResponseRedirect(reverse('login'))
	return render(request, 'accounts/create_account.html', {
		'form': form,
	})

def login_view(request):
	"""Displays user login view. If user has had a previously anonymous
	account with a shopping cart, assigns that cart to them when logged in
	"""

	# Don't allow logged in users to acces login_view
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('profile'))

	redirect_to = request.GET.get('next' or None)

	if redirect_to is None and 'carry_over_cart' in request.session:
		redirect_to = reverse('view_cart')

	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			if not is_safe_url(url=redirect_to, host=request.get_host()):
				redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
			login(request, form.get_user())
			if 'carry_over_cart' in request.session:
				assign_anon_cart_to_user(request)
			return HttpResponseRedirect(redirect_to)
	else:
		form = AuthenticationForm(request)

	return render(request, 'registration/login.html', {
		'form': form
	})

def logged_out(request):
	"""Logs user out using provided logout function from django.contrib.auth"""

	if request.user.is_anonymous():
		return HttpResponseRedirect(reverse('home'))
		
	logout(request)
	return render(request, 'accounts/logged_out.html')

def reset_redirect(request):
	"""If user requests to change password, redirects them until
	change is processed
	"""

	return render(request, 'accounts/password_awaiting_change.html')

@login_required
def view_profile(request):
	"""Views user's account overview"""

	user = request.user
	profile = Profile.objects.get(user=user)
	cart = create_or_retrieve_cart(request)
	shipping = profile.get_default_shipping()
	payment = profile.get_default_billing()
	orders = Order.objects.filter(profile=profile, active=False).order_by('-date_completed')[:5]
	
	return render(request, 'accounts/profile.html', {
		'profile': profile,
		'shipping': shipping,
		'payment': payment,
		'orders': orders,
		'cart': cart
	})

@login_required
def view_shipping(request):
	"""
	View shipping handles 3 different functions:
	1.) User wants to specify existing shipping address as default address
	EX: elif 'default' in request.POST
	2.) User wants to delete an existing shipping address from their account
	EX: elif 'delete' in request.POST
	3.) User wants to add a new shipping address to their account
	EX: elif 'save' in request.POST
	"""

	profile = Profile.objects.get(user=request.user)
	shipping_addresses = ShippingAddress.objects.filter(user=profile)
	make_default_form = MakeDefaultShippingForm()
	delete_form = DeleteShippingForm()
	shipping_form = ShippingAddressForm()

	if request.method == 'POST':

		# Executes if user is only changing default address and not adding new one
		if 'default' in request.POST:
			make_default_form = MakeDefaultShippingForm(request.POST)
			if make_default_form.is_valid():
				address_id = make_default_form.cleaned_data['address']
				address = profile.shippingaddress_set.get(pk=address_id)
				default_shipping = profile.shippingaddress_set.filter(default_address=True).first()
				if address != default_shipping:
					default_shipping.default_address = False
					default_shipping.save()
					address.default_address = True
					address.save()
				return HttpResponseRedirect('/accounts/shipping')

		# Executes if user is deleting an address
		elif 'delete' in request.POST:
			delete_shipping = DeleteShippingForm(request.POST)
			if delete_shipping.is_valid():
				address_id = delete_shipping.cleaned_data['address']
				address = profile.shippingaddress_set.get(pk=address_id)

				# Executes if user is deleting default address. If there are other addresses
				# new default address is arbitrarily chosen
				if address.default_address:
					address.delete()
					all_addresses = profile.shippingaddress_set.filter(user=request.user)
					if all_addresses:
						all_addresses[0].default_address = True
						all_addresses[0].save()
				
				# If user's address is not default, delete without extra evaluation
				else:
					address.delete()

				return HttpResponseRedirect('/accounts/shipping/')

		# Executes if user is saving a new address to their account
		elif 'save' in request.POST:
			shipping_form = ShippingAddressForm(request.POST)
			if shipping_form.is_valid():
				cd = shipping_form.cleaned_data
				create_shipping = ShippingAddress(user=profile,
												first_name=cd['first_name'],
												last_name=cd['last_name'],
												nickname=cd['nickname'],
												address1=cd['address1'],
												address2=cd['address2'],
												city=cd['city'],
												state=cd['state'],
												country=cd['country'],
												zip_code=cd['zip_code'],
												phone_number=cd['phone_number'],
											)

				# if user wants new address to be default
				# set other addresses to not default address
				# before saving shipping address as only default address

				default_shipping_address = profile.get_default_shipping()

				if cd['default_address']:
					if default_shipping_address is not None:
						default_shipping_address.default_address = False
						default_shipping_address.save()
					create_shipping.default_address = True

				# if there are no other addresses on account,
				# always set new address to default address
				elif not cd['default_address']:
					if not default_shipping_address:
						create_shipping.default_address = True

				create_shipping.save()

	return render(request, 'accounts/shipping_address_form.html', {
			'addresses': shipping_addresses,
			'make_default_form': make_default_form,
			'delete_form': delete_form,
			'shipping_form': shipping_form,
		})

@login_required
def view_payment(request):
	"""
	View payment handles 3 different functions:
	1.) Add a new card either using default shipping address or billing address form data
	EX: if 'stripeToken' in request.POST
	2.) Specify a previously entered card as your new default card
	EX: if 'default' in request.POST
	3.) Delete a previously entered card and changes DefaultBilling if necessary
	EX: if 'delete' in request.POST

	This view stays in lock step with Stripe's API in order to extend user
	payment flexibility while mitigating API calls, which is the purpose of storing
	all information in the DefaultBilling object
	"""

	profile = Profile.objects.get(user=request.user)
	shipping_address = profile.get_default_shipping()
	default_billing = profile.get_default_billing()
	customer = stripe.Customer.retrieve(profile.stripe_id)
	delete_card_form = DeleteCardForm()
	make_default_card_form = MakeDefaultCardForm()
	add_payment_form = AddPaymentForm()
	use_shipping_as_billing_form = UseShippingAsBillingForm()
	new_card_default_form = NewCardDefaultForm()

	# Store Stripe card IDs in dict to avoid storing IDs in hidden form inputs
	card_id_dict = {}
	for idx, card in enumerate(customer.cards['data']):
		card_id_dict[idx] = card.id

	if request.method == 'POST':

		# User is deleting an existing card from account
		# Deletes using Stripe API and modifies default_billing/open orders
		if 'delete' in request.POST:
			delete_card_form = DeleteCardForm(request.POST)
			if delete_card_form.is_valid():
				card_id = card_id_dict[delete_card_form.cleaned_data['index']]
				card = customer.cards.retrieve(card_id)
				stripe_helper = StripeContinuity(customer=customer, profile=profile)
				stripe_helper.delete_card(card=card, default_billing=default_billing)
			return HttpResponseRedirect('/accounts/payment/')

		# User is specifying an existing card as their default card for all
		# future orders
		elif 'default' in request.POST:
			make_default_card_form = MakeDefaultCardForm(request.POST)
			if make_default_card_form.is_valid():
				card_id = card_id_dict[make_default_card_form.cleaned_data['index']]
				card = customer.cards.retrieve(card_id)
				stripe_helper = StripeContinuity(customer=customer, profile=profile)
				stripe_helper.make_default(card=card)
			return HttpResponseRedirect('/accounts/profile')

		# User is adding a new card to their account
		elif 'stripeToken' in request.POST:
			token = request.POST['stripeToken']
			retrieved_token = stripe.Token.retrieve(token)

			# Check if user is adding duplicate card - don't add twice if they are
			# adding a card with the same fingerprint, exp_month, and exp_year
			stripe_helper = StripeContinuity(customer=customer, profile=profile)
			duplicate = stripe_helper.check_duplicate(request=request, retrieved_token=retrieved_token)
			
			# if duplicate card is found, redirect before trying to add_card
			if duplicate:
				return HttpResponseRedirect(reverse('user_payment'))			

			# if user wants to use default shipping address as billing address
			if 'use_shipping' in request.POST:
				stripe_helper.save_card_use_shipping(request=request, token=retrieved_token, shipping=shipping_address)
				return HttpResponseRedirect(reverse('user_payment'))
			
			# if user does not indicate using default shipping address
			# use add_payment_form data to validate their inputs
			else:
				add_payment_form = AddPaymentForm(request.POST)
				if add_payment_form.is_valid():
					stripe_helper.save_card_use_form_data(request=request, token=retrieved_token, cd=add_payment_form.cleaned_data)
					return HttpResponseRedirect(reverse('user_payment'))

	return render(request, 'accounts/add_payment.html', {
		'shipping_address': shipping_address,
		'use_shipping_as_billing_form': use_shipping_as_billing_form,
		'new_card_default_form': new_card_default_form,
		'delete_card_form': delete_card_form,
		'make_default_card_form': make_default_card_form,
		'add_payment_form': add_payment_form,
		'default_card': customer.default_card,
		'cards': customer.cards['data'],
		'card_id_dict': card_id_dict
	})

@login_required
def past_order_detail(request, order_id):
	"""View order detail of a completed order"""

	order = get_object_or_404(Order, order_id=order_id, active=False)
	return render(request, 'orders/history_detail.html', {
			'order': order,
		})

@login_required
def past_order_history(request):
	"""View entire order history"""

	profile = Profile.objects.get(user=request.user)
	orders = Order.objects.filter(profile=profile, active=False).order_by('-date_completed')
	
	return render(request, 'orders/history.html', {
		'orders': orders,
	})