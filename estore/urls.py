from django.conf import settings

from django.conf.urls import patterns, include, url

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
    	'document_root': settings.STATIC_ROOT
    	}),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
    	'document_root': settings.MEDIA_ROOT
    	}),  

    url(r'^admin/', include(admin.site.urls)),
    # url(r'^customadmin/track_input', 'products.views.track_input'),
    # url(r'^customadmin/album/', 'products.views.new'),
    # url(r'^customadmin/album_images/', 'products.views.album_image_upload'),

    #Misc views (home page, email, FAQ)
    url(r'^', include('misc.urls')),

    #Cart app URLs
    url(r'^cart/', include('cart.urls')),

    #Accounts URLs
    url(r'^accounts/', include('accounts.urls')),

    #Order URLs
    url(r'^orders/', include('orders.urls')),
    
    #Albums app URLs
    url(r'^artists/', include('albums.artist_urls')),
    url(r'^albums/', include('albums.album_urls')),

    #Shirt app urls
    url(r'^shirts/', include('shirts.urls')),
    url(r'^companies/(?P<slug>.*)$', 'shirts.views.brand_detail', name='brand_detail'),
)