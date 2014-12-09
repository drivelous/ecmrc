from django.conf import settings

from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^$', 'misc.views.home', name='home'),
	url(r'^about/$', 'misc.views.about', name='about'),
	url(r'^contact/$', 'misc.views.email_sean', name='contact_me'),
	url(r'^walkthrough/$', 'misc.views.walkthrough', name='walkthrough')
)