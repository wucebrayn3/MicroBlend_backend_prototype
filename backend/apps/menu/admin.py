from django.contrib import admin
from .models import Category, MenuItem, MenuItemIngredient, OrderPlaylist, OrderPlaylistItem

admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(MenuItemIngredient)
admin.site.register(OrderPlaylist)
admin.site.register(OrderPlaylistItem)
