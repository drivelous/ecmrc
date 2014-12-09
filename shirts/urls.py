from django.conf.urls import patterns, include, url

from shirts import views

urlpatterns = patterns('',
    url(r'^$', views.all_shirts, name='all_shirts'),
    url(r'^(?P<slug>.*)/$', views.shirt_detail, name='shirt_detail'),
)