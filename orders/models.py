import string, random, datetime

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db import models
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render
from django.template.loader import get_template, render_to_string
from django.template import Context

from localflavor.us.models import PhoneNumberField

import stripe
stripe.api_key = settings.STRIPE_API_KEY

from cart.models import Cart
from accounts.models import Profile, ShippingAddress

STATUS_CHOICES = (
	('Started', 'Started'),
	('Collected', 'Collected'),
)

def order_id_generator(size=8, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

class Order(models.Model):
	profile = models.ForeignKey(Profile, null=True, blank=True)
	cart = models.ForeignKey(Cart)
	order_id = models.CharField(max_length=50, null=True, unique=True)
	full_name = models.CharField(max_length=100, null=True, blank=False)
	shipping_address = models.ForeignKey(ShippingAddress, null=True, blank=False, on_delete=models.SET_NULL)
	card_id = models.CharField(max_length=100, null=True)
	shipping_nickname = models.CharField(max_length=100, null=True)
	shipping_first_name = models.CharField(max_length=100, null=True)
	shipping_last_name = models.CharField(max_length=100, null=True)
	shipping_address1 = models.CharField(max_length=100, null=True)
	shipping_address2 = models.CharField(max_length=100, null=True)
	shipping_city = models.CharField(max_length=100, null=True)
	shipping_state = models.CharField(max_length=100, null=True)
	shipping_zip = models.CharField(max_length=16, null=True)
	shipping_country = models.CharField(max_length=100, null=True)
	shipping_phone_number = PhoneNumberField(null=True, blank=True)
	billing_address1 = models.CharField(max_length=100, null=True)
	billing_address2 = models.CharField(max_length=100, null=True, blank=True)
	billing_city = models.CharField(max_length=100, null=True)
	billing_state = models.CharField(max_length=50, null=True)
	billing_zip = models.CharField(max_length=16, null=True)
	billing_country = models.CharField(max_length=100, null=True)
	exp_month = models.IntegerField(max_length=2, null=True)
	exp_year = models.IntegerField(max_length=2, null=True)
	cc_four = models.CharField(max_length=4, null=True, blank=True)
	brand = models.CharField(max_length=50, null=True)
	active = models.BooleanField(default=True)
	status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Started')
	date_completed = models.DateTimeField(null=True, blank=True, auto_now_add=False)

	def save(self, *args, **kwargs):
		"""Generates guaranteed unique ID for each order"""
		if not self.order_id:
			while not self.order_id:
				order_id = order_id_generator()
				gen_order_id = str(order_id[:3]) + str(self.cart_id) + str(order_id[3:])
				if not Order.objects.filter(order_id=gen_order_id):
					self.order_id = gen_order_id

		# If shipping address changes, save all info. This saves history of addresses
		# for orders even if user deletes address from database
		addr = self.shipping_address
		if self.active is not False and addr is not None and addr.address1 != self.shipping_address1:
			self.shipping_nickname = addr.nickname
			self.shipping_first_name = addr.first_name
			self.shipping_last_name = addr.last_name
			self.shipping_address1 = addr.address1
			self.shipping_address2 = addr.address2
			self.shipping_city = addr.city
			self.shipping_state = addr.state
			self.shipping_zip = addr.zip_code
			self.shipping_country = addr.country
			self.shipping_phone_number = addr.phone_number

		super(Order, self).save(*args, **kwargs)

	def update_order_billing(self, full_name=None, card_id=None, address1=None, address2=None, city=None, state=None, zip_code=None, country=None, exp_month=None, exp_year=None, cc_four=None, brand=None):
		self.full_name = full_name
		self.card_id = card_id
		self.billing_address1 = address1
		self.billing_address2 = address2
		self.billing_city = city
		self.billing_state = state
		self.billing_zip = zip_code
		self.billing_country = country
		self.exp_month = exp_month
		self.exp_year = exp_year
		self.cc_four = cc_four
		self.brand = brand
		self.save()

	def charge_customer(self, customer):
		"""
		Charge customer using card that is
		tied to order
		"""
		stripe.Charge.create(
			amount=int(self.cart.total * 100),
			currency="usd",
			customer=customer.id,
			card=self.card_id,
			description="Payment for order #{0}".format(self.order_id)
		)

	def send_order_confirmation(self, request, order_email):
		"""Sends email to user confirming order and contents"""
		
		user = self.profile.user

		context = Context({
						'user': user,
						'cart': self.cart,
						'MEDIA_URL': settings.MEDIA_URL,
						'SITE_URL': settings.SITE_URL
						})

		subject = 'Thanks for the biz! Here\'s your order confirmation.'
		from_email = 'Sean Dominguez <sean@drivelous.com>'
		
		# If at order screen, user provided an email address
		if order_email != '':
			to = order_email
		else:
			to = self.profile.user.email
			
		text_content = render_to_string('orders/email/order_confirmation.txt', context)
		html_content = render_to_string('orders/email/order_confirmation.html', context)
		msg = EmailMultiAlternatives(subject, text_content)
		msg.attach_alternative(html_content, "text/html")
		msg.to = [to]
		msg.from_email = from_email

		# Send a copy to me after finished as well
		msg_copy = EmailMultiAlternatives("Copy of order confirmation", text_content)
		msg_copy.attach_alternative(html_content, "text/html")
		msg_copy.to = ['sean@drivelous.com']
		msg_copy.from_email = from_email

		msg.send()
		msg_copy.send()

	def finalize(self, request, customer, order_email):
		"""
		1.) Confirms all products available, decrements db, sets cart inactive
		2.) Charges customer
		3.) Sets order to finished
		4.) Sends confirmation email
		"""

		# Safe guard against faked submissions
		if not self.shipping_address:
			messages.warning(request, 'You\'re naughty. Fake submission? No shipping address specified.')
			return False
		if not self.billing_address1:
			messages.warning(request, 'You\'re naughty. Fake submission? No payment information entered.')
			return False
			
		successful = self.cart.finalize_cart(request)

		if successful:
			self.charge_customer(customer)
			self.status = 'Collected'
			self.active = False
			messages.info(request, 'Your order has been completed and will be shipping shortly. Thanks for your business!')
			self.date_completed = datetime.datetime.now()
			self.save()
			self.send_order_confirmation(request, order_email)
			return True
		else:
			return False

	def __str__(self):
		return "Order # is {0} -- Status is {1}".format(self.order_id, self.status)