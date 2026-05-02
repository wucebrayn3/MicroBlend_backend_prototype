from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny

from common.permissions import IsAuthenticatedAndActive, IsStaffOrAdmin

from .models import Category, MenuItem, OrderPlaylist
from .serializers import CategorySerializer, CustomerMenuItemSerializer, MenuItemSerializer, OrderPlaylistSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrAdmin]


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        queryset = MenuItem.objects.select_related("category").prefetch_related("ingredients__ingredient").all()
        sort_by = self.request.query_params.get("sort")
        audience = self.request.query_params.get("audience")
        if audience == "customer":
            queryset = queryset.filter(is_available=True)
        if sort_by == "price":
            queryset = queryset.order_by("price", "name")
        elif sort_by == "popularity":
            queryset = queryset.order_by("-popularity_score", "name")
        else:
            queryset = queryset.order_by("name")
        return queryset

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [IsStaffOrAdmin()]

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"} and self.request.query_params.get("audience") == "customer":
            return CustomerMenuItemSerializer
        return MenuItemSerializer


class OrderPlaylistViewSet(viewsets.ModelViewSet):
    serializer_class = OrderPlaylistSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        if self.request.user.is_guest:
            return OrderPlaylist.objects.none()
        return OrderPlaylist.objects.filter(owner=self.request.user).prefetch_related("items__menu_item")

    def perform_create(self, serializer):
        if self.request.user.is_guest:
            raise PermissionDenied("Guest users cannot create order playlists.")
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.is_guest:
            raise PermissionDenied("Guest users cannot edit order playlists.")
        serializer.save()
