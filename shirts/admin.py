from django.contrib import admin
from .models import Brand, Shirt, ShirtStyle

class BrandAdmin(admin.ModelAdmin):
	class Meta:
		model = Brand

admin.site.register(Brand, BrandAdmin)

class ShirtStyleInline(admin.TabularInline):
	model = ShirtStyle
	extra = 0

class ShirtAdmin(admin.ModelAdmin):
	inlines = (ShirtStyleInline,)

	class Meta:
		model = Shirt

admin.site.register(Shirt, ShirtAdmin)