from rest_framework.routers import DefaultRouter
from .views import MenuItemViewSet

router = DefaultRouter()
router.register(r"menu-items", MenuItemViewSet)

urlpatterns = router.urls