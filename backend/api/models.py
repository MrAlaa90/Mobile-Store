from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    name = models.CharField(max_length=255)
    store_name = models.CharField(max_length=255, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('user', 'User')], default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    REQUIRED_FIELDS = ['email', 'name']

    def __str__(self):
        store_display = f" - {self.store_name}" if self.store_name else ""
        return f"{self.username}{store_display}"

    def get_active_license(self):
        from django.utils import timezone
        today = timezone.localdate()
        return self.licenses.filter(
            status='active',
            start_date__lte=today,
            end_date__gte=today
        ).first()

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

class License(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='licenses')
    license_key = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    type = models.CharField(max_length=20, choices=[('trial', 'Trial'), ('paid', 'Paid')])
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('expired', 'Expired'), ('revoked', 'Revoked')], default='active')
    max_devices = models.PositiveIntegerField(default=3, help_text="الحد الأقصى للأجهزة المصرح بها (ديسكتوب وموبايل)")
    notes = models.CharField(max_length=255, blank=True, default='')

    @property
    def is_valid(self):
        from django.utils import timezone
        today = timezone.localdate()
        return self.status == 'active' and self.start_date <= today <= self.end_date

    @property
    def days_remaining(self):
        from django.utils import timezone
        today = timezone.localdate()
        if self.end_date < today:
            return 0
        return (self.end_date - today).days

    def __str__(self):
        return f"{self.license_key} ({self.get_type_display()}) - {self.status}"

class Device(models.Model):
    DEVICE_TYPES = [
        ('desktop', 'Desktop (كاشير ديسكتوب)'),
        ('mobile', 'Mobile (تطبيق هاتف)'),
        ('tablet', 'Tablet (تابلت)'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255, blank=True, default='')
    hardware_id = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='desktop')
    is_active = models.BooleanField(default=True)
    license = models.ForeignKey(License, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name or 'Device'} ({self.hardware_id[:12]})"

class Token(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='token')
    token_encrypted = models.TextField()
    last_online_check = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField()

    def __str__(self):
        return f"Token for {self.device}"

class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('available', 'Available'), ('sold', 'Sold')], default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} - {self.name} (${self.sale_price})"

REPAIR_STATUS_CHOICES = [
    ('diagnosing', 'قيد الفحص والتشخيص'),
    ('waiting_parts', 'في انتظار قطع الغيار'),
    ('in_progress', 'قيد الصيانة والإصلاح'),
    ('ready', 'جاهز للاستلام'),
    ('delivered', 'تم التسليم ومكتمل'),
    ('cancelled', 'مرفوض / تعذر الإصلاح'),
]

class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    item = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    item_description = models.CharField(max_length=255, blank=True, default='')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    customer_name = models.CharField(max_length=255, blank=True, default='Walk-in Customer')
    invoice_id = models.CharField(max_length=50, blank=True, default='')
    terminal_device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    quantity = models.PositiveIntegerField(default=1)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        cost = self.item.purchase_price if (self.item and self.item.purchase_price) else self.cost_price
        if self.profit is None or self.profit == 0:
            self.profit = (self.sale_price - cost) * self.quantity
        if not self.item_description and self.item:
            self.item_description = f"{self.item.brand} {self.item.model} - {self.item.name}"
        super().save(*args, **kwargs)
        if self.item and self.item.status != 'sold':
            self.item.status = 'sold'
            self.item.save(update_fields=['status'])

    def __str__(self):
        desc = self.item_description or (self.item.name if self.item else 'Item')
        return f"Sale #{self.id} ({self.invoice_id}): {desc} (${self.sale_price})"

class Repair(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repairs')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='repairs')
    customer_name = models.CharField(max_length=255, blank=True, default='')
    device_info = models.CharField(max_length=255)
    issue_description = models.TextField()
    repair_cost = models.DecimalField(max_digits=10, decimal_places=2)
    customer_payment = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=30, choices=REPAIR_STATUS_CHOICES, default='diagnosing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def remaining_balance(self):
        return self.customer_payment - self.deposit

    def save(self, *args, **kwargs):
        if self.profit is None or self.profit == 0:
            self.profit = self.customer_payment - self.repair_cost
        if not self.customer_name and self.customer:
            self.customer_name = self.customer.name
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.customer_name or (self.customer.name if self.customer else 'Customer')
        return f"Repair for {name}: {self.device_info} ({self.get_status_display()})"


import secrets
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def generate_license_key(prefix="MS-TR"):
    token = secrets.token_hex(4).upper()
    return f"{prefix}-{token[:4]}-{token[4:]}"


def create_trial_license_for_user(user, days=20, max_devices=3):
    today = timezone.localdate()
    license_key = generate_license_key("MS-TR")
    while License.objects.filter(license_key=license_key).exists():
        license_key = generate_license_key("MS-TR")
    return License.objects.create(
        user=user,
        license_key=license_key,
        start_date=today,
        end_date=today + timedelta(days=days),
        type='trial',
        status='active',
        max_devices=max_devices,
        notes=f"رخصة تجريبية تلقائية لمدة {days} يوماً (أقصى أجهزة: {max_devices})"
    )


@receiver(post_save, sender=User)
def auto_provision_trial_license(sender, instance, created, **kwargs):
    """Automatically generates a 20-day trial license when a new store owner account is created."""
    if created and not instance.is_superuser:
        if not instance.licenses.exists():
            create_trial_license_for_user(instance, days=20, max_devices=3)
