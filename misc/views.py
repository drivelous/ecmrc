from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, HttpResponseRedirect

from all_products.models import Product, ProductType
from shirts.models import Shirt, Brand
from albums.models import Album, Artist

from .forms import EmailMe

def email_sean(request):
	form = EmailMe(request.POST or None)

	if request.method == 'POST' and form.is_valid():

		cd = form.cleaned_data

		from_email = cd['name'] + ' <'+ cd['email'] + '>'
		subject = cd['subject']
		body = cd['message']

		send_mail(subject, body, from_email, [settings.EMAIL_HOST_USER])

	return render(request, 'email_me.html', {
		'form': form,
	})

def home(request):
	"""Displays all product types and links to products from parents
	of products of each product type"""

	products = Product.objects.filter(active=True).order_by('?')[:28]
	product_types = ProductType.objects.all()
	brands = Brand.objects.all()[:4]
	artists = Artist.objects.all()[:4]
	return render(request, 'home.html', {
		'product_types': product_types,
		'products': products,
		'brands': brands,
		'artists': artists,
	})

def walkthrough(request):
	"""Walkthrough page of eCommerce project"""
	return render(request, 'walkthrough.html', {})

def about(request):
	"""About this site"""
	return render(request, 'about.html', {})
