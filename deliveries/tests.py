from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser

from .forms import DeliveryRequestForm
from .models import DeliveryRequest


class DeliveryRequestFormTests(TestCase):
    def form_data(self, **overrides):
        data = {
            "item_description": "Coffee",
            "pickup_location": "Main Canteen",
            "dropoff_location": "Library",
            "delivery_fee": "25.00",
            "notes": "",
        }
        data.update(overrides)
        return data

    def test_form_accepts_valid_delivery_request(self):
        form = DeliveryRequestForm(data=self.form_data())

        self.assertTrue(form.is_valid(), form.errors)

    def test_form_rejects_non_positive_fee(self):
        form = DeliveryRequestForm(data=self.form_data(delivery_fee="0"))

        self.assertFalse(form.is_valid())
        self.assertIn("delivery_fee", form.errors)

    def test_form_rejects_same_pickup_and_dropoff(self):
        form = DeliveryRequestForm(
            data=self.form_data(
                pickup_location="Main Canteen",
                dropoff_location=" main canteen ",
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class DeliveryRequestViewsTests(TestCase):
    def create_user(self, role, suffix):
        return CustomUser.objects.create_user(
            username=f"{role.lower()}-{suffix}",
            email=f"{role.lower()}-{suffix}@example.edu",
            password="test-password-123",
            role=role,
            student_id=f"{role.lower()}-{suffix}",
            contact_number="09171234567",
        )

    def create_delivery(self, customer, **overrides):
        values = {
            "customer": customer,
            "item_description": "Coffee",
            "pickup_location": "Main Canteen",
            "dropoff_location": "Library",
            "delivery_fee": Decimal("25.00"),
        }
        values.update(overrides)
        return DeliveryRequest.objects.create(**values)

    def setUp(self):
        self.customer = self.create_user(CustomUser.Role.CUSTOMER, "one")
        self.other_customer = self.create_user(CustomUser.Role.CUSTOMER, "two")
        self.courier = self.create_user(CustomUser.Role.COURIER, "one")
        self.admin = self.create_user(CustomUser.Role.ADMIN, "one")

    def test_customer_can_create_request_and_becomes_owner(self):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("deliveries:create_delivery"),
            {
                "item_description": "Coffee",
                "pickup_location": "Main Canteen",
                "dropoff_location": "Library",
                "delivery_fee": "25.00",
                "notes": "Leave at front desk",
            },
        )

        delivery = DeliveryRequest.objects.get()
        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
        )
        self.assertEqual(delivery.customer, self.customer)
        self.assertEqual(delivery.status, DeliveryRequest.Status.PENDING)

    def test_non_customer_cannot_create_request(self):
        self.client.force_login(self.courier)

        response = self.client.get(reverse("deliveries:create_delivery"))

        self.assertRedirects(
            response,
            reverse("deliveries:my_deliveries"),
            fetch_redirect_response=False,
        )
        self.assertFalse(DeliveryRequest.objects.exists())

    def test_list_is_scoped_by_role(self):
        customer_delivery = self.create_delivery(self.customer)
        other_delivery = self.create_delivery(self.other_customer)
        assigned_delivery = self.create_delivery(
            self.other_customer,
            courier=self.courier,
            status=DeliveryRequest.Status.ACCEPTED,
        )

        self.client.force_login(self.customer)
        response = self.client.get(reverse("deliveries:my_deliveries"))
        self.assertEqual(
            list(response.context["deliveries"]),
            [customer_delivery],
        )

        self.client.force_login(self.courier)
        response = self.client.get(reverse("deliveries:my_deliveries"))
        self.assertEqual(
            list(response.context["deliveries"]),
            [assigned_delivery],
        )
        self.assertNotIn(other_delivery, response.context["deliveries"])

        self.client.force_login(self.admin)
        response = self.client.get(reverse("deliveries:my_deliveries"))
        self.assertCountEqual(
            response.context["deliveries"],
            [customer_delivery, other_delivery, assigned_delivery],
        )

    def test_detail_is_available_to_owner_admin_and_courier_for_open_request(self):
        delivery = self.create_delivery(self.customer)
        url = reverse("deliveries:delivery_detail", args=[delivery.pk])

        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.courier)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_customer_cannot_view_another_customers_delivery(self):
        delivery = self.create_delivery(self.other_customer)
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("deliveries:delivery_detail", args=[delivery.pk])
        )

        self.assertRedirects(
            response,
            reverse("deliveries:my_deliveries"),
            fetch_redirect_response=False,
        )

    def test_customer_can_edit_pending_delivery(self):
        delivery = self.create_delivery(self.customer)
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("deliveries:edit_delivery", args=[delivery.pk]),
            {
                "item_description": "Tea",
                "pickup_location": "Cafe",
                "dropoff_location": "Library",
                "delivery_fee": "30.00",
                "notes": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
        )
        delivery.refresh_from_db()
        self.assertEqual(delivery.item_description, "Tea")
        self.assertEqual(delivery.delivery_fee, Decimal("30.00"))

    def test_customer_cannot_edit_another_customers_delivery(self):
        delivery = self.create_delivery(self.other_customer)
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("deliveries:edit_delivery", args=[delivery.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_non_pending_delivery_cannot_be_edited_or_deleted(self):
        delivery = self.create_delivery(
            self.customer,
            status=DeliveryRequest.Status.ACCEPTED,
        )
        self.client.force_login(self.customer)

        edit_response = self.client.post(
            reverse("deliveries:edit_delivery", args=[delivery.pk]),
            {"item_description": "Changed"},
        )
        delete_response = self.client.post(
            reverse("deliveries:delete_delivery", args=[delivery.pk])
        )

        self.assertRedirects(
            edit_response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            delete_response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
            fetch_redirect_response=False,
        )
        self.assertTrue(DeliveryRequest.objects.filter(pk=delivery.pk).exists())

    def test_delete_requires_post_confirmation(self):
        delivery = self.create_delivery(self.customer)
        self.client.force_login(self.customer)
        url = reverse("deliveries:delete_delivery", args=[delivery.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(DeliveryRequest.objects.filter(pk=delivery.pk).exists())

        response = self.client.post(url)

        self.assertRedirects(response, reverse("deliveries:my_deliveries"))
        self.assertFalse(DeliveryRequest.objects.filter(pk=delivery.pk).exists())

# Create your tests here.
