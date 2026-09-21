from rest_framework import serializers
from .models import Customer, Device, Inventory, License, Repair, Sale, Token, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'role']
        read_only_fields = ['id']


class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ['id', 'license_key', 'start_date', 'end_date', 'type', 'status']
        read_only_fields = ['id']


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'name', 'hardware_id', 'license', 'created_at']
        read_only_fields = ['id', 'created_at']


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


