from django import forms

from .models import DeliveryRequest


class DeliveryRequestForm(forms.ModelForm):
    class Meta:
        model = DeliveryRequest
        fields = [
            "item_description",
            "pickup_location",
            "dropoff_location",
            "delivery_fee",
            "notes",
        ]
        widgets = {
            "item_description": forms.TextInput(
                attrs={"placeholder": "e.g., 2 Iced Coffees from Canteen"}
            ),
            "pickup_location": forms.TextInput(
                attrs={"placeholder": "e.g., Main Canteen"}
            ),
            "dropoff_location": forms.TextInput(
                attrs={"placeholder": "e.g., NGE Building Room 304"}
            ),
            "delivery_fee": forms.NumberInput(
                attrs={"step": "0.01", "min": "10", "placeholder": "e.g., 25.00"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional instructions (landmarks, contact note, fragile item, etc.)",
                }
            ),
        }

    def clean_delivery_fee(self):
        fee = self.cleaned_data.get("delivery_fee")
        if fee is not None and fee <= 0:
            raise forms.ValidationError("Delivery fee must be greater than ₱0.00.")
        return fee

    def clean(self):
        cleaned_data = super().clean()
        pickup = cleaned_data.get("pickup_location", "").strip()
        dropoff = cleaned_data.get("dropoff_location", "").strip()
        if pickup and dropoff and pickup.casefold() == dropoff.casefold():
            raise forms.ValidationError(
                "Pickup location and drop-off location cannot be the same."
            )
        return cleaned_data
