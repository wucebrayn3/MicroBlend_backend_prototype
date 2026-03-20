from rest_framework import serializers

from .models import Category, MenuItem, MenuItemIngredient, OrderPlaylist, OrderPlaylistItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class MenuItemIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = MenuItemIngredient
        fields = ("id", "ingredient", "ingredient_name", "quantity_required")


class MenuItemSerializer(serializers.ModelSerializer):
    ingredients = MenuItemIngredientSerializer(many=True, required=False)

    class Meta:
        model = MenuItem
        fields = "__all__"

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients", [])
        menu_item = MenuItem.objects.create(**validated_data)
        for ingredient_data in ingredients:
            MenuItemIngredient.objects.create(menu_item=menu_item, **ingredient_data)
        menu_item.recalculate_availability(save=True)
        return menu_item

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if ingredients is not None:
            instance.ingredients.all().delete()
            for ingredient_data in ingredients:
                MenuItemIngredient.objects.create(menu_item=instance, **ingredient_data)
        instance.recalculate_availability(save=True)
        return instance


class CustomerMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ("id", "name", "category", "description", "price", "prep_eta_minutes", "is_available", "popularity_score")


class OrderPlaylistItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = OrderPlaylistItem
        fields = ("id", "menu_item", "menu_item_name", "quantity")


class OrderPlaylistSerializer(serializers.ModelSerializer):
    items = OrderPlaylistItemSerializer(many=True)

    class Meta:
        model = OrderPlaylist
        fields = ("id", "name", "items", "created_at", "updated_at")

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        playlist = OrderPlaylist.objects.create(**validated_data)
        for item in items:
            OrderPlaylistItem.objects.create(playlist=playlist, **item)
        return playlist

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for item in items:
                OrderPlaylistItem.objects.create(playlist=instance, **item)
        return instance
