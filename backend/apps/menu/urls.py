from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet, OrderPlaylistViewSet

router = DefaultRouter()
router.register(r"menu-items", MenuItemViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"order-playlists", OrderPlaylistViewSet, basename="order-playlists")
urlpatterns = router.urls
