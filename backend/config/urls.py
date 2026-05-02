from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include("apps.analytics.urls")),
    path("api/", include("apps.feedback.urls")),
    path("api/", include("apps.integrations.urls")),
    path("api/", include("apps.inventory.urls")),
    path("api/", include("apps.menu.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/", include("apps.realtime.urls")),
    path("api/", include("apps.tables.urls")),
    path("api/", include("apps.table_sessions.urls")),
    path("api/", include("apps.users.urls")),
]
