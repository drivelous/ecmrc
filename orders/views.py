from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.core.urlresolvers import reverse

import stripe
stripe.api_key = settings.STRIPE_API_KEY

from accounts.forms import ShippingAddressForm, AddPaymentForm, DeleteCardForm, UseShippingAsBillingForm, NewCardDefaultForm
from accounts.models import Profile, ShippingAddress, DefaultBilling
from accounts.stripeutils import StripeContinuity
from cart.custom import create_or_retrieve_cart

from .custom import create_or_retrieve_order
from .forms import UseAddressForm, UseCardForm, EnterEmailForm
from .models import Order
from .orderutils import OrderModify

@login_required
def choose_shipping(request):
	"""
	Choose shipping in orders app serves two functions. Allows user to:
	1.) Use a current shipping address for an order
	EX: if 'use' in request.POST
	2.) Save a new shipping address to account and use it for order
	EX: elif 'save' in request.POST
	"""

	profile = Profile.objects.get(user=request.user)
	cart = create_or_retrieve_cart(request)
	order = create_or_retrieve_order(request, cart)
	shipping_addresses = ShippingAddress.objects.filter(user=profile)
	use_address_form = UseAddressForm()
	shipping_form = ShippingAddressForm()

	if request.method == 'POST':

		if 'use' in request.POST:
			use_address_form = UseAddressForm(request.POST)
			if use_address_form.is_valid():
				order_modify = OrderModify(profile=profile, order=order, cleaned_data=use_address_form.cleaned_data)
				order_modify.use_shipping()
				return HttpResponseRedirect('/orders/checkout/')

		elif 'save' in request.POST:
			shipping_form = ShippingAddressForm(request.POST)
			if shipping_form.is_valid():
				order_modify = OrderModify(profile=profile, order=order, cleaned_data=shipping_form.cleaned_data)
				order_modify.save_shipping()
				return HttpResponseRedirect('/orders/checkout/')

	return render(request, 'orders/choose_shipping.html', {
		'use_address_form': use_address_form,
		'shipping_form': shipping_form,
		'addresses': shipping_addresses,
	})

def choose_payment(request):
	"""
	View payment handles 3 different functions:
	1.) Add a new card either using default shipping address or billing address form data
	EX: if 'stripeToken' in request.POST
	2.) Use a previously entered card for current order
	EX: if 'use' in request.POST
	3.) Delete a previously entered card and changes DefaultBilling if necessary
	EX: if 'delete' in request.POST

	This view stays in lock step with Stripe's API in order to extend user
	payment flexibility while mitigating API calls, which is the purpose of storing
	all information in the DefaultBilling object
	"""
	profile = Profile.objects.get(user=request.user)
	cart = create_or_retrieve_cart(request)
	order = create_or_retrieve_order(request, cart)
	shipping_address = profile.get_default_shipping()
	default_billing = profile.get_default_billing()
	customer = stripe.Customer.retrieve(profile.stripe_id)
	delete_card_form = DeleteCardForm()
	use_card_form = UseCardForm()
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
			return HttpResponseRedirect(reverse('order_payment'))

		# User wants to use a card for their order
		# Modifies order billing information
		elif 'use' in request.POST:
			use_card_form = UseCardForm(request.POST)
			if use_card_form.is_valid():
				card_id = card_id_dict[use_card_form.cleaned_data['index']]
				card = customer.cards.retrieve(card_id)
				order_modify = OrderModify(profile=profile, order=order)
				order_modify.use_card(card=card)
				return HttpResponseRedirect(reverse('checkout'))

		# User is adding a new card to order
		elif 'stripeToken' in request.POST:
			token = request.POST['stripeToken']
			retrieved_token = stripe.Token.retrieve(token)

			# Checks to see if card is duplicate. Won't add to Stripe if it is.
			stripe_helper = StripeContinuity(customer=customer, profile=profile)
			duplicate = stripe_helper.check_duplicate(request=request, retrieved_token=retrieved_token)
			
			# if duplicate card is found, redirect before trying to add_card
			if duplicate:
				return HttpResponseRedirect(reverse('order_payment'))

			# if user wants to use default shipping address as billing address
			elif 'use_shipping' in request.POST:
				card = stripe_helper.save_card_use_shipping(request=request, token=retrieved_token, shipping=shipping_address)

				# since user is adding card, assume they want to use it for order
				if card is not None:
					order_modify = OrderModify(profile=profile, order=order)
					order_modify.use_card(card=card)
					return HttpResponseRedirect(reverse('checkout'))

				# Card didn't save - there was an error
				else:
					return HttpResponseRedirect(reverse('order_payment'))

			# if user does not indicate to use default shipping address
			# use add_payment_form data to validate their inputs
			else:
				add_payment_form = AddPaymentForm(request.POST)
				if add_payment_form.is_valid():
					card = stripe_helper.save_card_use_form_data(request=request, token=retrieved_token, cd=add_payment_form.cleaned_data)
					
					# since user is adding card, assume they want to use it for order					
					if card is not None:
						order_modify = OrderModify(profile=profile, order=order)
						order_modify.use_card(card=card)
						return HttpResponseRedirect(reverse('checkout'))

					# Card didn't save - there was an error
					else:
						return HttpResponseRedirect(reverse('order_payment'))

	return render(request, 'orders/choose_payment.html', {
		'shipping_address': shipping_address,
		'use_shipping_as_billing_form': use_shipping_as_billing_form,
		'new_card_default_form': new_card_default_form,
		'delete_card_form': delete_card_form,
		'use_card_form': use_card_form,
		'add_payment_form': add_payment_form,
		'default_card': customer.default_card,
		'cards': customer.cards['data'],
		'card_id_dict': card_id_dict
	})

@login_required
def checkout(request):
	"""Finalizes order information before confirming purchase. Central view
	to reach all ways of modifying order account details
	"""

	profile = Profile.objects.get(user=request.user)
	cart = create_or_retrieve_cart(request)
	order = create_or_retrieve_order(request, cart)
	customer = stripe.Customer.retrieve(profile.stripe_id)
	shipping_address = order.shipping_address

	# Get default card from Stripe. If it doesn't exist, set default_card to False
	# to use in template /orders/checkout.html
	try:
		default_card = customer.cards.retrieve(customer.default_card)
	except TypeError:
		default_card = False

	# Redirect if cart is empty
	if cart.size() < 1:
		return HttpResponseRedirect(reverse('view_cart'))

	if request.method == 'POST':

		# Direct user to page for modifying order's shipping address
		if 'shipping' in request.POST:
			return HttpResponseRedirect(reverse('order_shipping'))

		# Direct user to page for modifying order's payment
		elif 'payment' in request.POST:
			return HttpResponseRedirect(reverse('order_payment'))

		# User submitted order
		elif 'finalize' in request.POST:

			email_form = EnterEmailForm(request.POST)
			if email_form.is_valid():
				order_email = email_form.cleaned_data['email']

			successful = order.finalize(request, customer, order_email)
			
			if successful:
				# All finalizing steps successful
				return HttpResponseRedirect(reverse('order_detail', args=(order.order_id, )))
			else:
				# Something went wrong - render error messages in /orders/checkout/
				return HttpResponseRedirect(reverse('checkout'))

	return render(request, 'orders/checkout.html', {
		'order': order,
		'shipping_address': shipping_address,
		'cart': cart,
		'default_card': default_card,
		})