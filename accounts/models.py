from django.contrib.auth.models import UserManager, AbstractUser
from django.db import models


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)
        extra_fields.setdefault("is_verified_student", True)
        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Student Customer"
        COURIER = "COURIER", "Student Courier"
        ADMIN = "ADMIN", "Campus Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    student_id = models.CharField(max_length=20, unique=True)
    contact_number = models.CharField(max_length=15)
    campus_building_or_dept = models.CharField(max_length=100, blank=True)
    is_verified_student = models.BooleanField(default=False)
    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True,
    )

    objects = CustomUserManager()

    REQUIRED_FIELDS = ["email", "student_id", "contact_number"]

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "Campus User"
        verbose_name_plural = "Campus Users"

    @property
    def display_name(self):
        full_name = self.get_full_name().strip()
        return full_name or self.username

    def __str__(self):
        return f"{self.display_name} ({self.student_id}) - {self.get_role_display()}"
