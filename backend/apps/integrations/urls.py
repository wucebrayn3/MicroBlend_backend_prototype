from rest_framework.routers import DefaultRouter

from .views import ExternalSystemViewSet, SyncEventViewSet

router = DefaultRouter()
router.register("integrations/external-systems", ExternalSystemViewSet, basename="external-systems")
router.register("integrations/sync-events", SyncEventViewSet, basename="sync-events")
urlpatterns = router.urls
