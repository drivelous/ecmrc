from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect

from all_products.views import current_url
from all_products.models import Product, ProductType
from all_products.queryutil import ShirtQuery
from cart.forms import ShirtQtyForm
from cart.formutils import CartQuery
from cart.custom import create_or_retrieve_cart

from .models import Brand, Shirt, ShirtStyle

def filter_brand(shirt_list, brand):
	"""Filters all_shirts results by brand"""

	return [shirt for shirt in shirt_list if str(shirt.get_parent()) == brand]

def filter_size(shirt_list, size):
	"""Filters all_shirts results by sizes available"""

	filtered_shirts = []
	for shirt in shirt_list:
		shirt_query = ShirtQuery(shirt)
		if shirt_query.get_stock(size) > 0:
			filtered_shirts.append(shirt)
	return filtered_shirts

def all_shirts(request):
	"""Displays all shirts objects in stock unless user filters results"""

	# Start with list of all active shirts, brands, and sizes
	shirts = Product.objects.filter(product_type='1', active=True)
	brands = Brand.objects.all()
	sizes = ['XS', 'S', 'M', 'L', 'XL']

	# Check if user has specified whether to filter results
	# First, filter by brand if user specifies
	brand_query = request.GET.get('company', None)
	if brand_query is not None:
		shirts = filter_brand(shirts, brand_query)

	# Then, filter by size if user specifies
	size_query = request.GET.get('size', None)
	if size_query is not None:
		shirts = filter_size(shirts, size_query)

	# Structure the URL for correct amount of get params
	currenturl = current_url(request)

	# Based on the results of the filters, create apt paginator
	paginator = Paginator(shirts, 20)

	page = request.GET.get('page')

	try:
		shirt_list = paginator.page(page)
	except PageNotAnInteger:
		shirt_list = paginator.page(1)
	except EmptyPage:
		shirt_list = paginator.page(paginator.num_pages)
	
	return render(request, 'shirts/all_shirts.html', {
		'shirts': shirt_list,
		'paginator': paginator,
		'brands': brands,
		'sizes': sizes,
		'brand_query': brand_query,
		'size_query': size_query,
		'currenturl': currenturl,
	})

def shirt_detail(request, slug=None):
	"""Detail view of selected shirt object. Allows user to
	add shirt to shopping cart
	"""

	add_product = ShirtQtyForm(request.POST or None)
	shirt = get_object_or_404(Product, slug=slug)
	product_type = shirt.product_type
	shirt_style = shirt.get_style()
	brand = shirt.get_parent()

	# A bit of a hack to get a price to display
	price = shirt.get_price('S')

	shirt_query = ShirtQuery(shirt)

	default = shirt.get_default_image()
	images = shirt.get_images()
	stock = shirt_query.sizes_available()
	all_available = shirt_query.all_available()

	# Retrieves image and slug to display other shirts
	other_styles = []
	for style in shirt_style.get_active_styles():
		product = style.get_product()
		slug = product.slug
		default_other = product.get_default_image()
		other_styles.append([default_other, slug])

	if request.method == 'POST' and add_product.is_valid():
		cart = create_or_retrieve_cart(request)
		cart_query = CartQuery(request=request, cart=cart, cleaned_data=add_product.cleaned_data)
		cart_query.add_to_cart(product_type)
		return HttpResponseRedirect('/cart/')

	return render(request, 'shirts/shirt_detail.html', {
		'shirt': shirt,
		'brand': brand,
		'price': price,
		'stock': stock,
		'all_available': all_available,
		'other_styles': other_styles,
		'quantity': range(90),
		'images': images,
		'default': default,
		'add_product': add_product,
	})

def brand_detail(request, slug=None):
	"""Detail view of a brand's page"""

	brand = get_object_or_404(Brand, slug=slug)
	products = Product.objects.filter(shirtstyle__shirt__brand__name=brand.name)

	return render(request, 'brands/brand_detail.html', {
		'brand': brand,
		'products': products
	})