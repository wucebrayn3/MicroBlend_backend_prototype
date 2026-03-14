from rest_framework.routers import DefaultRouter
from .views import MenuItemViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r"menu-items", MenuItemViewSet)
router.register(r"categories", CategoryViewSet)
urlpatterns = router.urls