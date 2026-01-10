import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth import get_user_model

from apps.v1.orders.models import DeliveryMethod, PaymentMethod, Order, OrderProduct
from apps.v1.products.models import Product

User = get_user_model()
fake = Faker('ru_RU')  # Rus tili uchun


class Command(BaseCommand):
    help = 'База данныхни fake order ma\'lumotlari bilan to\'ldiradi'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Mavjud order ma'lumotlari tozalanmoqda..."))
        
        # Mavjud order ma'lumotlarini tozalash
        OrderProduct.objects.all().delete()
        Order.objects.all().delete()
        PaymentMethod.objects.all().delete()
        DeliveryMethod.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Ma'lumotlar tozalandi."))
        self.stdout.write(self.style.SUCCESS("Fake order ma'lumotlari yaratilmoqda..."))

        # 1. DeliveryMethod yaratish
        delivery_methods_data = [
            {
                'name': 'Курьерская доставка',
                'description': 'Доставка курьером на указанный адрес в течение 1-3 рабочих дней'
            },
            {
                'name': 'Самовывоз',
                'description': 'Самовывоз из пункта выдачи заказов'
            },
            {
                'name': 'Почта России',
                'description': 'Доставка через Почту России, срок доставки 5-14 дней'
            },
            {
                'name': 'Экспресс-доставка',
                'description': 'Экспресс-доставка в течение дня (только для крупных городов)'
            },
            {
                'name': 'Транспортная компания',
                'description': 'Доставка через транспортную компанию (СДЭК, ПЭК и др.)'
            }
        ]
        
        delivery_methods = []
        for data in delivery_methods_data:
            delivery_method = DeliveryMethod.objects.create(**data)
            delivery_methods.append(delivery_method)
            self.stdout.write(self.style.SUCCESS(f"  ✓ DeliveryMethod yaratildi: {delivery_method.name}"))

        # 2. PaymentMethod yaratish
        payment_methods_data = [
            {
                'name': 'Наличными',
                'description': 'Оплата наличными при получении заказа'
            },
            {
                'name': 'Банковская карта онлайн',
                'description': 'Оплата банковской картой через платежную систему'
            },
            {
                'name': 'Банковский перевод',
                'description': 'Оплата через банковский перевод на расчетный счет'
            },
            {
                'name': 'Электронные кошельки',
                'description': 'Оплата через электронные платежные системы (ЮMoney, Qiwi и др.)'
            },
            {
                'name': 'Рассрочка',
                'description': 'Оплата в рассрочку на выгодных условиях'
            }
        ]
        
        payment_methods = []
        for data in payment_methods_data:
            payment_method = PaymentMethod.objects.create(**data)
            payment_methods.append(payment_method)
            self.stdout.write(self.style.SUCCESS(f"  ✓ PaymentMethod yaratildi: {payment_method.name}"))

        # 3. Userlarni olish (agar mavjud bo'lsa)
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR("  ✗ Userlar topilmadi! Avval userlar yaratilishi kerak."))
            return
        
        # 4. Productlarni olish
        products = Product.objects.filter(is_active=True)
        if not products.exists():
            self.stdout.write(self.style.ERROR("  ✗ Productlar topilmadi! Avval productlar yaratilishi kerak."))
            return

        # 5. Orderlar yaratish
        cities = ['г. Москва', 'г. Санкт-Петербург', 'г. Новосибирск', 'г. Екатеринбург', 
                  'г. Казань', 'г. Нижний Новгород', 'г. Челябинск', 'г. Омск', 'г. Самара']
        
        streets = ['ул. Ленина', 'пр. Мира', 'ул. Пушкина', 'ул. Гагарина', 
                   'ул. Советская', 'пр. Победы', 'ул. Центральная', 'ул. Новая']
        
        num_orders = random.randint(20, 50)  # 20-50 ta order
        
        for i in range(num_orders):
            user = random.choice(users)
            city = random.choice(cities)
            street = random.choice(streets)
            house = str(random.randint(1, 200))
            flat = str(random.randint(1, 200)) if random.choice([True, False]) else ''
            index = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            delivery_method = random.choice(delivery_methods) if delivery_methods else None
            payment_method = random.choice(payment_methods) if payment_methods else None
            price_for_delivery = Decimal(str(random.uniform(0, 500).__round__(2)))
            
            # Order yaratish (total_price keyin hisoblanadi)
            order = Order.objects.create(
                user=user,
                city=city,
                street=street,
                house=house,
                flat=flat,
                index=index,
                total_price=Decimal('0.00'),  # Keyin yangilanadi
                delivery_method=delivery_method,
                payment_method=payment_method,
                price_for_delivery=price_for_delivery
            )
            
            # OrderProductlar yaratish
            num_products_in_order = random.randint(1, 5)  # Har bir orderda 1-5 ta product
            selected_products = random.sample(list(products), min(num_products_in_order, len(products)))
            
            total_price = Decimal('0.00')
            
            for product in selected_products:
                quantity = random.randint(1, 10)
                # Product narxini olish (price_per_meter)
                price = product.price_per_meter
                
                OrderProduct.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                
                total_price += price * quantity
            
            # Total price + delivery price
            total_price += price_for_delivery
            
            # Order total_price ni yangilash
            order.total_price = total_price
            order.save()
            
            self.stdout.write(self.style.SUCCESS(f"  ✓ Order #{order.id} yaratildi - {user.email} ({total_price} руб.)"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Barcha fake order ma'lumotlari yaratildi!"))
        self.stdout.write(self.style.SUCCESS(f"  - DeliveryMethod: {len(delivery_methods)}"))
        self.stdout.write(self.style.SUCCESS(f"  - PaymentMethod: {len(payment_methods)}"))
        self.stdout.write(self.style.SUCCESS(f"  - Order: {num_orders}"))
        self.stdout.write(self.style.SUCCESS(f"  - OrderProduct: {OrderProduct.objects.count()}"))
