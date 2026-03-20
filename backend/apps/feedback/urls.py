from rest_framework.routers import DefaultRouter

from .views import FeedbackEntryViewSet

router = DefaultRouter()
router.register("feedback", FeedbackEntryViewSet, basename="feedback")
urlpatterns = router.urls
