from django.urls import path

from . import views

urlpatterns = [
    path("bookings/", views.BookingListCreateView.as_view(), name="booking-list-create"),
    path("bookings/my/", views.BookingListCreateView.as_view(), name="my-bookings"),
    path("bookings/point/", views.PointBookingsView.as_view(), name="point-bookings"),
    path("bookings/<int:pk>/confirm/", views.BookingConfirmView.as_view(), name="booking-confirm"),
    path("bookings/<int:pk>/reject/", views.BookingRejectView.as_view(), name="booking-reject"),
]