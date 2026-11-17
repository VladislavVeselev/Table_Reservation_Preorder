from django.urls import path

from . import views

urlpatterns = [
    path("points/", views.PointListView.as_view(), name="point-list"),
    path("points/my/", views.MyPointView.as_view(), name="my-point"),
    path("points/my/tables/", views.MyPointTablesView.as_view(), name="my-point-tables"),  # <-- новый
    path("points/<int:pk>/tables/", views.PointTablesView.as_view(), name="point-tables"),
    path("points/<int:pk>/", views.PointDetailView.as_view(), name="point-detail"),
    path("networks/my/", views.MyNetworkView.as_view(), name="my-network"),
]