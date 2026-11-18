from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import CustomUser

from .forms import DeliveryRequestForm
from .models import DeliveryRequest


@login_required
def my_deliveries(request):
    if request.user.role == CustomUser.Role.CUSTOMER:
        deliveries = DeliveryRequest.objects.filter(customer=request.user)
    elif request.user.role == CustomUser.Role.COURIER:
        deliveries = DeliveryRequest.objects.filter(courier=request.user)
    else:
        deliveries = DeliveryRequest.objects.all()
    return render(request, "deliveries/request_list.html", {"deliveries": deliveries})


@login_required
def create_delivery(request):
    if request.user.role != CustomUser.Role.CUSTOMER:
        messages.error(request, "Only Student Customers can create delivery requests.")
        return redirect("deliveries:my_deliveries")

    if request.method == "POST":
        form = DeliveryRequestForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.customer = request.user
            delivery.save()
            messages.success(request, "Delivery request posted successfully!")
            return redirect("deliveries:delivery_detail", pk=delivery.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = DeliveryRequestForm()

    return render(
        request,
        "deliveries/request_form.html",
        {
            "form": form,
            "page_title": "Create Delivery Request",
            "submit_label": "Post Request",
        },
    )


@login_required
def delivery_detail(request, pk):
    delivery = get_object_or_404(DeliveryRequest, pk=pk)
    is_owner = delivery.customer_id == request.user.pk
    is_assigned_courier = delivery.courier_id == request.user.pk
    is_open_for_courier = (
        request.user.role == CustomUser.Role.COURIER
        and delivery.status == DeliveryRequest.Status.PENDING
    )
    is_open_for_customer = (
        request.user.role == CustomUser.Role.CUSTOMER
        and delivery.status == DeliveryRequest.Status.PENDING
        and delivery.courier_id is None
    )
    is_admin = (
        request.user.role == CustomUser.Role.ADMIN or request.user.is_superuser
    )
    if not (
        is_owner
        or is_assigned_courier
        or is_open_for_courier
        or is_open_for_customer
        or is_admin
    ):
        messages.error(request, "You do not have permission to view this delivery request.")
        return redirect("deliveries:my_deliveries")
    return render(request, "deliveries/request_detail.html", {"delivery": delivery})


@login_required
def edit_delivery(request, pk):
    delivery = get_object_or_404(DeliveryRequest, pk=pk, customer=request.user)
    if delivery.status != DeliveryRequest.Status.PENDING:
        messages.error(
            request,
            "You can only edit a delivery request while it is still Pending.",
        )
        return redirect("deliveries:delivery_detail", pk=delivery.pk)

    if request.method == "POST":
        form = DeliveryRequestForm(request.POST, instance=delivery)
        if form.is_valid():
            form.save()
            messages.success(request, "Delivery request updated successfully.")
            return redirect("deliveries:delivery_detail", pk=delivery.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = DeliveryRequestForm(instance=delivery)
    return render(
        request,
        "deliveries/request_form.html",
        {
            "form": form,
            "delivery": delivery,
            "page_title": f"Edit Delivery #{delivery.id}",
            "submit_label": "Save Changes",
        },
    )


@login_required
def delete_delivery(request, pk):
    delivery = get_object_or_404(DeliveryRequest, pk=pk, customer=request.user)
    if delivery.status != DeliveryRequest.Status.PENDING:
        messages.error(
            request,
            "You can only delete a delivery request while it is still Pending.",
        )
        return redirect("deliveries:delivery_detail", pk=delivery.pk)
    if request.method == "POST":
        delivery.delete()
        messages.success(request, "Delivery request deleted.")
        return redirect("deliveries:my_deliveries")
    return render(
        request,
        "deliveries/request_confirm_delete.html",
        {"delivery": delivery},
    )


@login_required
def available_deliveries(request):
    if request.user.role not in (
        CustomUser.Role.CUSTOMER,
        CustomUser.Role.COURIER,
    ):
        messages.error(
            request,
            "Only Student Customers and Couriers can browse open requests.",
        )
        return redirect("deliveries:my_deliveries")
    open_requests = DeliveryRequest.objects.filter(
        status=DeliveryRequest.Status.PENDING,
        courier__isnull=True,
    ).exclude(customer=request.user)
    return render(
        request,
        "deliveries/available_deliveries.html",
        {"deliveries": open_requests},
    )


@login_required
@require_POST
def accept_delivery(request, pk):
    if request.user.role != CustomUser.Role.COURIER:
        messages.error(request, "Only Student Couriers can accept deliveries.")
        return redirect("deliveries:delivery_detail", pk=pk)

    delivery = get_object_or_404(DeliveryRequest, pk=pk)
    if delivery.customer_id == request.user.pk:
        messages.error(request, "You cannot accept your own delivery request.")
        return redirect("deliveries:delivery_detail", pk=pk)

    claimed = DeliveryRequest.objects.filter(
        pk=pk,
        status=DeliveryRequest.Status.PENDING,
        courier__isnull=True,
    ).update(
        courier=request.user,
        status=DeliveryRequest.Status.ACCEPTED,
        updated_at=timezone.now(),
    )
    if not claimed:
        messages.error(request, "This delivery request is no longer available.")
        return redirect("deliveries:available_deliveries")

    messages.success(request, f"You accepted Delivery #{delivery.id}!")
    return redirect("deliveries:delivery_detail", pk=delivery.pk)


@login_required
@require_POST
def update_delivery_status(request, pk):
    if request.user.role != CustomUser.Role.COURIER:
        messages.error(request, "Only Student Couriers can update delivery status.")
        return redirect("deliveries:my_deliveries")

    delivery = get_object_or_404(DeliveryRequest, pk=pk, courier=request.user)
    new_status = request.POST.get("status")
    valid_transitions = {
        DeliveryRequest.Status.ACCEPTED: DeliveryRequest.Status.IN_TRANSIT,
        DeliveryRequest.Status.IN_TRANSIT: DeliveryRequest.Status.DELIVERED,
    }

    if valid_transitions.get(delivery.status) != new_status:
        messages.error(request, "Invalid status transition.")
        return redirect("deliveries:delivery_detail", pk=delivery.pk)

    updated = DeliveryRequest.objects.filter(
        pk=delivery.pk,
        courier=request.user,
        status=delivery.status,
    ).update(status=new_status, updated_at=timezone.now())
    if updated:
        delivery.status = new_status
        messages.success(
            request,
            f"Delivery #{delivery.id} marked as {delivery.get_status_display()}.",
        )
    else:
        messages.error(request, "Invalid status transition.")
    return redirect("deliveries:delivery_detail", pk=delivery.pk)
