from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("analysis_app.urls")),
    path("", include("analysis_app.page_urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
