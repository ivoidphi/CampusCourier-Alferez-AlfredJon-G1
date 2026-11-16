from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CampusRegistrationForm, StudentProfileUpdateForm
from .models import CustomUser


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    "Access denied: you cannot access another role's dashboard.",
                )
                return redirect("dashboard_redirect")
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")

    if request.method == "POST":
        form = CampusRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "CampusCourier account created! Please log in.")
            return redirect("login")
        messages.error(request, "Registration failed. Please fix the errors below.")
    else:
        form = CampusRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")
    return redirect("login")


@login_required
def dashboard_redirect_view(request):
    if request.user.role == CustomUser.Role.ADMIN:
        return redirect("admin_dashboard")
    if request.user.role == CustomUser.Role.COURIER:
        return redirect("courier_dashboard")
    return redirect("customer_dashboard")


@role_required(CustomUser.Role.CUSTOMER)
def customer_dashboard_view(request):
    return render(request, "accounts/customer_dashboard.html")


@role_required(CustomUser.Role.COURIER)
def courier_dashboard_view(request):
    return render(request, "accounts/courier_dashboard.html")


@role_required(CustomUser.Role.ADMIN)
def admin_dashboard_view(request):
    pending_students = (
        CustomUser.objects.filter(is_verified_student=False)
        .exclude(role=CustomUser.Role.ADMIN)
        .order_by("date_joined")
    )
    return render(
        request,
        "accounts/admin_dashboard.html",
        {"pending_students": pending_students},
    )


@role_required(CustomUser.Role.ADMIN)
@require_POST
def verify_student_view(request, user_id):
    student = get_object_or_404(
        CustomUser.objects.filter(
            role__in=(CustomUser.Role.CUSTOMER, CustomUser.Role.COURIER)
        ),
        pk=user_id,
    )
    student.is_verified_student = True
    student.save(update_fields=["is_verified_student"])
    messages.success(
        request,
        f"{student.username} ({student.student_id}) has been verified.",
    )
    return redirect("admin_dashboard")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = StudentProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Student profile updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = StudentProfileUpdateForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
