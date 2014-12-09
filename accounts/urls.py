from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView

urlpatterns = patterns('',
	url(r'^create/$', 'accounts.views.create_account', name='signup'),
	url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': 'logged_out'}, name='logout'),
	url(r'^see-ya/$', 'accounts.views.logged_out', name='logged_out'),
    url(r'^login/$', 'accounts.views.login_view', name='login'),
    url(r'^password/reset/$', 'django.contrib.auth.views.password_reset', {'template_name': 'accounts/password_reset.html',
    	'post_reset_redirect': 'accounts.views.reset_redirect'}, name='password_reset'),
    url(r'^password/reset/done/$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'accounts/password_reset_done.html'}, name='password_reset_done'),
	url(r'^password/awaiting_reset/$', 'accounts.views.reset_redirect', name='post_reset_redirect'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'accounts/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete', {'template_name': 'accounts/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^profile/$', 'accounts.views.view_profile', name='profile'),
    url(r'^shipping/$', 'accounts.views.view_shipping', name='user_shipping'),
    url(r'^payment/$', 'accounts.views.view_payment', name='user_payment'),
    url(r'^orders/$', 'accounts.views.past_order_history', name='order_history'),
    url(r'^orders/(?P<order_id>.*)/$', 'accounts.views.past_order_detail', name="order_detail"),
)