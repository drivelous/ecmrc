from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.http import Http404

from all_products.models import Product, ProductType
from all_products.queryutil import InventoryControl

class Cart(models.Model):
	user = models.ForeignKey('accounts.Profile', null=True, blank=True)
	session = models.CharField(max_length=200, default='', null=True, blank=True)
	total = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		"""Saves items in cart and re-calculates total each time"""

		self.calculate_cart()
		
		super(Cart, self).save(*args, **kwargs)

	def get_cart_items(self):
		"""Returns list of all cart's cartitems"""

		return self.cartitem_set.all()

	def size(self):
		"""Returns number of items in cart"""

		return len(self.get_cart_items())

	def calculate_cart(self):
		"""Calculates all cart contents"""

		total = 0
		cart_items = self.get_cart_items()
		for item in cart_items:
			total += (item.quantity * item.price)
		self.total = total

	def create_or_update_cart_item(self, request, product_pk, size=None, quantity=None):
		"""Returns specific item in cart or else creates cartitem
		Used when it's unknown whether cartitem yet exists (add_to_cart)
		"""

		try:
			product = Product.objects.get(pk=product_pk)
			product_inventory = InventoryControl(product)
		except Product.DoesNotExist:
			raise Http404

		cartitem, created = CartItem.objects.get_or_create(cart=self,
															product=product,
															product_type=product.product_type,
															size=size,
															name=product.name)
		
		# if cartitem is just created, use cartitem's product methods to
		# finish creating cartitem
		if created:
			price = product.get_price(size)
			clean_quantity, changed = product_inventory.clean_quantity(request, quantity, size)
			cartitem.price = price
			cartitem.quantity = clean_quantity
			cartitem.total = price * clean_quantity
			cartitem.save()
			self.save()
		
		# if cartitem already existed, then add user specified
		# quantity to update quantity
		elif not created:
			new_quantity = cartitem.quantity + quantity
			cartitem.update_quantity(request, new_quantity)

		return cartitem

	def retrieve_cart_item(self, cartitem_pk):
		"""Retrieves item from cart"""

		try:
			cartitem = CartItem.objects.get(cart=self, pk=cartitem_pk)
		except CartItem.DoesNotExist:
			raise Http404
		return cartitem

	def confirm_stock(self, request):
		"""Confirms each product in user's cart is available
		at desired quantity. If changes occur, message is displayed.
		Else, returns True
		"""

		cartitems = self.get_cart_items()

		stock_changed = False
		for cartitem in cartitems:
			inventory_control = InventoryControl(cartitem.product)
			clean_quantity, changed = inventory_control.clean_quantity(request=request, quantity=cartitem.quantity, size=cartitem.size)
			if changed:
				cartitem.quantity = clean_quantity
				cartitem.save()
				stock_changed = True

		# Boolean aborts or continues process which called the method
		if stock_changed:
			return False
		return True

	def finalize_cart(self, request):
		"""
		1.) Confirms cart stock
		2.) Decrements items from database
		3.) Sets cart inactive
		"""
		available = self.confirm_stock(request)

		if available:
			cartitems = self.get_cart_items()
			for cartitem in cartitems:
				inventory_control = InventoryControl(cartitem.product)
				inventory_control.decrement_stock(quantity=cartitem.quantity, size=cartitem.size)
			self.active = False
			self.save()
			return True

		# Some stock is not available - aborts process which called it	
		else:
			return False

	def __unicode__(self):
		return str(self.id)

class CartItem(models.Model):
	cart = models.ForeignKey(Cart)
	product = models.ForeignKey(Product)
	product_type = models.ForeignKey(ProductType)
	name = models.CharField(max_length=80, null=True)
	total = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
	price = models.DecimalField(default=9.99, max_digits=10, decimal_places=2)
	quantity = models.IntegerField(default=0)
	size = models.CharField(max_length=30, null=True, blank=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		"""Creates name attribute if none exists.
		Calculates new total on every save
		"""

		if not self.name:
			self.name = self.product.name

		self.calculate_total()

		super(CartItem, self).save(*args, **kwargs)

	def get_price(self):
		"""Gets current price
		using product's get_price method
		"""

		product = self.product
		return product.get_price(size=self.size)

	def is_sale(self):
		"""Returns boolean if product is on sale"""

		product = self.product
		return product.is_sale(size=self.size)

	def get_stock(self):
		"""Checks current stock of cartitem's product"""

		return self.product.get_stock(size=self.size)

	def calculate_total(self):
		"""Calculates cartitem total. Called during every save"""
		
		self.total = self.get_quantity() * self.get_price()

	def get_quantity(self):
		"""Returns cart's quantity of current cartitem"""

		return self.quantity

	def update_quantity(self, request, quantity):
		"""Checks inventory if new quantity is valid
		If not, sets to closest possible quantity and displays a message
		"""
		
		product_inventory = InventoryControl(self.product)
		clean_quantity, changed = product_inventory.clean_quantity(request, quantity, self.size)
		self.quantity = clean_quantity
		self.save()

	def __str__(self):
		return "Cart #" + str(self.cart.pk) + " - " + str(self.product)