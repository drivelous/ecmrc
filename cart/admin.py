from django.contrib import admin

from albums.models import Album
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
	model = CartItem
	extra = 0

class CartAdmin(admin.ModelAdmin):
	inlines = (CartItemInline,)

	class Meta:
		model = Cart

admin.site.register(Cart, CartAdmin)