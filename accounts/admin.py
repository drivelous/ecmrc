from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Customer, Profile, ShippingAddress, DefaultBilling
from .forms import UserCreationForm, UserChangeForm

class CustomerAdmin(UserAdmin):
	add_form = UserCreationForm
	form = UserChangeForm

	list_display = ('username', 'email', 'is_staff',)
	list_filter = ('is_staff', 'is_superuser',
		'is_active',)
	search_fields = ('email',)
	ordering = ('email',)
	filter_horizontal = ('groups', 'user_permissions',)
	fieldsets = (
		(None, {'fields': ('username', 'email', 'password')}),
		('Personal info', {'fields': ('is_active',
									'is_staff',
									'is_superuser',
									'groups',
									'user_permissions')}),
		('Important dates', {'fields': ('last_login',)}),
		)

	add_field_sets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'password1', 'password2')}
			)
	)

admin.site.register(Customer, CustomerAdmin)

class ProfileAdmin(admin.ModelAdmin):
	class Meta:
		model = Profile

admin.site.register(Profile, ProfileAdmin)

class ShippingAddressAdmin(admin.ModelAdmin):
	class Meta:
		model = ShippingAddress

admin.site.register(ShippingAddress, ShippingAddressAdmin)

class DefaultBillingAdmin(admin.ModelAdmin):
	class Meta:
		model = DefaultBilling

admin.site.register(DefaultBilling, DefaultBillingAdmin)