from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Customer, Device, Inventory, License, Repair, Sale, User


class MobileStoreApiTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username='store_a',
            password='password123',
            email='store_a@example.com',
            name='Store A Owner',
            role='admin',
        )
        self.user_b = User.objects.create_user(
            username='store_b',
            password='password123',
            email='store_b@example.com',
            name='Store B Owner',
            role='user',
        )

        today = timezone.localdate()
        self.license_a = License.objects.create(
            user=self.user_a,
            license_key='MS-TEST-KEY-2026',
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=30),
            type='paid',
            status='active',
        )

    def test_login_returns_jwt_tokens(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'store_a', 'password': 'password123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_inventory_requires_authentication(self):
        response = self.client.get(reverse('inventory-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tenant_data_isolation(self):
        # Store A creates inventory item
        Inventory.objects.create(
            user=self.user_a,
            name='iPhone 15',
            brand='Apple',
            model='15 Pro',
            purchase_price='800.00',
            sale_price='999.00',
            status='available',
        )

        # Store B should NOT see Store A's inventory
        self.client.force_authenticate(user=self.user_b)
        response_b = self.client.get(reverse('inventory-list'))
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_b.data), 0)

        # Store A SHOULD see its own inventory
        self.client.force_authenticate(user=self.user_a)
        response_a = self.client.get(reverse('inventory-list'))
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_a.data), 1)
        self.assertEqual(response_a.data[0]['name'], 'iPhone 15')

    def test_sale_creation_updates_inventory_and_profit(self):
        self.client.force_authenticate(user=self.user_a)

        item = Inventory.objects.create(
            user=self.user_a,
            name='Galaxy S24',
            brand='Samsung',
            model='S24 Ultra',
            purchase_price='700.00',
            sale_price='950.00',
            status='available',
        )
        customer = Customer.objects.create(
            user=self.user_a,
            name='Ahmed Ali',
            phone='01012345678',
            email='ahmed@example.com',
        )

        sale_data = {
            'item': item.id,
            'customer': customer.id,
            'sale_price': '950.00',
        }
        response = self.client.post(reverse('sale-list'), sale_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check profit calculated: 950 - 700 = 250
        self.assertEqual(float(response.data['profit']), 250.0)

        # Check inventory item status is now 'sold'
        item.refresh_from_db()
        self.assertEqual(item.status, 'sold')

    def test_license_check_and_device_binding(self):
        self.client.force_authenticate(user=self.user_a)
        hw_id = 'test-machine-hardware-hash-999'

        # First check binds the hardware to active license
        response = self.client.get(reverse('license_check'), {'hardware_id': hw_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['license_key'], self.license_a.license_key)

        # Device should now exist in database
        device = Device.objects.filter(user=self.user_a, hardware_id=hw_id).first()
        self.assertIsNotNone(device)
        self.assertEqual(device.license, self.license_a)

    def test_offline_token_generation(self):
        self.client.force_authenticate(user=self.user_a)
        hw_id = 'test-machine-offline-hash-888'

        response = self.client.post(reverse('offline_token'), {'hardware_id': hw_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payload', response.data)
        self.assertIn('signature', response.data)
        self.assertEqual(response.data['payload']['hardware_id'], hw_id)
        self.assertEqual(response.data['payload']['license_key'], self.license_a.license_key)
