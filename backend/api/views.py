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
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Customer,
    Device,
    Inventory,
    License,
    Repair,
    Sale,
    Token,
    User,
    create_trial_license_for_user,
)
from .serializers import (
    CustomerSerializer,
    DeviceSerializer,
    InventorySerializer,
    LicenseSerializer,
    RepairSerializer,
    SaleSerializer,
    StoreRegistrationSerializer,
    UserSerializer,
)


class HasActiveLicenseOrReadOnly(BasePermission):
    """
    Enforces SaaS subscription and trial limits.
    Store owners whose 20-day trial or annual subscription has expired can view historical
    records (GET), but cannot modify or insert new records until renewing.
    Superusers bypass this check.
    """
    message = "انتهت فترة الاشتراك التجريبية (20 يوماً) أو الاشتراك السنوي. يرجى التجديد للاستمرار في إجراء العمليات."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        if request.method in SAFE_METHODS:
            return True
        today = timezone.localdate()
        License.objects.filter(user=request.user, status='active', end_date__lt=today).update(status='expired')
        return License.objects.filter(
            user=request.user,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        ).exists()


class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, HasActiveLicenseOrReadOnly]

    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InventoryViewSet(ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated, HasActiveLicenseOrReadOnly]

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
    permission_classes = [IsAuthenticated, HasActiveLicenseOrReadOnly]

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
    permission_classes = [IsAuthenticated, HasActiveLicenseOrReadOnly]

    def get_queryset(self):
        return Repair.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeviceViewSet(ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Device.objects.all().select_related('user', 'license').order_by('-created_at')
        return Device.objects.filter(user=user).select_related('license').order_by('-created_at')


class StoreRegistrationView(APIView):
    """
    Public endpoint: Allows a new store owner to register their store.
    Automatically generates an isolated tenant account with an active 20-day trial license.
    """
    permission_classes = []

    def post(self, request):
        serializer = StoreRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            name=data['store_name'],
            store_name=data['store_name'],
            phone=data.get('phone', ''),
            role='user',
        )

        license_obj = user.get_active_license()
        if not license_obj:
            license_obj = create_trial_license_for_user(user, days=20, max_devices=3)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "تم إنشاء حساب المتجر وتفعيل الفترة التجريبية (20 يوماً) بنجاح!",
            "user": UserSerializer(user).data,
            "license": LicenseSerializer(license_obj).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LicenseCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        hardware_id = request.query_params.get('hardware_id')
        today = timezone.localdate()

        # Auto-expire licenses whose end date has passed
        License.objects.filter(
            user=user,
            status='active',
            end_date__lt=today
        ).update(status='expired')

        active_license = user.get_active_license()

        if not active_license:
            return Response({
                "error": "license_expired",
                "detail": "انتهت فترة الرخصة التجريبية (20 يوماً) أو الاشتراك السنوي لهذا المتجر. يرجى التواصل مع الإدارة لتجديد الاشتراك.",
                "status": "expired"
            }, status=status.HTTP_403_FORBIDDEN)

        if hardware_id:
            device = Device.objects.filter(user=user, hardware_id=hardware_id).first()
            if device:
                if not device.is_active:
                    return Response({
                        "error": "device_disabled",
                        "detail": "تم تعطيل هذا الجهاز من قبل إدارة المتجر."
                    }, status=status.HTTP_403_FORBIDDEN)

                if device.license != active_license:
                    device.license = active_license
                device.last_seen = timezone.now()
                device.save(update_fields=['license', 'last_seen'])
                result_licenses = [active_license]
            else:
                # Enforce max_devices limit per license
                current_active_devices = Device.objects.filter(
                    user=user,
                    license=active_license,
                    is_active=True
                ).count()

                if current_active_devices >= active_license.max_devices:
                    return Response({
                        "error": "max_devices_exceeded",
                        "detail": f"تم الوصول للحد الأقصى للأجهزة المصرح بها لهذا المتجر ({active_license.max_devices} أجهزة). يرجى إلغاء ربط أحد الأجهزة السابقة أو ترقية باقة الاشتراك.",
                        "max_devices": active_license.max_devices,
                        "current_devices": current_active_devices,
                    }, status=status.HTTP_403_FORBIDDEN)

                # Register new device bound to this license
                device = Device.objects.create(
                    user=user,
                    hardware_id=hardware_id,
                    license=active_license,
                    name=f"Terminal-{hardware_id[:8]}",
                    device_type='desktop',
                    is_active=True
                )
                result_licenses = [active_license]
        else:
            result_licenses = licenses

        serializer = LicenseSerializer(result_licenses, many=True)
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

            # Check max devices limit
            current_active_devices = Device.objects.filter(user=user, license=active_license, is_active=True).count()
            if current_active_devices >= active_license.max_devices:
                return Response({
                    'error': f'Max devices limit reached ({active_license.max_devices}). Please unbind an old device.'
                }, status=status.HTTP_403_FORBIDDEN)

            device = Device.objects.create(
                user=user,
                hardware_id=hardware_id,
                license=active_license,
                name=f"Terminal-{hardware_id[:8]}",
                device_type='desktop',
                is_active=True
            )

        if not device.is_active:
            return Response({'error': 'This device has been deactivated'}, status=status.HTTP_403_FORBIDDEN)

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


