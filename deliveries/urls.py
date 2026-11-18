from django.urls import path

from . import views


app_name = "deliveries"

urlpatterns = [
    path("", views.my_deliveries, name="my_deliveries"),
    path("available/", views.available_deliveries, name="available_deliveries"),
    path("create/", views.create_delivery, name="create_delivery"),
    path("<int:pk>/", views.delivery_detail, name="delivery_detail"),
    path("<int:pk>/edit/", views.edit_delivery, name="edit_delivery"),
    path("<int:pk>/delete/", views.delete_delivery, name="delete_delivery"),
    path("<int:pk>/accept/", views.accept_delivery, name="accept_delivery"),
    path(
        "<int:pk>/status/",
        views.update_delivery_status,
        name="update_delivery_status",
    ),
]
