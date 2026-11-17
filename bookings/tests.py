from datetime import date, time, timedelta

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import Profile
from points.models import Network, Point, Table

from .models import Booking


class BookingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="g", password="p")
        Profile.objects.create(user=self.user)
        self.other = User.objects.create_user(username="g2", password="p")
        Profile.objects.create(user=self.other)
        self.net = Network.objects.create(name="N")
        self.point = Point.objects.create(
            network=self.net, name="P", address="a", is_active=True
        )
        self.table = Table.objects.create(point=self.point, name="Стол 1", seats=2)
        self.tomorrow = date.today() + timedelta(days=1)
        self.client.force_authenticate(self.user)

    def test_create_booking_ok(self):
        r = self.client.post("/api/bookings/", {
            "point": self.point.id, "table": self.table.id,
            "date": str(self.tomorrow), "time": "18:00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["status"], "pending")
        self.assertEqual(r.data["start_time"], "18:00:00")
        self.assertEqual(r.data["end_time"], "19:00:00")

    def test_conflict_returns_409(self):
        Booking.objects.create(
            user=self.user, point=self.point, table=self.table,
            date=self.tomorrow, start_time=time(18, 0), end_time=time(19, 0),
            status=Booking.STATUS_CONFIRMED,
        )
        r = self.client.post("/api/bookings/", {
            "point": self.point.id, "table": self.table.id,
            "date": str(self.tomorrow), "time": "18:00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Booking.objects.count(), 1)

    def test_adjacent_booking_ok(self):
        Booking.objects.create(
            user=self.user, point=self.point, table=self.table,
            date=self.tomorrow, start_time=time(18, 0), end_time=time(19, 0),
        )
        r = self.client.post("/api/bookings/", {
            "point": self.point.id, "table": self.table.id,
            "date": str(self.tomorrow), "time": "19:00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_past_date_rejected(self):
        yesterday = date.today() - timedelta(days=1)
        r = self.client.post("/api/bookings/", {
            "point": self.point.id, "table": self.table.id,
            "date": str(yesterday), "time": "18:00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_out_of_hours_rejected(self):
        r = self.client.post("/api/bookings/", {
            "point": self.point.id, "table": self.table.id,
            "date": str(self.tomorrow), "time": "23:00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_bookings_only_mine(self):
        Booking.objects.create(
            user=self.user, point=self.point, table=self.table,
            date=self.tomorrow, start_time=time(18, 0), end_time=time(19, 0),
        )
        Booking.objects.create(
            user=self.other, point=self.point, table=self.table,
            date=self.tomorrow, start_time=time(20, 0), end_time=time(21, 0),
        )
        r = self.client.get("/api/bookings/my/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["start_time"], "18:00:00")


class PointTablesTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="g", password="p")
        Profile.objects.create(user=self.user)
        self.net = Network.objects.create(name="N")
        self.point = Point.objects.create(
            network=self.net, name="P", address="a", is_active=True
        )
        self.t1 = Table.objects.create(point=self.point, name="T1", seats=2)
        self.t2 = Table.objects.create(point=self.point, name="T2", seats=4)
        self.client.force_authenticate(self.user)
        self.tomorrow = date.today() + timedelta(days=1)

    def test_tables_list_marks_busy(self):
        Booking.objects.create(
            user=self.user, point=self.point, table=self.t1,
            date=self.tomorrow, start_time=time(18, 0), end_time=time(19, 0),
        )
        r = self.client.get(
            f"/api/points/{self.point.id}/tables/?date={self.tomorrow}&time=18:00"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        by_id = {t["id"]: t for t in r.data}
        self.assertFalse(by_id[self.t1.id]["is_available"])
        self.assertTrue(by_id[self.t2.id]["is_available"])


class AdminBookingTests(APITestCase):
    def setUp(self):
        self.net = Network.objects.create(name="N")
        self.point = Point.objects.create(
            network=self.net, name="P", address="a", is_active=True
        )
        self.other_point = Point.objects.create(
            network=self.net, name="P2", address="b", is_active=True
        )
        self.table = Table.objects.create(point=self.point, name="T1", seats=2)
        self.guest = User.objects.create_user(username="g", password="p")
        Profile.objects.create(user=self.guest)
        self.admin = User.objects.create_user(username="a", password="p")
        Profile.objects.create(
            user=self.admin, role=Profile.ROLE_POINT_ADMIN, point=self.point
        )
        self.other_admin = User.objects.create_user(username="a2", password="p")
        Profile.objects.create(
            user=self.other_admin, role=Profile.ROLE_POINT_ADMIN, point=self.other_point
        )
        self.tomorrow = date.today() + timedelta(days=1)
        self.booking = Booking.objects.create(
            user=self.guest, point=self.point, table=self.table,
            date=self.tomorrow, start_time=time(18, 0), end_time=time(19, 0),
            status=Booking.STATUS_PENDING,
        )

    def test_admin_sees_only_own_point_bookings(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/bookings/point/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["id"], self.booking.id)

    def test_other_admin_sees_nothing(self):
        self.client.force_authenticate(self.other_admin)
        r = self.client.get("/api/bookings/point/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 0)

    def test_guest_forbidden(self):
        self.client.force_authenticate(self.guest)
        r = self.client.get("/api/bookings/point/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_changes_status(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post(f"/api/bookings/{self.booking.id}/confirm/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CONFIRMED)

    def test_reject_changes_status(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post(f"/api/bookings/{self.booking.id}/reject/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_REJECTED)

    def test_other_admin_cannot_confirm(self):
        self.client.force_authenticate(self.other_admin)
        r = self.client.post(f"/api/bookings/{self.booking.id}/confirm/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_rejected_frees_table(self):
        # отклоняем первую бронь и создаём вторую на то же время
        self.booking.status = Booking.STATUS_REJECTED
        self.booking.save()
        self.client.force_authenticate(self.guest)
        r = self.client.post("/api/bookings/", {
            "point": self.point.id, "table": self.table.id,
            "date": str(self.tomorrow), "time": "18:00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)