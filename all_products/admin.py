from django.contrib import admin
from .models import Product, ProductType, ProductImage

class ProductImageInline(admin.TabularInline):
	model = ProductImage
	extra = 3

class ProductAdmin(admin.ModelAdmin):
	class Meta:
		model = Product

	inlines = (ProductImageInline,)

admin.site.register(Product, ProductAdmin)

class ProductTypeAdmin(admin.ModelAdmin):
	class Meta:
		model = ProductType

admin.site.register(ProductType, ProductTypeAdmin)
