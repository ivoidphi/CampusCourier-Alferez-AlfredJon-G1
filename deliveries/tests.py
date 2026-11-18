import re
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser

from .forms import DeliveryRequestForm
from .models import DeliveryRequest


class DeliveryRequestTests(TestCase):
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
        self.other_courier = self.create_user(CustomUser.Role.COURIER, "two")
        self.admin = self.create_user(CustomUser.Role.ADMIN, "one")

    def test_delivery_form_validates_fee_and_distinct_locations(self):
        data = {
            "item_description": "Coffee",
            "pickup_location": "Main Canteen",
            "dropoff_location": "Library",
            "delivery_fee": "25.00",
            "notes": "",
        }
        self.assertTrue(DeliveryRequestForm(data=data).is_valid())

        data["delivery_fee"] = "0"
        self.assertIn("delivery_fee", DeliveryRequestForm(data=data).errors)
        data["delivery_fee"] = "25.00"
        data["dropoff_location"] = " main canteen "
        self.assertIn("__all__", DeliveryRequestForm(data=data).errors)

    def test_customer_can_create_request(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("deliveries:create_delivery"),
            {
                "item_description": "Coffee",
                "pickup_location": "Main Canteen",
                "dropoff_location": "Library",
                "delivery_fee": "25.00",
                "notes": "",
            },
        )

        delivery = DeliveryRequest.objects.get()
        self.assertEqual(delivery.customer, self.customer)
        self.assertEqual(delivery.status, DeliveryRequest.Status.PENDING)
        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
        )

    def test_my_deliveries_are_scoped_by_customer_and_courier(self):
        customer_delivery = self.create_delivery(self.customer)
        self.create_delivery(self.other_customer)
        assigned_delivery = self.create_delivery(
            self.other_customer,
            courier=self.courier,
            status=DeliveryRequest.Status.ACCEPTED,
        )

        self.client.force_login(self.customer)
        response = self.client.get(reverse("deliveries:my_deliveries"))
        self.assertEqual(list(response.context["deliveries"]), [customer_delivery])

        self.client.force_login(self.courier)
        response = self.client.get(reverse("deliveries:my_deliveries"))
        self.assertEqual(list(response.context["deliveries"]), [assigned_delivery])

    def test_customers_and_couriers_can_browse_other_open_deliveries(self):
        delivery = self.create_delivery(self.customer)
        own_delivery = self.create_delivery(self.courier)
        self.create_delivery(
            self.other_customer,
            status=DeliveryRequest.Status.ACCEPTED,
            courier=self.other_courier,
        )

        self.client.force_login(self.courier)
        response = self.client.get(reverse("deliveries:available_deliveries"))
        self.assertEqual(
            list(response.context["deliveries"]),
            [delivery],
        )
        self.assertContains(response, "Accept Job")

        self.client.force_login(self.customer)
        response = self.client.get(reverse("deliveries:available_deliveries"))
        self.assertEqual(
            list(response.context["deliveries"]),
            [own_delivery],
        )
        self.assertNotContains(response, "Accept Job")

        self.client.force_login(self.admin)
        response = self.client.get(reverse("deliveries:available_deliveries"))
        self.assertRedirects(
            response,
            reverse("deliveries:my_deliveries"),
            fetch_redirect_response=False,
        )

    def test_customer_can_view_another_customers_open_request_detail(self):
        delivery = self.create_delivery(self.customer)
        self.client.force_login(self.other_customer)

        response = self.client.get(
            reverse("deliveries:delivery_detail", args=[delivery.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, delivery.item_description)

    def test_courier_can_accept_pending_request(self):
        delivery = self.create_delivery(self.customer)
        self.client.force_login(self.courier)

        response = self.client.post(
            reverse("deliveries:accept_delivery", args=[delivery.pk])
        )

        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
        )
        delivery.refresh_from_db()
        self.assertEqual(delivery.courier, self.courier)
        self.assertEqual(delivery.status, DeliveryRequest.Status.ACCEPTED)

    def test_accept_form_works_with_csrf_checks_enabled(self):
        delivery = self.create_delivery(self.customer)
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(self.courier)
        url = reverse("deliveries:available_deliveries")

        page = client.get(url)
        self.assertEqual(page.status_code, 200)
        token = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"',
            page.content,
        ).group(1).decode()

        response = client.post(
            reverse("deliveries:accept_delivery", args=[delivery.pk]),
            {"csrfmiddlewaretoken": token},
        )

        self.assertEqual(response.status_code, 302)
        delivery.refresh_from_db()
        self.assertEqual(delivery.courier, self.courier)

    def test_only_first_courier_can_accept_a_request(self):
        delivery = self.create_delivery(self.customer)
        self.client.force_login(self.courier)
        self.client.post(reverse("deliveries:accept_delivery", args=[delivery.pk]))

        self.client.force_login(self.other_courier)
        response = self.client.post(
            reverse("deliveries:accept_delivery", args=[delivery.pk])
        )

        self.assertRedirects(
            response,
            reverse("deliveries:available_deliveries"),
            fetch_redirect_response=False,
        )
        delivery.refresh_from_db()
        self.assertEqual(delivery.courier, self.courier)

    def test_courier_cannot_accept_own_delivery(self):
        delivery = self.create_delivery(self.courier)
        self.client.force_login(self.courier)

        response = self.client.post(
            reverse("deliveries:accept_delivery", args=[delivery.pk])
        )

        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
            fetch_redirect_response=False,
        )
        delivery.refresh_from_db()
        self.assertIsNone(delivery.courier)
        self.assertEqual(delivery.status, DeliveryRequest.Status.PENDING)

    def test_accept_requires_post_and_courier_role(self):
        delivery = self.create_delivery(self.customer)
        self.client.force_login(self.courier)
        response = self.client.get(
            reverse("deliveries:accept_delivery", args=[delivery.pk])
        )
        self.assertEqual(response.status_code, 405)

        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("deliveries:accept_delivery", args=[delivery.pk])
        )
        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
            fetch_redirect_response=False,
        )
        delivery.refresh_from_db()
        self.assertIsNone(delivery.courier)

    def test_assigned_courier_can_advance_only_valid_statuses(self):
        delivery = self.create_delivery(
            self.customer,
            courier=self.courier,
            status=DeliveryRequest.Status.ACCEPTED,
        )
        self.client.force_login(self.courier)
        url = reverse("deliveries:update_delivery_status", args=[delivery.pk])

        response = self.client.post(url, {"status": DeliveryRequest.Status.DELIVERED})
        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
        )
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, DeliveryRequest.Status.ACCEPTED)

        response = self.client.post(url, {"status": DeliveryRequest.Status.IN_TRANSIT})
        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
        )
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, DeliveryRequest.Status.IN_TRANSIT)

        response = self.client.post(url, {"status": DeliveryRequest.Status.DELIVERED})
        self.assertRedirects(
            response,
            reverse("deliveries:delivery_detail", args=[delivery.pk]),
        )
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, DeliveryRequest.Status.DELIVERED)

    def test_unassigned_courier_cannot_update_delivery(self):
        delivery = self.create_delivery(
            self.customer,
            courier=self.courier,
            status=DeliveryRequest.Status.ACCEPTED,
        )
        self.client.force_login(self.other_courier)

        response = self.client.post(
            reverse("deliveries:update_delivery_status", args=[delivery.pk]),
            {"status": DeliveryRequest.Status.IN_TRANSIT},
        )

        self.assertEqual(response.status_code, 404)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, DeliveryRequest.Status.ACCEPTED)
