from django.test import TestCase
from django.urls import reverse

from .forms import CampusRegistrationForm
from .models import CustomUser


class CampusRegistrationFormTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            "username": "student",
            "student_id": "2023-12345",
            "first_name": "Campus",
            "last_name": "Student",
            "email": "student@example.edu",
            "contact_number": "09171234567",
            "campus_building_or_dept": "Engineering",
            "role": CustomUser.Role.CUSTOMER,
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
        }
        data.update(overrides)
        return data

    def test_public_registration_creates_unverified_student(self):
        form = CampusRegistrationForm(data=self.registration_data())

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.role, CustomUser.Role.CUSTOMER)
        self.assertFalse(user.is_verified_student)

    def test_public_registration_cannot_select_admin(self):
        form = CampusRegistrationForm(
            data=self.registration_data(role=CustomUser.Role.ADMIN)
        )

        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)

    def test_superuser_is_created_as_verified_admin(self):
        user = CustomUser.objects.create_superuser(
            username="campus-admin",
            email="admin@example.edu",
            password="a-strong-password-123",
            student_id="admin-001",
            contact_number="09170000000",
        )

        self.assertEqual(user.role, CustomUser.Role.ADMIN)
        self.assertTrue(user.is_verified_student)


class RoleDashboardTests(TestCase):
    def create_user(self, role):
        return CustomUser.objects.create_user(
            username=f"user-{role.lower()}",
            email=f"{role.lower()}@example.edu",
            password="a-strong-password-123",
            role=role,
            student_id=f"id-{role.lower()}",
            contact_number="09171234567",
        )

    def test_customer_cannot_open_courier_dashboard(self):
        user = self.create_user(CustomUser.Role.CUSTOMER)
        self.client.force_login(user)

        response = self.client.get(reverse("courier_dashboard"))

        self.assertRedirects(
            response,
            reverse("dashboard_redirect"),
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            self.client.get(response.url),
            reverse("customer_dashboard"),
        )
        self.assertEqual(len(list(response.wsgi_request._messages)), 1)

    def test_dashboard_redirect_uses_user_role(self):
        user = self.create_user(CustomUser.Role.COURIER)
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard_redirect"))

        self.assertRedirects(response, reverse("courier_dashboard"))

    def test_home_redirects_to_login_for_anonymous_visitors(self):
        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("login"))

    def test_admin_dashboard_lists_unverified_students(self):
        admin = self.create_user(CustomUser.Role.ADMIN)
        pending = self.create_user(CustomUser.Role.CUSTOMER)
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertContains(response, pending.student_id)
        self.assertNotContains(response, admin.student_id)
