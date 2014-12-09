from django import forms

from albums.models import Album
from all_products.models import Product

class ShirtQtyForm(forms.Form):
	"""Form used for adding shirts to a shopping cart"""

	pk = forms.IntegerField(required=True)
	size = forms.CharField(required=True)
	product_type = forms.CharField(required=True)
	quantity = forms.IntegerField(required=True)

class AlbumQtyForm(forms.Form):
	"""Form used for adding music albums to a shopping cart"""

	pk = forms.IntegerField(required=True)
	product_type = forms.CharField(required=True)
	quantity = forms.IntegerField(required=True)

class DeleteItemForm(forms.Form):
	"""Form used for deleting any product from a user's shopping cart"""

	cartitem = forms.IntegerField(required=True)	

class UpdateItemForm(forms.Form):
	"""Form used for updating item qty in user's shopping cart"""

	cartitem = forms.IntegerField(required=True)
	quantity = forms.IntegerField(required=True)