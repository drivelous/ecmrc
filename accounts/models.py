from django.conf import settings
from django.contrib.auth.models import (
	BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.db import models
from localflavor.us.models import PhoneNumberField, USPostalCodeField, USStateField

from cart.models import Cart

class CustomerManager(BaseUserManager):
	"""
	Default user model for project is custom 'Customer',
	not default user
	"""
	def create_user(self, username, email, password=None):
		if not email:
			raise ValueError('users must have an email address')

		user = self.model(
			username=username,
			email=CustomerManager.normalize_email(email),
		)

		user.set_password(password)
		user.save(using=self._db)

		return user

	def create_superuser(self, username, email, password):
		user = self.create_user(
			username=username,
			email=email,
			password=password,
		)

		user.is_superuser = True
		user.is_admin = True
		user.is_staff = True
		user.save(using=self._db)
		return user

class Customer(AbstractBaseUser, PermissionsMixin):
	"""Custom user model"""

	username = models.CharField(max_length=40, unique=True, db_index=True)
	email = models.EmailField(max_length=254)

	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = ['email',]

	is_active = models.BooleanField(default=True)
	is_admin = models.BooleanField(default=False)
	is_staff = models.BooleanField(default=False)

	objects = CustomerManager()

	def get_full_name(self):
		return "{0} | {1}".format(self.username, self.email)

	def get_short_name(self):
		return self.username

class Profile(models.Model):
	"""
	Profile model stores user information unique to this project such as
	order history, carts, stripe accounts, and account information
	"""
	user = models.ForeignKey(Customer)
	stripe_id = models.CharField(max_length=300, null=True, blank=True)
	timestamp = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now_add=False, auto_now=True)

	def retrieve_active_carts(self):
		cart_list = Cart.objects.filter(user=self, active=True)
		return cart_list

	def set_carts_inactive(self, cart_list):
		for cart in cart_list:
			cart.active = False
			cart.save()

	def get_shipping(self, pk):
		return self.shippingaddress_set.get(pk=pk)

	def get_default_shipping(self):
		return self.shippingaddress_set.filter(default_address=True).first()

	def get_default_billing(self):
		return self.defaultbilling_set.get(user=self)

	def update_default_billing(self, name=None, address1=None, address2=None, city=None, state=None, zip_code=None, country=None, cc_four=None, exp_month=None, exp_year=None, brand=None):
		default_billing = self.get_default_billing()
		default_billing.full_name = name
		default_billing.billing_address1 = address1
		default_billing.billing_address2 = address2
		default_billing.billing_city = city
		default_billing.billing_state = state
		default_billing.billing_country = country
		default_billing.billing_zip = zip_code
		default_billing.cc_four = cc_four
		default_billing.exp_month = exp_month
		default_billing.exp_year = exp_year
		default_billing.brand = brand
		default_billing.save()

	def get_order(self):
		return self.order_set.filter(active=True).first()

	def get_order_history(self):
		return self.order_set.filter(active=False)

	def __str__(self):
		return str(self.user)

class ShippingAddress(models.Model):
	user = models.ForeignKey(Profile)
	first_name = models.CharField(max_length=50, default='', blank=False)
	last_name = models.CharField(max_length=80, default='', blank=False)
	nickname = models.CharField(max_length=50, null=True, blank=True)
	address1 = models.CharField(max_length=100)
	address2 = models.CharField(max_length=100, null=True, blank=True)
	city = models.CharField(max_length=50)
	state = USStateField()
	country = models.CharField(max_length=50)
	zip_code = models.CharField(max_length=16, default='', null=False, blank=False)
	phone_number = PhoneNumberField(null=True, blank=True)
	timestamp = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now_add=False, auto_now=True)
	default_address = models.BooleanField(default=False)

	def __unicode__(self, ):
		return self.address1

class DefaultBilling(models.Model):
	"""Displays current defeault card info from Stripe to avoid
	repeatedly hitting the API to display non-changing information
	"""
	
	user = models.ForeignKey(Profile)
	stripe_id = models.CharField(max_length=300, null=True, blank=True)
	full_name = models.CharField(max_length=100, null=True) 
	billing_address1 = models.CharField(max_length=100, null=True)
	billing_address2 = models.CharField(max_length=100, null=True)
	billing_city = models.CharField(max_length=100, null=True)
	billing_state = models.CharField(max_length=50, null=True)
	billing_zip = models.CharField(max_length=16, null=True)
	billing_country = models.CharField(max_length=100, null=True)
	exp_month = models.IntegerField(max_length=2, null=True)
	exp_year = models.IntegerField(max_length=2, null=True)
	cc_four = models.CharField(max_length=4, null=True, blank=True)
	brand = models.CharField(max_length=50, null=True)










