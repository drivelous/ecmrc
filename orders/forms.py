from django import forms

class UseAddressForm(forms.Form):
	address = forms.IntegerField(required=True)

class UseCardForm(forms.Form):
	index = forms.IntegerField(required=True)

class EnterEmailForm(forms.Form):
	email = forms.EmailField(required=False)