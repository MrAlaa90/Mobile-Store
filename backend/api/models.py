from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('user', 'User')], default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    REQUIRED_FIELDS = ['email', 'name']

    def __str__(self):
        return self.username

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
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('expired', 'Expired')], default='active')

    def __str__(self):
        return f"{self.license_key} - {self.status}"

class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255, blank=True, default='')
    hardware_id = models.CharField(max_length=255, unique=True)
    license = models.ForeignKey(License, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    created_at = models.DateTimeField(auto_now_add=True)

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


