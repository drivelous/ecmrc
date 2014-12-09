import os
from django.db import models
from django.template.defaultfilters import slugify

from .queryutil import ShirtQuery

class ProductType(models.Model):
	product_type = models.CharField(max_length=50)

	def get_parents(self):
		"""Get parents (artists for albums, brands for shirts)
		particular product type"""

		if str(self) == 'Shirt':
			# Avoids circular import
			from shirts.models import Brand
			return Brand.objects.all()[:5]
		elif str(self) == 'Album':
			# Avoids circular import
			from albums.models import Artist
			return Artist.objects.all()[:5]

	def __str__(self):
		return str(self.product_type)


class Product(models.Model):
	"""Master Product model that contains universal product information
	Product details unique to product types link into this model
	"""

	name = models.CharField(max_length=250, default='')
	product_type = models.ForeignKey(ProductType, default='')
	description = models.TextField(default='About this product', null=False, blank=False)
	short_desc = models.CharField(max_length=250, default='Shortened product description', null=False, blank=False)
	active = models.BooleanField(default=False)
	slug = models.SlugField(null=True, blank=True)
	added = models.DateTimeField(auto_now=True, auto_now_add=False)
	updated = models.DateTimeField(auto_now=False, auto_now_add=True)

	def save(self,size=None, *args, **kwargs):
		"""Takes name of product and turns it into slug"""

		if not self.slug:
			self.slug = slugify(self.name)

		super(Product, self).save(*args, **kwargs)

	def get_price(self, size=None):
		"""Retrieve current price of product
		Does not indicate if sale or original price
		"""

		if str(self.product_type) == 'Album':
			album = self.album_set.all()[0]
			if album.sale_price is None:
				return album.original_price
			return album.sale_price
		elif str(self.product_type) == 'Shirt':
			shirt_query = ShirtQuery(self)
			price = shirt_query.get_price(size)
			return price

	def get_original_price(self, size=None):
		"""Retrieve original price of product"""

		if str(self.product_type) == 'Album':
			return self.album_set.all()[0].original_price
		elif str(self.product_type) == 'Shirt':
			shirt_query = ShirtQuery(self)
			return shirt_query.get_original_price(size)

	def get_slug(self):
		"""Returns Product slug for use in Product URLs/filtering"""

		return self.slug

	def get_style(self):
		"""Gets shirt style object. Only for use on shirts"""

		try:
			pattern = self.shirtstyle_set.all()[0]
			return pattern
		except IndexError:
			print "QueryError: Query is reserved for shirts only."

	def get_album(self):
		"""Gets album model instance. Only for use on music albums"""

		try:
			album = self.album_set.all()[0]
			return album
		except IndexError:
			print "QueryError: No matching album. Is the product object an album?"

	def get_images(self):
		"""Gets all product's images"""

		return [image.image for image in self.productimage_set.all()]

	def get_default_image(self):
		"""Get product's default image"""
		try:
			image = self.productimage_set.all()[0].image
			return image
		except IndexError:
			print "ImageError: No default image"

	def get_style_name(self):
		"""Gets style name. Only for use on shirts"""

		try:
			pattern = self.shirtstyle_set.all()[0].pattern
			return pattern
		except IndexError:
			print "QueryError: Query is reserved for shirts only."

	def get_artist(self):
		"""Gets artist name. Only for use on albums"""

		try:
			artist = self.album_set.all()[0].artists.all()[0]
			return artist
		except:
			print "QueryError: Query is reserved for albums only."

	def get_parent(self):
		"""Returns parent of product EX: artist of an album or company of shirt"""

		if str(self.product_type) == 'Album':
			album = self.album_set.all()[0]
			return album.artists.all()[0]
		elif str(self.product_type) == 'Shirt':
			shirt_query = ShirtQuery(self)
			brand = shirt_query.get_brand()
			return brand

	def get_parent_slug(self):
		"""Returns slug of parent of product.
		Used for hyperlinking product parent URLs
		"""

		if str(self.product_type) == 'Album':
			album = self.album_set.all()[0]
			return album.artists.all()[0].slug
		elif str(self.product_type) == 'Shirt':
			shirt_query = ShirtQuery(self)
			brand_slug = shirt_query.get_brand_slug()
			return brand_slug

	def is_sale(self, size=None):
		"""Returns boolean specifying if product
		is on sale
		"""

		if str(self.product_type) == 'Album':
			album = self.album_set.all()[0]
			if album.sale_price is not None:
				return True
			return False
		elif str(self.product_type) == 'Shirt':
			shirt_query = ShirtQuery(self)
			is_sale = shirt_query.is_sale(size)
			return is_sale

	def get_stock(self, size=None):
		"""Returns current stock for product
		"""
		if str(self.product_type) == 'Album':
			album = self.album_set.all()[0]
			return album.stock
		elif str(self.product_type) == 'Shirt':
			shirt_query = ShirtQuery(self)
			stock = shirt_query.get_stock(size)
			return stock

	# This function should ONLY be called by InventoryControl
	# and NEVER called directly to prevent inventory issues
	def decrement_stock(self, quantity, size=None):
		"""Reduces stock of product
		by quantity specified
		Always called by InventoryControl
		"""
		stock = self.get_stock(size)
		new_stock = stock - quantity

		if str(self.product_type) == 'Album':
			album = self.album_set.all()[0]
			album.stock = new_stock
			if new_stock == 0:
				self.active = False
				self.save()
			album.save()
		elif str(self.product_type) == 'Shirt':
			shirt_query = ShirtQuery(self)
			shirt_query.decrement_stock(new_stock, size)
			if not shirt_query.stock_exists():
				self.active = False
				self.save()

	def __str__(self):
		if str(self.product_type) == 'Album':
			return str(self.name) + ' ' + 'by ' + str(self.get_artist())
		elif str(self.product_type) == 'Shirt':
			return str(self.get_parent()) + ' - ' + str(self.name) + ' - ' + str(self.get_style_name())

class ProductImage(models.Model):

	def get_upload_path(instance, filename):
		return os.path.join(
			'product_images', "%s" % instance.product.slug, filename
		)

	image = models.ImageField(default='default/noimage.jpg', upload_to=get_upload_path)
	slug = models.SlugField(null=True, blank=True)
	description = models.CharField(max_length=500, null=True, blank=True)
	product = models.ForeignKey(Product)
	default = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		"""If image hasn't been saved,
		generates a slug based on image name
		"""
		
		if not self.id:
			self.slug = slugify(self.image)

		super(ProductImage, self).save(*args, **kwargs)

	def __unicode__(self):
		return str(self.product) + "   ---   " + str(self.default)