from django.conf import settings

import stripe
stripe.api_key = settings.STRIPE_API_KEY

from accounts.models import Profile, ShippingAddress, DefaultBilling

from .models import Order

def create_or_retrieve_order(request, cart):
	"""Retrieves existing order or creates skeleton of an order"""

	profile = Profile.objects.get(user=request.user)
	
	try:
		order = Order.objects.get(cart=cart)
	except Order.DoesNotExist:
		order = Order(
					profile=profile,
					cart=cart
				)
		order.save()

	default_shipping = profile.get_default_shipping()
	default_billing = profile.get_default_billing()

	# if order has no shipping_address but there's a default_shipping
	# address available, make the default address this order's shipping address
	if not order.shipping_address and default_shipping is not None:
		default_shipping = profile.shippingaddress_set.filter(default_address=True).first()
		order.shipping_address = default_shipping
		order.save()

	# if order has no billing_address but there's a default_billing address
	# then make the default_billing address the order's billing address
	if not order.billing_address1 and default_billing is not None:
		order.update_order_billing(full_name=default_billing.full_name,
									address1=default_billing.billing_address1,
									address2=default_billing.billing_address2,
									city=default_billing.billing_city,
									state=default_billing.billing_state,
									zip_code=default_billing.billing_zip,
									country=default_billing.billing_country,
									exp_month=default_billing.exp_month,
									exp_year=default_billing.exp_year,
									cc_four=default_billing.cc_four,
									brand=default_billing.brand
								)
	return order