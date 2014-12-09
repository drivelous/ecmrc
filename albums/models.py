import os
from django.db import models
from django.template.defaultfilters import slugify

from all_products.models import Product, ProductType

class Artist(models.Model):
	"""Model for music artists"""

	def get_upload_path(instance, filename):
		return os.path.join(
			'artists', "%s" % instance.slug, filename
		)
	
	name = models.CharField(max_length=100, null=False, blank=False)
	bio = models.TextField(default='Bio goes here', null=False, blank=False)
	profile = models.ImageField(default='artists/default.png', upload_to=get_upload_path)
	slug = models.SlugField(null=True, blank=True)
	added = models.DateTimeField(auto_now=True, auto_now_add=False)
	updated = models.DateTimeField(auto_now=False, auto_now_add=True)

	def save(self, *args, **kwargs):
		""" Automatically create slug when object is saved"""

		if not self.id:
			self.slug = slugify(self.name)

		super(Artist, self).save(*args, **kwargs)

	def get_slug(self):
		"""Getter for Artist slug"""
		
		return self.slug

	def get_albums(self):
		"""Retrieve all album Product objects by an artist"""

		albums = self.album_set.all()
		return [album.product_id for album in albums]

	def __unicode__(self):
		return self.name

	class Meta:
		ordering = ('name',)

class AlbumManager(models.Manager):
	def get_queryset(self):
		return super(AlbumManager, self).get_queryset().order_by('artists')

class Album(models.Model):
	"""Model for music albums. Generic product details in all_products.models
	but album details stored in this model
	"""

	product_id = models.ForeignKey(Product, null=True, blank=True)
	product_type = models.ForeignKey(ProductType)
	name = models.CharField(max_length=150, null=False, blank=False)
	artists = models.ManyToManyField(Artist)
	release_date = models.DateField(null=True, blank=True)
	stock = models.PositiveSmallIntegerField(default=0)
	original_price = models.DecimalField(max_digits=8, decimal_places=2, default=1999, null=False, blank=False)
	sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	objects = AlbumManager()

	def save(self, *args, **kwargs):
		"""Create entry in Product model to save product_id"""

		if not self.pk:
			create_product = Product(
									name=str(self.name),
									product_type=self.product_type,
									description="This is an album",
								)
			create_product.save()

			self.product_id = create_product

		super(Album, self).save(*args, **kwargs)

	def get_tracks(self):
		return self.track_set.all().order_by('track_no')

	def __unicode__(self):
		return str(self.artists.all()[0]) + ' - ' + str(self.name)

class TrackManager(models.Manager):
	def get_queryset(self):
		return super(TrackManager, self).get_queryset().order_by('artists')

class Track(models.Model):
	"""Model for tracks that are a part of a music album"""

	name = models.CharField(max_length=200, null=False, blank=False)
	album = models.ForeignKey(Album)
	track_no = models.PositiveSmallIntegerField(null=True, blank=True)
	minutes = models.PositiveSmallIntegerField(null=True, blank=True)
	seconds = models.PositiveSmallIntegerField(null=True, blank=True)

	def __unicode__(self):
		return str(self.album) + ' ' + str(self.track_no) + ' ' + str(self.name)
