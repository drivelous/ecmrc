from django import forms

class EmailMe(forms.Form):
	name = forms.CharField(required=True)
	email = forms.EmailField()
	subject = forms.CharField(required=True)
	message = forms.CharField(required=True)