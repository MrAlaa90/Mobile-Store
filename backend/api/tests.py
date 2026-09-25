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
        self.user_a.licenses.all().delete()
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

    def test_store_registration_auto_provisions_20_day_trial(self):
        signup_data = {
            'store_name': 'New Star Mobile',
            'username': 'newstar',
            'password': 'secretpassword123',
            'phone': '01123456789',
            'email': 'newstar@example.com',
        }
        response = self.client.post(reverse('store_register'), signup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('license', response.data)
        self.assertEqual(response.data['license']['type'], 'trial')
        self.assertEqual(response.data['license']['days_remaining'], 20)
        self.assertEqual(response.data['license']['max_devices'], 3)

        # Verify user in DB has store_name
        new_user = User.objects.get(username='newstar')
        self.assertEqual(new_user.store_name, 'New Star Mobile')
        self.assertTrue(new_user.licenses.filter(type='trial', status='active').exists())

    def test_max_devices_limit_enforced(self):
        self.client.force_authenticate(user=self.user_a)
        # License A has max_devices = 3 (default)
        self.license_a.max_devices = 2
        self.license_a.save()

        # Connect Device 1 -> OK
        resp1 = self.client.get(reverse('license_check'), {'hardware_id': 'hw-device-01'})
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Connect Device 2 -> OK
        resp2 = self.client.get(reverse('license_check'), {'hardware_id': 'hw-device-02'})
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

        # Connect Device 3 -> Should exceed max_devices (2) -> 403 Forbidden!
        resp3 = self.client.get(reverse('license_check'), {'hardware_id': 'hw-device-03'})
        self.assertEqual(resp3.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp3.data.get('error'), 'max_devices_exceeded')

    def test_cross_tenant_sale_rejected(self):
        # Store A creates inventory item
        item_a = Inventory.objects.create(
            user=self.user_a,
            name='iPad Air',
            brand='Apple',
            model='Air 5',
            purchase_price='500.00',
            sale_price='650.00',
            status='available',
        )

        # Store B tries to sell Store A's item!
        self.client.force_authenticate(user=self.user_b)
        response = self.client.post(reverse('sale-list'), {
            'item': item_a.id,
            'sale_price': '650.00'
        }, format='json')
        # Should be rejected with validation error!
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('item', response.data)

