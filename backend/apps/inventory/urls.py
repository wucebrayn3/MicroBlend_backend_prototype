from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, InventoryBatchViewSet, InventoryMovementViewSet

router = DefaultRouter()
router.register("inventory/ingredients", IngredientViewSet, basename="ingredients")
router.register("inventory/batches", InventoryBatchViewSet, basename="inventory-batches")
router.register("inventory/movements", InventoryMovementViewSet, basename="inventory-movements")
urlpatterns = router.urls
