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
        form = CampusRegistrationForm(
            data=self.registration_data(
                email="  STUDENT@Example.edu  ",
                student_id="  2023-12345  ",
                contact_number="  09171234567  ",
            )
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.role, CustomUser.Role.CUSTOMER)
        self.assertFalse(user.is_verified_student)
        self.assertEqual(user.email, "student@example.edu")
        self.assertEqual(user.student_id, "2023-12345")
        self.assertEqual(user.contact_number, "09171234567")

    def test_display_name_uses_full_name_or_username(self):
        named_user = CustomUser(
            username="student",
            first_name="Campus",
            last_name="Student",
        )
        unnamed_user = CustomUser(username="campus-user")

        self.assertEqual(named_user.display_name, "Campus Student")
        self.assertEqual(unnamed_user.display_name, "campus-user")

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
    def create_user(self, role, suffix=""):
        username = f"user-{role.lower()}{suffix}"
        return CustomUser.objects.create_user(
            username=username,
            email=f"{username}@example.edu",
            password="a-strong-password-123",
            role=role,
            student_id=f"id-{role.lower()}{suffix}",
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
        verified = self.create_user(CustomUser.Role.COURIER)
        verified.is_verified_student = True
        verified.save(update_fields=["is_verified_student"])
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertContains(response, pending.student_id)
        self.assertNotContains(response, admin.student_id)
        self.assertContains(response, reverse("verify_student", args=[pending.pk]))
        self.assertEqual(response.context["total_students"], 2)
        self.assertEqual(response.context["verified_count"], 1)

    def test_admin_cannot_verify_another_admin_account(self):
        admin = self.create_user(CustomUser.Role.ADMIN)
        other_admin = self.create_user(CustomUser.Role.ADMIN, suffix="-other")
        self.client.force_login(admin)

        response = self.client.post(
            reverse("verify_student", args=[other_admin.pk])
        )

        self.assertEqual(response.status_code, 404)
        other_admin.refresh_from_db()
        self.assertFalse(other_admin.is_verified_student)

    def test_admin_can_verify_student_with_post(self):
        admin = self.create_user(CustomUser.Role.ADMIN)
        student = self.create_user(CustomUser.Role.CUSTOMER)
        self.client.force_login(admin)

        response = self.client.post(reverse("verify_student", args=[student.pk]))

        self.assertRedirects(response, reverse("admin_dashboard"))
        student.refresh_from_db()
        self.assertTrue(student.is_verified_student)

    def test_verification_action_rejects_get(self):
        admin = self.create_user(CustomUser.Role.ADMIN)
        student = self.create_user(CustomUser.Role.CUSTOMER)
        self.client.force_login(admin)

        response = self.client.get(reverse("verify_student", args=[student.pk]))

        self.assertEqual(response.status_code, 405)
        student.refresh_from_db()
        self.assertFalse(student.is_verified_student)

    def test_non_admin_cannot_verify_student(self):
        customer = self.create_user(CustomUser.Role.CUSTOMER)
        student = self.create_user(CustomUser.Role.COURIER)
        self.client.force_login(customer)

        response = self.client.post(reverse("verify_student", args=[student.pk]))

        self.assertRedirects(
            response,
            reverse("dashboard_redirect"),
            fetch_redirect_response=False,
        )
        student.refresh_from_db()
        self.assertFalse(student.is_verified_student)
