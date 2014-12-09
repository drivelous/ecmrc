from django.conf.urls import patterns, include, url

from albums import views

# Splits URL dispatcher in app: one for artists, another for their albums
urlpatterns = patterns('',  
    url(r'^$', views.all_albums, name='all_albums'),
    url(r'^(?P<slug>.*)/$', views.album_detail, name='album_detail'),
)