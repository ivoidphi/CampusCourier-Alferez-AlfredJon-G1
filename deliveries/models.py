from django.conf import settings
from django.db import models


class DeliveryRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_deliveries",
    )
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courier_deliveries",
    )
    item_description = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=150)
    dropoff_location = models.CharField(max_length=150)
    notes = models.TextField(blank=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.id} - {self.item_description} ({self.get_status_display()})"