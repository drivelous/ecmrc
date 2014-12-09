from django.contrib import messages
from django.shortcuts import Http404

from .forms import ShirtQtyForm, AlbumQtyForm, DeleteItemForm, UpdateItemForm
from .models import Cart, CartItem

class CartQuery(object):
	"""Centrally handles controls adding/updating/deleting cart items"""

	def __init__(self, request, cart, cleaned_data):
		"""Updates cart using cleaned (already validated) form data
		If any error occurs, an error message is inserted into request
		"""

		self.request = request
		self.cart = cart
		self.cd = cleaned_data

	def add_to_cart(self, product_type):
		"""Add product to cart using different products forms"""

		if str(product_type) == 'Shirt':
			self.cart.create_or_update_cart_item(self.request,
												product_pk=self.cd['pk'],
												quantity=self.cd['quantity'],
												size=self.cd['size'])

			messages.info(self.request, 'You\'ve just added a shirt to your cart. To continue shopping for shirts, click', extra_tags='shop_shirts')

		elif str(product_type) == 'Album':
			self.cart.create_or_update_cart_item(self.request,
													product_pk=self.cd['pk'],
													quantity=self.cd['quantity'])

			messages.info(self.request, 'You\'ve just added an album to your cart. To continue shopping for albums,  click'	, extra_tags='shop_albums')
		
		self.cart.save()

	def delete_item(self):
		"""Deletes item from cart"""

		cartitem_pk = self.cd['cartitem']
		cartitem = self.cart.retrieve_cart_item(cartitem_pk)
		cartitem.delete()
		self.cart.save()

	def update_cart(self):
		"""Updates quantity of items in cart by checking to see which quantities 
		the user changed
		"""

		for form_row in self.cd:
			quantity = form_row['quantity']
			cartitem = self.cart.retrieve_cart_item(cartitem_pk=form_row['cartitem'])
			if cartitem.quantity != quantity:
				cartitem.update_quantity(self.request, quantity)
		self.cart.save()

