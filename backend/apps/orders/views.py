from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAuthenticatedAndActive, IsStaffOrAdmin, build_staff_role_permission

from .models import Order, OrderItem
from .serializers import (
    CancelOrderSerializer,
    CashierStatusSerializer,
    OrderItemSerializer,
    OrderSerializer,
    PlaylistOrderSerializer,
    StationStatusSerializer,
    SubmitOrderSerializer,
)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("table_session", "placed_by").prefetch_related("items", "status_logs").all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in {"create", "list", "retrieve", "submit", "cancel", "from_playlist"}:
            return [IsAuthenticatedAndActive()]
        if self.action in {"kitchen_update"}:
            return [build_staff_role_permission("kitchen")()]
        if self.action in {"bar_update"}:
            return [build_staff_role_permission("bar")()]
        if self.action in {"cashier_update"}:
            return [build_staff_role_permission("cashier")()]
        return [IsStaffOrAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.role == "customer":
            return queryset.filter(placed_by=user)
        if user.role == "staff" and user.staff_role == "waiter":
            return queryset
        if user.role == "staff" and user.staff_role == "kitchen":
            return queryset.filter(items__station="kitchen").distinct()
        if user.role == "staff" and user.staff_role == "bar":
            return queryset.filter(items__station="bar").distinct()
        return queryset

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        order = self.get_object()
        serializer = SubmitOrderSerializer(data=request.data, context={"order": order, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        serializer = CancelOrderSerializer(data=request.data, context={"order": order, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"], permission_classes=[build_staff_role_permission("kitchen")])
    def kitchen_update(self, request, pk=None):
        order = self.get_object()
        serializer = StationStatusSerializer(data=request.data, context={"order": order, "request": request, "station": "kitchen"})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"], permission_classes=[build_staff_role_permission("bar")])
    def bar_update(self, request, pk=None):
        order = self.get_object()
        serializer = StationStatusSerializer(data=request.data, context={"order": order, "request": request, "station": "bar"})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"], permission_classes=[build_staff_role_permission("cashier")])
    def cashier_update(self, request, pk=None):
        order = self.get_object()
        serializer = CashierStatusSerializer(data=request.data, context={"order": order, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    @action(detail=False, methods=["post"])
    def from_playlist(self, request):
        serializer = PlaylistOrderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderItem.objects.select_related("order", "menu_item").all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsStaffOrAdmin]
