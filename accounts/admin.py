from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "student_id",
        "email",
        "role",
        "is_verified_student",
        "is_staff",
    )
    list_filter = ("role", "is_verified_student", "is_staff")
    search_fields = ("username", "student_id", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        (
            "CampusCourier profile",
            {
                "fields": (
                    "student_id",
                    "contact_number",
                    "campus_building_or_dept",
                    "role",
                    "is_verified_student",
                    "profile_photo",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "CampusCourier profile",
            {
                "fields": (
                    "email",
                    "student_id",
                    "contact_number",
                    "campus_building_or_dept",
                    "role",
                    "is_verified_student",
                )
            },
        ),
    )
