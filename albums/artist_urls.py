from django.conf.urls import patterns, include, url

from albums import views

# Splits URL dispatcher in app: one for artists, another for their albums
urlpatterns = patterns('',
    # Will re-do and commit all_artists after initial release
    #url(r'^$', views.all_artists, name='all_artists'),
    url(r'^(?P<slug>.*)/$', views.artist_detail, name='artist_detail'),
)