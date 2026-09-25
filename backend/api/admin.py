from datetime import timedelta
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html

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
    generate_license_key,
)

admin.site.site_header = "نظام Mobile-Store | لوحة التحكم المركزية والتراخيص (Super Admin)"
admin.site.site_title = "Mobile-Store Admin"
admin.site.index_title = "إدارة المتاجر، التراخيص، الأجهزة والمبيعات"


class LicenseInline(admin.TabularInline):
    model = License
    extra = 0
    fields = ('license_key', 'type', 'status', 'start_date', 'end_date', 'max_devices', 'notes')
    readonly_fields = ('license_key',)
    show_change_link = True


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    fields = ('name', 'hardware_id', 'device_type', 'is_active', 'last_seen', 'created_at')
    readonly_fields = ('created_at', 'last_seen')
    show_change_link = True


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'store_name_display',
        'phone',
        'role',
        'license_summary',
        'devices_count_display',
        'is_active',
        'date_joined',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'name', 'store_name', 'phone', 'email')
    ordering = ('-date_joined',)
    inlines = [LicenseInline, DeviceInline]

    fieldsets = BaseUserAdmin.fieldsets + (
        ('معلومات المتجر والتجارة (Store Profile)', {
            'fields': ('store_name', 'phone', 'role'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('معلومات المتجر والتجارة (Store Profile)', {
            'fields': ('store_name', 'phone', 'role'),
        }),
    )

    def get_inlines(self, request, obj=None):
        # Do not render inlines on the Add User screen to prevent orphan foreign keys
        if obj is None:
            return []
        return self.inlines

    def store_name_display(self, obj):
        return obj.store_name or obj.name or '-'
    store_name_display.short_description = "اسم المتجر"

    def license_summary(self, obj):
        lic = obj.get_active_license()
        if not lic:
            return format_html('<span style="color:#ef4444; font-weight:bold;">❌ لا توجد رخصة نشطة</span>')
        days = lic.days_remaining
        color = "#10b981" if days > 5 else "#f59e0b"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} (باقي {} يوم)</span>',
            color,
            lic.get_type_display(),
            days,
        )
    license_summary.short_description = "حالة الاشتراك"

    def devices_count_display(self, obj):
        count = obj.devices.filter(is_active=True).count()
        lic = obj.get_active_license()
        max_d = lic.max_devices if lic else 0
        return f"{count} / {max_d} جهاز"
    devices_count_display.short_description = "الأجهزة المعتمدة"

    actions = ['provision_20_day_trial']

    @admin.action(description="🎁 إصدار رخصة تجريبية جديدة (20 يوماً) للمتاجر المحددة")
    def provision_20_day_trial(self, request, queryset):
        count = 0
        for user in queryset:
            create_trial_license_for_user(user, days=20, max_devices=3)
            count += 1
        self.message_user(request, f"تم إنشاء رخصة تجريبية 20 يوماً بنجاح لـ {count} متجر.")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = (
        'license_key',
        'store_display',
        'type_badge',
        'status_badge',
        'start_date',
        'end_date',
        'days_remaining_display',
        'devices_usage_display',
    )
    list_filter = ('type', 'status', 'start_date', 'end_date')
    search_fields = ('license_key', 'user__username', 'user__store_name', 'user__name')
    date_hierarchy = 'end_date'
    actions = ['extend_30_days', 'upgrade_to_one_year_paid', 'revoke_licenses']

    def get_changeform_initial_data(self, request):
        today = timezone.localdate()
        return {
            'start_date': today,
            'end_date': today + timedelta(days=365),
            'type': 'paid',
            'status': 'active',
            'license_key': generate_license_key("MS-PAID"),
            'max_devices': 3,
        }

    def store_display(self, obj):
        return f"{obj.user.store_name or obj.user.username} ({obj.user.phone or 'بدون هاتف'})"
    store_display.short_description = "المتجر / العميل"

    def type_badge(self, obj):
        if obj.type == 'trial':
            return format_html('<span style="background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:4px; font-weight:bold;">تجريبي (Trial)</span>')
        return format_html('<span style="background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:4px; font-weight:bold;">مدفوع (Paid)</span>')
    type_badge.short_description = "نوع الترخيص"

    def status_badge(self, obj):
        if obj.status == 'active':
            return format_html('<span style="background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:4px; font-weight:bold;">🟢 نشط</span>')
        elif obj.status == 'expired':
            return format_html('<span style="background:#fee2e2; color:#b91c1c; padding:3px 8px; border-radius:4px; font-weight:bold;">🔴 منتهي</span>')
        return format_html('<span style="background:#f3f4f6; color:#6b7280; padding:3px 8px; border-radius:4px; font-weight:bold;">⚪ معطل</span>')
    status_badge.short_description = "الحالة"

    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days == 0:
            return format_html('<span style="color:#ef4444; font-weight:bold;">منتهي الصلاحية</span>')
        color = "#10b981" if days > 7 else "#f59e0b"
        return format_html('<span style="color:{}; font-weight:bold;">{} يوم متبقي</span>', color, days)
    days_remaining_display.short_description = "المدة المتبقية"

    def devices_usage_display(self, obj):
        active_count = obj.devices.filter(is_active=True).count()
        return f"{active_count} / {obj.max_devices} أجهزة"
    devices_usage_display.short_description = "استهلاك الأجهزة"

    @admin.action(description="➕ تمديد الصلاحية 30 يوماً للتراخيص المحددة")
    def extend_30_days(self, request, queryset):
        today = timezone.localdate()
        for lic in queryset:
            base_date = lic.end_date if lic.end_date >= today else today
            lic.end_date = base_date + timedelta(days=30)
            lic.status = 'active'
            lic.save(update_fields=['end_date', 'status'])
        self.message_user(request, f"تم تمديد صلاحية {queryset.count()} ترخيص لمدة 30 يوماً بنجاح.")

    @admin.action(description="⭐ ترقية إلى اشتراك سنوي مدفوع (سنة كاملة)")
    def upgrade_to_one_year_paid(self, request, queryset):
        today = timezone.localdate()
        for lic in queryset:
            lic.type = 'paid'
            lic.status = 'active'
            lic.start_date = today
            lic.end_date = today + timedelta(days=365)
            lic.notes = "اشتراك سنوي معتمد"
            lic.save(update_fields=['type', 'status', 'start_date', 'end_date', 'notes'])
        self.message_user(request, f"تمت ترقية {queryset.count()} ترخيص لاشتراك سنوي مدفوع بنجاح!")

    @admin.action(description="⛔ إيقاف / تعطيل التراخيص المحددة فوراً")
    def revoke_licenses(self, request, queryset):
        queryset.update(status='revoked')
        self.message_user(request, f"تم تعطيل {queryset.count()} ترخيص.")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'store_display',
        'device_type',
        'hardware_id_short',
        'is_active',
        'license_link',
        'last_seen',
        'created_at',
    )
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('name', 'hardware_id', 'user__username', 'user__store_name')
    actions = ['unbind_devices', 'activate_devices', 'deactivate_devices']

    def store_display(self, obj):
        return obj.user.store_name or obj.user.username
    store_display.short_description = "المتجر"

    def hardware_id_short(self, obj):
        return f"{obj.hardware_id[:16]}..."
    hardware_id_short.short_description = "بصمة العتاد (HWID)"

    def license_link(self, obj):
        if obj.license:
            return obj.license.license_key
        return "بدون رخصة"
    license_link.short_description = "الرخصة المرتبطة"

    @admin.action(description="🔓 إلغاء ربط الأجهزة المحددة (تحرير مقعد ترخيص)")
    def unbind_devices(self, request, queryset):
        for dev in queryset:
            dev.license = None
            dev.is_active = False
            dev.save(update_fields=['license', 'is_active'])
        self.message_user(request, f"تم إلغاء ربط {queryset.count()} جهاز وتحرير أماكنها في التراخيص.")

    @admin.action(description="✅ تفعيل الأجهزة المحددة")
    def activate_devices(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {queryset.count()} جهاز.")

    @admin.action(description="🚫 تعطيل الأجهزة المحددة")
    def deactivate_devices(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"تم تعطيل {queryset.count()} جهاز.")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'model', 'purchase_price', 'sale_price', 'status', 'store_display', 'created_at')
    list_filter = ('status', 'brand', 'user')
    search_fields = ('name', 'brand', 'model', 'user__username', 'user__store_name')

    def store_display(self, obj):
        return obj.user.store_name or obj.user.username
    store_display.short_description = "المتجر"


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'item_description', 'customer_name', 'sale_price', 'profit', 'store_display', 'date')
    list_filter = ('date', 'user')
    search_fields = ('invoice_id', 'item_description', 'customer_name', 'user__username', 'user__store_name')
    date_hierarchy = 'date'

    def store_display(self, obj):
        return obj.user.store_name or obj.user.username
    store_display.short_description = "المتجر"


@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = ('device_info', 'customer_name', 'status', 'repair_cost', 'customer_payment', 'profit', 'store_display', 'created_at')
    list_filter = ('status', 'created_at', 'user')
    search_fields = ('device_info', 'issue_description', 'customer_name', 'user__username', 'user__store_name')

    def store_display(self, obj):
        return obj.user.store_name or obj.user.username
    store_display.short_description = "المتجر"


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'store_display', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'phone', 'email', 'user__username', 'user__store_name')

    def store_display(self, obj):
        return obj.user.store_name or obj.user.username
    store_display.short_description = "المتجر"


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('device', 'expiry_date', 'last_online_check')
    readonly_fields = ('token_encrypted',)
