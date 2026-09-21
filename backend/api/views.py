import base64
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Customer, Device, Inventory, License, Repair, Sale, Token
from .serializers import (
    CustomerSerializer,
    DeviceSerializer,
    InventorySerializer,
    LicenseSerializer,
    RepairSerializer,
    SaleSerializer,
)


class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InventoryViewSet(ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Inventory.objects.filter(user=self.request.user).order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HealthCheckView(APIView):
    """Lightweight endpoint to ping server availability without requiring authentication."""
    permission_classes = []

    def get(self, request):
        return Response({
            'status': 'ok',
            'server_time': timezone.now().isoformat(),
            'service': 'Mobile-Store API',
            'version': '1.0.0'
        })


class SaleViewSet(ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Sale.objects.filter(user=self.request.user).order_by('-date')

    def create(self, request, *args, **kwargs):
        invoice_id = request.data.get('invoice_id')
        if invoice_id:
            existing = Sale.objects.filter(user=request.user, invoice_id=invoice_id).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RepairViewSet(ModelViewSet):
    serializer_class = RepairSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repair.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeviceViewSet(ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user).order_by('-created_at')


class LicenseCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        hardware_id = request.query_params.get('hardware_id')
        today = timezone.localdate()

        licenses = License.objects.filter(
            user=user,
            status='active',
            start_date__lte=today,
            end_date__gte=today,
        )

        if hardware_id:
            device = Device.objects.filter(user=user, hardware_id=hardware_id).first()
            if device:
                if device.license and device.license.status == 'active':
                    licenses = licenses.filter(id=device.license_id)
                elif not device.license and licenses.exists():
                    # Bind existing device to available active license
                    active_license = licenses.first()
                    device.license = active_license
                    device.save(update_fields=['license'])
                    licenses = licenses.filter(id=active_license.id)
                else:
                    licenses = License.objects.none()
            else:
                # Register new device for user and bind to first active license if available
                active_license = licenses.first()
                if active_license:
                    Device.objects.create(
                        user=user,
                        hardware_id=hardware_id,
                        license=active_license,
                        name=f"Terminal-{hardware_id[:8]}"
                    )
                    licenses = licenses.filter(id=active_license.id)
                else:
                    licenses = License.objects.none()

        serializer = LicenseSerializer(licenses, many=True)
        return Response(serializer.data)


class OfflineTokenView(APIView):
    """Generates an RSA-signed offline license token with a 7-day grace period."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        hardware_id = request.data.get('hardware_id')
        if not hardware_id:
            return Response({'error': 'hardware_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.localdate()
        licenses = License.objects.filter(
            user=user,
            status='active',
            start_date__lte=today,
            end_date__gte=today,
        )

        device = Device.objects.filter(user=user, hardware_id=hardware_id).first()
        if not device:
            active_license = licenses.first()
            if not active_license:
                return Response({'error': 'No active license available to bind this device'}, status=status.HTTP_403_FORBIDDEN)
            device = Device.objects.create(
                user=user,
                hardware_id=hardware_id,
                license=active_license,
                name=f"Terminal-{hardware_id[:8]}"
            )

        if not device.license or device.license.status != 'active':
            return Response({'error': 'Device does not have an active license'}, status=status.HTTP_403_FORBIDDEN)

        # 7-day grace period for offline operation
        expires_at = timezone.now() + timedelta(days=7)
        payload = {
            'hardware_id': hardware_id,
            'username': user.username,
            'license_key': device.license.license_key,
            'issued_at': timezone.now().isoformat(),
            'expires_at': expires_at.isoformat(),
        }

        key_path = Path(settings.BASE_DIR) / 'keys' / 'private_key.pem'
        if not key_path.exists():
            example_key_path = Path(settings.BASE_DIR) / 'keys' / 'private_key.pem.example'
            if example_key_path.exists():
                key_path = example_key_path
            else:
                return Response({'error': 'Server signing key not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with open(key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = private_key.sign(
            payload_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        signature_b64 = base64.b64encode(signature).decode('utf-8')

        Token.objects.update_or_create(
            device=device,
            defaults={
                'token_encrypted': signature_b64,
                'expiry_date': expires_at,
            }
        )

        return Response({
            'payload': payload,
            'signature': signature_b64,
        })

