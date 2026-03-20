from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LoginView, LogoutView, MeView, MyHistoryView, RegisterView, UserAdminViewSet

router = DefaultRouter()
router.register("admin/users", UserAdminViewSet, basename="admin-users")

urlpatterns = [
    path("identity/register/", RegisterView.as_view(), name="register"),
    path("identity/login/", LoginView.as_view(), name="login"),
    path("identity/logout/", LogoutView.as_view(), name="logout"),
    path("identity/me/", MeView.as_view(), name="me"),
    path("identity/me/history/", MyHistoryView.as_view(), name="my-history"),
    path("", include(router.urls)),
]
