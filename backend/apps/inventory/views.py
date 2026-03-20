from rest_framework import mixins, viewsets

from apps.inventory.models import Ingredient, InventoryBatch, InventoryMovement
from apps.inventory.serializers import IngredientSerializer, InventoryBatchSerializer, InventoryMovementSerializer
from common.permissions import IsAdmin, IsStaffOrAdmin, build_staff_role_permission


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsStaffOrAdmin]


class InventoryBatchViewSet(viewsets.ModelViewSet):
    queryset = InventoryBatch.objects.select_related("ingredient").all()
    serializer_class = InventoryBatchSerializer
    permission_classes = [build_staff_role_permission("kitchen", "bar", "cashier")]


class InventoryMovementViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = InventoryMovement.objects.select_related("ingredient", "actor", "batch").all()
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAdmin]
