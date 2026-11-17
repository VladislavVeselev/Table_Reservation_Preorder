from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Network, Point, Table
from accounts.models import Profile

class PointListTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="guest", password="pass12345")
        self.network = Network.objects.create(name="Культурно коротко")
        self.active = Point.objects.create(
            network=self.network, name="Кафе на Ленина",
            address="ул. Ленина, 1", is_active=True,
        )
        self.inactive = Point.objects.create(
            network=self.network, name="Закрытое кафе",
            address="ул. Мира, 2", is_active=False,
        )

    def test_requires_auth(self):
        r = self.client.get("/api/points/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_returns_only_active(self):
        self.client.force_authenticate(self.user)
        r = self.client.get("/api/points/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = [p["id"] for p in r.data]
        self.assertIn(self.active.id, ids)
        self.assertNotIn(self.inactive.id, ids)

    def test_empty_list(self):
        Point.objects.all().delete()
        self.client.force_authenticate(self.user)
        r = self.client.get("/api/points/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, [])

class MyPointTablesTests(APITestCase):
    def setUp(self):
        from datetime import date, time, timedelta
        from bookings.models import Booking

        self.net = Network.objects.create(name="N")
        self.point = Point.objects.create(
            network=self.net, name="P", address="a", is_active=True
        )
        self.other_point = Point.objects.create(
            network=self.net, name="P2", address="b", is_active=True
        )
        self.t1 = Table.objects.create(point=self.point, name="Стол 1", seats=2)
        self.t2 = Table.objects.create(point=self.point, name="Стол 2", seats=4)
        self.t_other = Table.objects.create(point=self.other_point, name="Чужой", seats=2)

        self.guest = User.objects.create_user(username="g", password="p")
        Profile.objects.create(user=self.guest)

        self.admin = User.objects.create_user(username="a", password="p")
        Profile.objects.create(
            user=self.admin, role=Profile.ROLE_POINT_ADMIN, point=self.point
        )

        self.admin_no_point = User.objects.create_user(username="a2", password="p")
        Profile.objects.create(user=self.admin_no_point, role=Profile.ROLE_POINT_ADMIN)

        self.tomorrow = date.today() + timedelta(days=1)
        Booking.objects.create(
            user=self.guest, point=self.point, table=self.t1,
            date=self.tomorrow, start_time=time(18, 0), end_time=time(19, 0),
            status=Booking.STATUS_PENDING,
        )

    def test_guest_forbidden(self):
        self.client.force_authenticate(self.guest)
        r = self.client.get("/api/points/my/tables/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_without_point_forbidden(self):
        self.client.force_authenticate(self.admin_no_point)
        r = self.client.get("/api/points/my/tables/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_sees_only_own_point_tables(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get(
            f"/api/points/my/tables/?date={self.tomorrow}&time=18:00"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = [t["id"] for t in r.data]
        self.assertIn(self.t1.id, ids)
        self.assertIn(self.t2.id, ids)
        self.assertNotIn(self.t_other.id, ids)

    def test_busy_table_has_booking_info(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get(
            f"/api/points/my/tables/?date={self.tomorrow}&time=18:00"
        )
        by_id = {t["id"]: t for t in r.data}
        busy = by_id[self.t1.id]
        self.assertFalse(busy["is_available"])
        self.assertEqual(busy["busy_booking"]["user_username"], "g")
        self.assertEqual(busy["busy_booking"]["start_time"], "18:00")

    def test_free_table_has_no_booking(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get(
            f"/api/points/my/tables/?date={self.tomorrow}&time=18:00"
        )
        by_id = {t["id"]: t for t in r.data}
        free = by_id[self.t2.id]
        self.assertTrue(free["is_available"])
        self.assertIsNone(free["busy_booking"])

    def test_rejected_booking_does_not_block(self):
        from datetime import time
        from bookings.models import Booking
        Booking.objects.filter(table=self.t1).update(status=Booking.STATUS_REJECTED)
        self.client.force_authenticate(self.admin)
        r = self.client.get(
            f"/api/points/my/tables/?date={self.tomorrow}&time=18:00"
        )
        by_id = {t["id"]: t for t in r.data}
        self.assertTrue(by_id[self.t1.id]["is_available"])