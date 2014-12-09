from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect
from django.contrib import messages

import stripe
stripe.api_key = settings.STRIPE_API_KEY

class StripeContinuity(object):
	"""
	Takes a Stripe Customer object and Profile model instance and ensures
	continuity of eCommerce project with Stripe's API
	"""

	def __init__(self, customer, profile):
		self.customer = customer
		self.profile = profile
		self.errors = {
			'declined': 'That card was declined. Please use a test card as specified below.',
			'duplicate': 'You have already added this card.',
		}

	def check_duplicate(self, request, retrieved_token):
		"""
		Doesn't add card to stripe if it is duplicate.
		Sets this card as default if specified
		Returns boolean
		"""
		for card in self.customer.cards['data']:
			if card['fingerprint'] == retrieved_token['card'].fingerprint and card['exp_month'] == retrieved_token['card'].exp_month and card['exp_year'] == retrieved_token['card'].exp_year:
				messages.info(request, self.errors['duplicate'])
				if 'make_default' in request.POST:
					self.make_default(card)
				return True
		return False

	def delete_card(self, card, default_billing):
		"""Deletes card in Stripe and in database. Sets new default card the same
		way stripe does"""

		# if all matches occur, then user is deleting their default card
		if card.last4 == default_billing.cc_four and card.exp_month == default_billing.exp_month and card.exp_year == default_billing.exp_year:
			
			# new default card is determined by number of cards in Stripe account
			# Stripe API specifies that, if a default card is deleted, the second card in
			# customer.cards['data'] becomes new default_card
			if len(self.customer.cards['data']) > 1:
				new_default = self.customer.cards['data'][1]
				self.profile.update_default_billing(name=new_default.name,
													address1=new_default.address_line1,
													address2=new_default.address_line2,
													city=new_default.address_city,
													state=new_default.address_state,
													zip_code=new_default.address_zip,
													country=new_default.address_country,
													cc_four=new_default.last4,
													exp_month=new_default.exp_month,
													exp_year=new_default.exp_year,
													brand=new_default.brand)
			
			# if there's only one card, since no more cards will exist after
			# this card is deleted, set default back to None for
			# each attribute
			else:
				self.profile.update_default_billing()
		
		# card being deleted is also tied to active order - reset all order billing
		# fields to None
		order = self.profile.get_order()
		if order is not None and card.last4 == order.cc_four and card.exp_month == order.exp_month and card.exp_year == order.exp_year:
			order.update_order_billing()
		
		# finally, delete card
		card.delete()

	def make_default(self, card):
		"""Saves specified card as default in Stripe and keeps this
		information stored internally
		"""
		self.customer.default_card = card.id
		self.customer.save()
		self.profile.update_default_billing(name=card.name,
											address1=card.address_line1,
											address2=card.address_line2,
											city=card.address_city,
											state=card.address_state,
											zip_code=card.address_zip,
											country=card.address_country,
											cc_four=card.last4,
											exp_month=card.exp_month,
											exp_year=card.exp_year,
											brand=card.brand)

	def save_card(self, request, token):
		try:
			card = self.customer.cards.create(card=token)
			return card
		except stripe.error.CardError:
			messages.error(request, self.errors['declined'])
			return False


	def save_card_details(self, card, name=None, address1=None, address2=None, city=None, state=None, zip_code=None, country=None):
		"""Saves payment details of new card"""

		card.name = name
		card.address_line1 = address1
		if address2:
			card.address_line2 = address2
		card.address_city = city
		card.address_state = state
		card.address_country = country
		card.address_zip = zip_code
		card.save()

	def save_card_use_shipping(self, request, token, shipping):
		"""Save billing details using shipping object"""
		# took out card from args

		card = self.save_card(request, token)

		# Only save card if card was successfully created
		if card is not False:
			self.save_card_details(card, name=shipping.first_name + ' ' + shipping.last_name,
										address1=shipping.address1,
										address2=shipping.address2,
										city=shipping.city,
										state=shipping.state,
										zip_code=shipping.zip_code,
										country=shipping.country)

			if not self.customer.default_card or 'make_default' in request.POST:
				self.customer.default_card = card.id
				self.customer.save()
				self.make_default(card=card)

			return card

	def save_card_use_form_data(self, request, token, cd):
		"""Save billing details using cleaned data from AddPaymentForm"""

		card = self.save_card(request, token)

		# Only save card if card was successfully created
		if card is not False:		
			self.save_card_details(card, name=cd['first_name'] + ' ' + cd['last_name'],
										address1=cd['address1'],
										address2=cd['address2'],
										city=cd['city'],
										state = cd['state'],
										zip_code=cd['zip_code'],
										country=cd['country'])

			if not self.customer.default_card or 'make_default' in request.POST:
				self.customer.default_card = card.id
				self.customer.save()
				self.make_default(card=card)

			return card