import os
from django.db import models
from django.template.defaultfilters import slugify

from all_products.models import Product, ProductType

class Brand(models.Model):
	"""Name of clothing brand that makes shirts"""

	def get_upload_path(instance, filename):
		return os.path.join(
			"%s" % instance.slug, filename
		)
	name = models.CharField(max_length=100, null=False, blank=False)
	about = models.TextField(default='Brand details go here', null=False, blank=False)
	profile = models.ImageField(default='artists/default.png', upload_to=get_upload_path)
	slug = models.SlugField(null=True, blank=True)
	added = models.DateTimeField(auto_now=True, auto_now_add=False)
	updated = models.DateTimeField(auto_now=False, auto_now_add=True)

	def save(self, *args, **kwargs):
		""" Automatically create slug when object is saved"""

		if not self.id:
			self.slug = slugify(self.name)

		super(Brand, self).save(*args, **kwargs)

	def get_shirts(self):
		"""Returns all shirt Product objects by brand instance"""

		return Product.objects.filter(shirtstyle__shirt__brand__name=self.name)

	def get_active_shirts(self):
		"""Returns all non-sold out shirts by brand instance"""

		return Product.objects.filter(active=True).filter(shirtstyle__shirt__brand__name=self.name)

	def get_slug(self):
		return self.slug

	def __unicode__(self):
		return self.name

	class Meta:
		ordering = ('name',)

class Shirt(models.Model):
	"""Parent shirt model for related ShirtStyle objects"""

	product_type = models.ForeignKey(ProductType)
	brand = models.ForeignKey(Brand)
	name = models.CharField(max_length=150, null=False, blank=False)
	description = models.TextField(default='This shirt is tight', null=False, blank=False)

	def get_styles(self):
		"""Gets all styles/color patterns of a shirt instance"""

		return self.shirtstyle_set.all()

	def get_brand(self):
		"""Gets brand of shirt"""

		return self.brand

	def get_brand_slug(self):
		"""Gets brand slug to link to brand's URL"""

		return self.brand.slug

	def __unicode__(self):
		return self.name

	class Meta:
		ordering = ('name',)

class ShirtStyle(models.Model):
	shirt = models.ForeignKey(Shirt)
	product_id = models.ForeignKey(Product, null=True, blank=True)
	pattern = models.CharField(max_length=50, null=False, blank=False)
	primary = models.BooleanField(default=False)
	xs_stock = models.IntegerField(default=0)
	xs_original_price = models.DecimalField(max_digits=8, decimal_places=2, default=19.99, blank=False, null=False)
	xs_sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	s_stock = models.IntegerField(default=0)
	s_original_price = models.DecimalField(max_digits=8, decimal_places=2, default=19.99, blank=False, null=False)
	s_sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	m_stock = models.IntegerField(default=0)
	m_original_price = models.DecimalField(max_digits=8, decimal_places=2, default=19.99, blank=False, null=False)
	m_sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	l_stock = models.IntegerField(default=0)
	l_original_price = models.DecimalField(max_digits=8, decimal_places=2, default=19.99, blank=False, null=False)
	l_sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	xl_stock = models.IntegerField(default=0)
	xl_original_price = models.DecimalField(max_digits=8, decimal_places=2, default=19.99, blank=False, null=False)
	xl_sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

	def save(self, *args, **kwargs):
		""" Create entry in Product model to save product_id"""

		if not self.pk:
			create_product = Product(
									name=str(self.shirt.name),
									product_type=self.shirt.product_type,
									description=self.shirt.description,
									slug=slugify(str(self.shirt.brand) + ' ' + str(self.shirt.name) + ' - ' + str(self.pattern))
								)
			create_product.save()

			self.product_id = create_product

		super(ShirtStyle, self).save(*args, **kwargs)

	def get_other_styles(self):
		"""Gets sibling ShirtStyle objects (same Shirt parent object)"""

		return self.shirt.shirtstyle_set.all()

	def get_active_styles(self):
		"""Gets sibling ShirtStyle objects that are still in stock"""

		return self.shirt.shirtstyle_set.filter(product_id__active=True)

	def get_product(self):
		"""Retrieves ShirtStyle instance's Product instance"""

		return self.product_id

	def __unicode__(self):
		return str(self.shirt) + ' - ' + str(self.pattern)
