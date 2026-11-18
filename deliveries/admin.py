from django.contrib import admin

from .models import DeliveryRequest


@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item_description",
        "customer",
        "courier",
        "delivery_fee",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "item_description",
        "pickup_location",
        "dropoff_location",
        "customer__username",
    )
