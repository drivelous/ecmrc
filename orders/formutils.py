from accounts.models import ShippingAddress

class OrderModify(object):
	"""Helper class to modify information that directly and indirectly affects
	open orders (EX: deleting a shipping address that was tied to an order)
	"""

	def __init__(self, profile, order, cleaned_data=None):
		self.profile = profile
		self.order = order
		
		# not every order modification requires cleaned form data
		if cleaned_data is not None:
			self.cd = cleaned_data

	def use_shipping(self):
		"""Takes UseAddressForm cleaned_data
		and uses specified address id as
		order's shipping address
		"""

		address_id = self.cd['address']
		address = self.profile.get_shipping(pk=address_id)
		self.order.shipping_address = address
		self.order.save()

	def save_shipping(self):
		"""Saves new shipping address added during order process"""

		create_shipping = ShippingAddress(user=self.profile,
										first_name=self.cd['first_name'],
										last_name=self.cd['last_name'],
										nickname=self.cd['nickname'],
										address1=self.cd['address1'],
										address2=self.cd['address2'],
										city=self.cd['city'],
										state=self.cd['state'],
										country=self.cd['country'],
										zip_code=self.cd['zip_code'],
										phone_number=self.cd['phone_number'],
									)

		default_shipping_address = self.profile.get_default_shipping()

		# if user specifies that newly saved address is default address,
		# find current default address and set default_address attr to False
		# then set default_address attr of new shipping_address to True
		if self.cd['default_address']:
			if default_shipping_address is not None:
				default_shipping_address.default_address = False
				default_shipping_address.save()

			# after evaluating previous default address, always set create_shipping to default
			create_shipping.default_address = True

		# if there is no default address, even if user does not click 'default' box,
		# still specify address as default address since it is the only one available
		elif not self.cd['default_address']:
			if default_shipping_address is None:
				create_shipping.default_address =  True

		create_shipping.save()
		self.order.shipping_address = create_shipping
		self.order.save()

	def delete_card(self, customer, card):
		"""Deletes user's card from database, open order, and Stripe account"""

		default_billing = self.profile.get_default_billing()
		
		# if all matches occur, then user is deleting their default card
		if card.last4 == default_billing.cc_four and card.exp_month == default_billing.exp_month and card.exp_year == default_billing.exp_year:
			
			# new default card is determined by number of cards in Stripe account
			# Stripe API specifies that, if a default card is deleted, the second card in
			# customer.cards['data'] becomes new default_card
			if len(customer.cards['data']) > 1:
				new_default = customer.cards['data'][1]
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
		if self.order is not None and card.last4 == self.order.cc_four and card.exp_month == self.order.exp_month and card.exp_year == self.order.exp_year:
			self.order.update_order_billing()
		
		# finally, delete card
		card.delete()

	def use_card(self, customer, card):
		"""Takes a card from Stripe account and ties it to user's open order"""
		
		self.order.update_order_billing(full_name=card.name,
										address1=card.address_line1,
										address2=card.address_line2,
										city=card.address_city,
										state=card.address_state,
										zip_code=card.address_zip,
										country=card.address_country,
										exp_month=card.exp_month,
										exp_year=card.exp_year,
										cc_four=card.last4,
										brand=card.brand)
