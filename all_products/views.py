# All product views are located in the views of their respective apps
# EX: shirts.views/albums.views

def current_url(request):
	"""Takes get request and returns correctly structured URL for
	any number of GET parameters
	"""

	if len(request.GET) == 0:
		return request.get_full_path() + '?'
	else:
		return request.get_full_path() + '&'
