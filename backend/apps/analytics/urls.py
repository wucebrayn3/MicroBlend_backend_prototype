from rest_framework.routers import DefaultRouter

from .views import AnalyticsViewSet, CostSimulationViewSet, GeneratedReportViewSet

router = DefaultRouter()
router.register("analytics", AnalyticsViewSet, basename="analytics")
router.register("analytics/reports", GeneratedReportViewSet, basename="analytics-reports")
router.register("analytics/simulations", CostSimulationViewSet, basename="analytics-simulations")
urlpatterns = router.urls
