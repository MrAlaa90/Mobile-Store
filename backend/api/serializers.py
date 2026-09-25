from rest_framework import serializers
from .models import Customer, Device, Inventory, License, Repair, Sale, Token, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'store_name', 'phone', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class LicenseSerializer(serializers.ModelSerializer):
    days_remaining = serializers.IntegerField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = License
        fields = [
            'id', 'license_key', 'start_date', 'end_date', 'type',
            'status', 'max_devices', 'days_remaining', 'is_valid', 'notes'
        ]
        read_only_fields = ['id', 'days_remaining', 'is_valid']


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'name', 'hardware_id', 'device_type', 'is_active', 'license', 'created_at', 'last_seen']
        read_only_fields = ['id', 'created_at', 'last_seen']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'name', 'brand', 'model', 'purchase_price', 'sale_price', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class SaleSerializer(serializers.ModelSerializer):
    item_detail = InventorySerializer(source='item', read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_id', 'item', 'item_detail', 'item_description',
            'customer', 'customer_name', 'terminal_device', 'quantity',
            'cost_price', 'sale_price', 'profit', 'date'
        ]
        read_only_fields = ['id', 'profit', 'date']

    def validate_item(self, value):
        request = self.context.get('request')
        if value and request and hasattr(request, 'user') and not request.user.is_superuser:
            if value.user != request.user:
                raise serializers.ValidationError("العنصر المحدد لا ينتمي إلى مخزون هذا المتجر.")
        return value

    def validate_customer(self, value):
        request = self.context.get('request')
        if value and request and hasattr(request, 'user') and not request.user.is_superuser:
            if value.user != request.user:
                raise serializers.ValidationError("العميل المحدد لا ينتمي إلى هذا المتجر.")
        return value


class RepairSerializer(serializers.ModelSerializer):
    remaining_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Repair
        fields = [
            'id', 'customer', 'customer_name', 'device_info',
            'issue_description', 'repair_cost', 'customer_payment',
            'deposit', 'remaining_balance', 'profit', 'status',
            'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'profit', 'remaining_balance', 'status_display', 'created_at', 'updated_at']

    def validate_customer(self, value):
        request = self.context.get('request')
        if value and request and hasattr(request, 'user') and not request.user.is_superuser:
            if value.user != request.user:
                raise serializers.ValidationError("العميل المحدد لا ينتمي إلى هذا المتجر.")
        return value


class StoreRegistrationSerializer(serializers.Serializer):
    store_name = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    email = serializers.EmailField(required=False, allow_blank=True, default='')

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("اسم المستخدم مستخدم بالفعل، يرجى اختيار اسم آخر.")
        return value



