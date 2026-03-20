from rest_framework.routers import DefaultRouter
from .views import StaffPageRequestViewSet, TableMergeGroupViewSet, TableScanRequestViewSet, TableViewSet

router = DefaultRouter()
router.register(r"tables", TableViewSet)
router.register(r"table-merges", TableMergeGroupViewSet, basename="table-merges")
router.register(r"table-scan-requests", TableScanRequestViewSet, basename="table-scan-requests")
router.register(r"staff-pages", StaffPageRequestViewSet, basename="staff-pages")
urlpatterns = router.urls
