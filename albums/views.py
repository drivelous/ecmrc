from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect

from all_products.models import Product, ProductType
from all_products.views import current_url
from cart.forms import AlbumQtyForm
from cart.formutils import CartQuery
from cart.custom import create_or_retrieve_cart
from .models import Artist, Album, Track

def filter_band(album_list, artist):
	"""Filters album lists by artist in all_albums search results"""

	return [album for album in album_list if str(album.get_parent()) == artist]

def all_albums(request):
	"""Retrieves all music albums. User can filter results from this view"""
	
	albums = [album for album in Product.objects.filter(product_type='2', active=True)]
	artists = Artist.objects.all()

	# if artist_query is not None, will filter results based on value
	artist_query = request.GET.get('artist', None)
	if artist_query is not None:
		albums = filter_band(albums, artist_query)

	currenturl = current_url(request)
	paginator = Paginator(albums, 5)
	page = request.GET.get('page')

	try:
		album_list = paginator.page(page)
	except PageNotAnInteger:
		album_list = paginator.page(1)
	except EmptyPage:
		album_list = paginator.page(paginator.num_pages)

	return render(request, 'albums/all_albums.html', {
		'albums': album_list,
		'paginator': paginator,
		'artists': artists,
		'artist_query': artist_query,
		'currenturl': currenturl
	})

def album_detail(request, slug):
	"""Views music album detail"""

	add_product = AlbumQtyForm(request.POST or None)
	album = get_object_or_404(Product, slug=slug)
	product_type = album.product_type
	artist = album.get_artist()
	stock = album.get_stock()
	album_info = album.get_album()
	tracks = album_info.get_tracks()

	if request.method == 'POST' and add_product.is_valid():
		cart = create_or_retrieve_cart(request)
		cart_query = CartQuery(request=request, cart=cart, cleaned_data=add_product.cleaned_data)
		cart_query.add_to_cart(product_type)
		return HttpResponseRedirect('/cart/')

	return render(request, 'albums/album_detail.html', {
		'album': album,
		'artist': artist,
		'album_info': album_info,
		'tracks': tracks,
		'add_product': add_product,
		'quantity': [num for num in range(stock)]
	})

def all_artists(request):
	"""Retrieves all music artists from database"""

	artists = [(e, e.album_set.all()) for e in Artist.objects.prefetch_related('album_set')]
	paginator = Paginator(artists, 5)

	page = request.GET.get('page')

	try:
		artist_list = paginator.page(page)
	except PageNotAnInteger:
		artist_list = paginator.page(1)
	except EmptyPage:
		artist_list = paginator.page(paginator.num_pages)

	return render(request, 'artists/all_artists.html', {
		'artists': artist_list,
	})

def artist_detail(request, slug):
	"""Detail view for music artist"""

	artist = get_object_or_404(Artist, slug=slug)
	return render(request, 'artists/artist_detail.html', {
		'artist': artist
	})