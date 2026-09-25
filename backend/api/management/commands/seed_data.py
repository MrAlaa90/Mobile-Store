from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import License, Device, Customer, Inventory, Repair, Sale

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with default admin user, active license, sample inventory, customers, and repairs."

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Admin User
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@mobilestore.local",
                "name": "Store Administrator",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user 'admin' (password: admin123)"))
        else:
            self.stdout.write("Admin user 'admin' already exists.")

        # 2. License
        lic, _ = License.objects.get_or_create(
            license_key="MS-2026-ENTERPRISE-PRO-KEY",
            defaults={
                "user": admin_user,
                "start_date": date.today() - timedelta(days=30),
                "end_date": date.today() + timedelta(days=365 * 2),
                "type": "paid",
                "status": "active",
            }
        )
        self.stdout.write(f"Active License: {lic.license_key}")

        # 3. Authorized Terminal Devices
        devices_data = [
            ("POS Terminal Main 01", "effb942a4261"),
            ("Workshop Diagnostic Terminal", "c8d1e2f3a4b5"),
        ]
        for dev_name, hw_id in devices_data:
            Device.objects.get_or_create(
                hardware_id=hw_id,
                defaults={
                    "user": admin_user,
                    "name": dev_name,
                    "license": lic,
                }
            )

        # 4. Customers
        customers_data = [
            ("أحمد محمود علي", "01012345678", "ahmed.ali@gmail.com"),
            ("سارة إبراهيم حسن", "01123456789", "sarah.ibrahim@outlook.com"),
            ("عمر طارق النجار", "01234567890", "omar.tareq@yahoo.com"),
            ("محمود مصطفى كمال", "01545678901", "m.mostafa@gmail.com"),
            ("هدى عبد الرحمن", "01098765432", "hoda.abdo@gmail.com"),
        ]
        created_customers = []
        for name, phone, email in customers_data:
            cust, _ = Customer.objects.get_or_create(
                user=admin_user,
                phone=phone,
                defaults={"name": name, "email": email}
            )
            created_customers.append(cust)

        self.stdout.write(f"Verified {len(created_customers)} customers.")

        # 5. Inventory Items
        inventory_data = [
            ("iPhone 15 Pro Max 256GB Natural Titanium", "Apple", "iPhone 15 Pro Max", Decimal("56000.00"), Decimal("63000.00"), "available"),
            ("Galaxy S24 Ultra 512GB Titanium Black", "Samsung", "Galaxy S24 Ultra", Decimal("49000.00"), Decimal("55500.00"), "available"),
            ("Reno 12 5G 256GB Silver", "Oppo", "Reno 12", Decimal("16500.00"), Decimal("19200.00"), "available"),
            ("Xiaomi 13T 256GB Black", "Xiaomi", "13T", Decimal("17000.00"), Decimal("19800.00"), "available"),
            ("AirPods Pro (2nd Gen) USB-C", "Apple", "AirPods Pro 2", Decimal("8800.00"), Decimal("10500.00"), "available"),
            ("شاحن سامسونج أصلي 45W Type-C", "Samsung", "Charger 45W", Decimal("650.00"), Decimal("950.00"), "available"),
            ("شاشة أصلية iPhone 13 OLED Replacement", "Apple Spare", "iPhone 13 Screen", Decimal("3800.00"), Decimal("5200.00"), "available"),
            ("Redmi Note 13 128GB Blue", "Xiaomi", "Redmi Note 13", Decimal("7800.00"), Decimal("9200.00"), "sold"),
        ]

        created_items = []
        for name, brand, model, purchase_price, sale_price, status in inventory_data:
            inv, _ = Inventory.objects.get_or_create(
                user=admin_user,
                name=name,
                defaults={
                    "brand": brand,
                    "model": model,
                    "purchase_price": purchase_price,
                    "sale_price": sale_price,
                    "status": status,
                }
            )
            created_items.append(inv)

        self.stdout.write(f"Verified {len(created_items)} inventory items.")

        # 6. Repair Tickets
        repairs_data = [
            (
                created_customers[0],
                "iPhone 14 Pro Max",
                "شاشة مكسورة بالكامل وتحتاج استبدال شاشة أصلية مع برمجة TrueTone",
                Decimal("4200.00"),
                Decimal("5800.00"),
                Decimal("2000.00"),
                "in_progress"
            ),
            (
                created_customers[1],
                "Samsung Galaxy S22 Ultra",
                "الجهاز لا يشحن - تلف في سوكيت الشحن الداخلي Sub-board",
                Decimal("350.00"),
                Decimal("750.00"),
                Decimal("400.00"),
                "waiting_parts"
            ),
            (
                created_customers[2],
                "Xiaomi Poco X3 Pro",
                "عطل في الباور وإعادة تشغيل متكررة (IC Power / CPU Reballing)",
                Decimal("800.00"),
                Decimal("1600.00"),
                Decimal("500.00"),
                "diagnosing"
            ),
            (
                created_customers[3],
                "Oppo Reno 6 5G",
                "تغيير بطارية أصلية وصيانة زر الباور",
                Decimal("450.00"),
                Decimal("900.00"),
                Decimal("900.00"),
                "ready"
            ),
            (
                created_customers[4],
                "iPad Air 5",
                "استبدال باغة زجاج الشاشة الخارجية مع المحافظة على الشاشة الأصلية",
                Decimal("1100.00"),
                Decimal("2200.00"),
                Decimal("2200.00"),
                "delivered"
            ),
        ]

        for cust, dev_info, issue, cost, payment, deposit, st in repairs_data:
            Repair.objects.get_or_create(
                user=admin_user,
                customer=cust,
                device_info=dev_info,
                defaults={
                    "customer_name": cust.name,
                    "issue_description": issue,
                    "repair_cost": cost,
                    "customer_payment": payment,
                    "deposit": deposit,
                    "profit": payment - cost,
                    "status": st,
                }
            )

        self.stdout.write("Verified 5 sample repair tickets.")

        # 7. Initial Sales Records
        sales_data = [
            ("INV-2026-001", "Xiaomi Redmi Note 13 128GB Blue", created_customers[0], 1, Decimal("7800.00"), Decimal("9200.00")),
            ("INV-2026-002", "جراب مغناطيسي وحماية شاشة 9D iPhone 15", created_customers[1], 2, Decimal("150.00"), Decimal("450.00")),
        ]

        for inv_id, desc, cust, qty, cost, sale_p in sales_data:
            Sale.objects.get_or_create(
                user=admin_user,
                invoice_id=inv_id,
                defaults={
                    "item_description": desc,
                    "customer": cust,
                    "customer_name": cust.name,
                    "quantity": qty,
                    "cost_price": cost,
                    "sale_price": sale_p,
                    "profit": (sale_p - cost) * qty,
                }
            )

        self.stdout.write(self.style.SUCCESS("✅ Database seeded successfully with full test suite!"))
