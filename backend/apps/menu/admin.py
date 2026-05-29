from django.contrib import admin
from .models import Category, MenuItem, MenuItemIngredient, OrderPlaylist, OrderPlaylistItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "created_at")
    search_fields = ("name",)
    readonly_fields = ("sort_order",)

class MenuItemIngredientInline(admin.TabularInline):
    model = MenuItemIngredient
    extra = 1


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "prep_eta_minutes", "preparation_station", "is_available")
    list_filter = ("category", "preparation_station", "is_available")
    search_fields = ("name", "description")
    inlines = [MenuItemIngredientInline]

admin.site.register(OrderPlaylist)
admin.site.register(OrderPlaylistItem)
