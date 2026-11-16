from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CampusRegistrationForm(UserCreationForm):
    PUBLIC_ROLES = [
        (CustomUser.Role.CUSTOMER, "Student Customer (Request Deliveries)"),
        (CustomUser.Role.COURIER, "Student Courier (Accept & Deliver Tasks)"),
    ]

    email = forms.EmailField(
        required=True,
        help_text="Use your university email if available.",
    )
    role = forms.ChoiceField(choices=PUBLIC_ROLES, label="Account Role")

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "student_id",
            "first_name",
            "last_name",
            "email",
            "contact_number",
            "campus_building_or_dept",
            "role",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if CustomUser.objects.filter(student_id__iexact=student_id).exists():
            raise forms.ValidationError("This Student ID is already registered.")
        return student_id

    def clean_contact_number(self):
        return self.cleaned_data["contact_number"].strip()


class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "contact_number",
            "campus_building_or_dept",
            "profile_photo",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            CustomUser.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("This email is already used by another student.")
        return email

    def clean_contact_number(self):
        return self.cleaned_data["contact_number"].strip()
