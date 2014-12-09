from django.contrib import messages

class ShirtQuery(object):
	"""Minimizes overhead from complicated queries"""

	def __init__(self, product):
		self.shirt = product.shirtstyle_set.all()[0]
		
		self.shirt_stock = {'XS': 'xs_stock',
						'S': 's_stock',
						'M': 'm_stock',
						'L': 'l_stock',
						'XL': 'xl_stock'}
		
		self.shirt_original_price = {'XS': 'xs_original_price',
									'S': 's_original_price',
									'M': 'm_original_price',
									'L': 'l_original_price',
									'XL': 'xl_original_price'}
		
		self.shirt_sale_price = {'XS': 'xs_sale_price',
								'S': 's_sale_price',
								'M': 'm_sale_price',
								'L': 'l_sale_price',
								'XL': 'xl_sale_price'}

		self.sizes = ['XS', 'S', 'M', 'L', 'XL']

	def get_price(self, size):
		"""Returns sale price if it exists. Else, returns original_price"""

		try:
			sale_price = getattr(self.shirt, self.shirt_sale_price[size])
			original_price = getattr(self.shirt, self.shirt_original_price[size])
			if sale_price is None:
				return original_price
			return sale_price
		except KeyError as e:
			print "{0} is not a valid size.".format(e)

	def get_original_price(self, size):
		"""Return original price of shirt"""
		try:
			return getattr(self.shirt, self.shirt_original_price[size])
		except KeyError as e:
			print "{0} is not a valid size.".format(e)

	def get_brand(self):
		"""Returns brand (maker) of shirt"""

		return self.shirt.shirt.brand

	def get_brand_slug(self):
		"""Returns brand slug for use in URL to call brand_detail view"""

		return self.shirt.shirt.brand.slug

	def is_sale(self, size):
		"""Returns boolean for if there's a sale_price"""

		try:
			sale_price = getattr(self.shirt, self.shirt_sale_price[size])
			if sale_price is not None:
				return True
			return False
		except KeyError as e:
			print "{0} is not a valid size.".format(e)

	def get_stock(self, size):
		"""Returns stock for particular shirt of particular size"""
		try:
			stock = getattr(self.shirt, self.shirt_stock[size])
			return stock
		except KeyError as e:
			print "{0} is not a valid size.".format(e)

	def all_available(self):
		"""Returns total qty of all items available in all sizes"""

		available = 0
		for size in self.sizes:
			available += getattr(self.shirt, self.shirt_stock[size])
		return available

	def sizes_available(self):
		"""Returns all sizes with stock > 0 """

		sizes = []
		for size in self.sizes:
			if self.get_stock(size) > 0:
				sizes.append(size)
		return sizes


	def decrement_stock(self, new_stock, size):
		"""Decrements stock for shirt of particular size
		Should be called exclusively by InventoryControl
		to avoid inventory issues"""

		try:
			setattr(self.shirt, self.shirt_stock[size], new_stock)
			self.shirt.save()
		except KeyError as e:
			print "{0} is not a valid size.".format(e)

	def stock_exists(self):
		"""Checks if shirt stock is empty. If so, sets product inactive
		Should be called exclusively by InventoryControl to avoid inventory issues
		"""

		for size in self.sizes:
			if getattr(self.shirt, self.shirt_stock[size]) > 0:
				return True
		return False



class InventoryControl(object):
	"""Central control for inventory checks to avoid inventory issues"""

	def __init__(self, product):
		self.product = product
		self.messages_dict = {
			'set_zero': 'Cannot set {0} quantity to 0. If you would like to remove the item, click the \'Remove\' button next to item.'.format(product),
			'exceeds_available': 'Quantity for item {0} exceeded stock available. Current cart quantity reflects maximum available.'.format(product),
			'limit_15': 'To prevent a single customer from cleaning the site out, every item is limited to a maximum of 15.'
		}

	def clean_quantity(self, request, quantity, size):
		"""Disallows illegal product quantities when adding/updating shopping cart"""

		changed = False
		stock = self.product.get_stock(size)
		limit_15 = 15

		if quantity > limit_15:
			quantity = limit_15
			changed = True
			messages.info(request, self.messages_dict['limit_15'])
		elif quantity > stock:
			quantity = stock
			changed = True
			messages.info(request, self.messages_dict['exceeds_available'])
		elif quantity <= 0:
			quantity = 1
			changed = True
			messages.info(request, self.messages_dict['set_zero'])
		return quantity, changed

	def decrement_stock(self, quantity, size):
		self.product.decrement_stock(quantity, size)