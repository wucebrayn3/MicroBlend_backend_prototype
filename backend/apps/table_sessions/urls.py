from rest_framework.routers import DefaultRouter
from .views import TableSessionViewSet

router = DefaultRouter()
router.register("table-sessions", TableSessionViewSet)
urlpatterns = router.urls