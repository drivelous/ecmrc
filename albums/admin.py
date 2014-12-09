from django.contrib import admin
from .models import Artist, Album, Track


class ArtistAdmin(admin.ModelAdmin):
	class Meta:
		model = Artist

admin.site.register(Artist, ArtistAdmin)

class TrackInline(admin.TabularInline):
	model = Track
	extra = 15
	fields = ('track_no', 'name', 'minutes', 'seconds')

class AlbumAdmin(admin.ModelAdmin):
	inlines = [
		TrackInline,
	]

admin.site.register(Album, AlbumAdmin)