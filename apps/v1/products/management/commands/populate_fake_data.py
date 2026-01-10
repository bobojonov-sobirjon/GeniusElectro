import os
import random
import io
from PIL import Image
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from faker import Faker
from django.contrib.auth import get_user_model

from apps.v1.products.models import (
    Category, MainCategory, SubCategory, Product,
    ProductImage, ProductMeterage, Favourite
)

User = get_user_model()
fake = Faker('ru_RU')  # Rus tili uchun


def create_dummy_image(filename="dummy.png", size=(800, 600)):
    """Dummy rasm yaratadi"""
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    
    image = Image.new('RGB', size, (r, g, b))
    image_io = io.BytesIO()
    image.save(image_io, format='PNG')
    image_file = ContentFile(image_io.getvalue(), name=filename)
    return image_file


class Command(BaseCommand):
    help = 'База данныхни fake product ma\'lumotlari bilan to\'ldiradi'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Mavjud ma'lumotlar tozalanmoqda..."))
        
        # Mavjud ma'lumotlarni tozalash
        Favourite.objects.all().delete()
        ProductImage.objects.all().delete()
        ProductMeterage.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Ma'lumotlar tozalandi."))
        self.stdout.write(self.style.SUCCESS("Fake ma'lumotlar yaratilmoqda..."))

        # 1. MainCategory yaratish (rasm bilan)
        main_category_names = [
            "Кабель и провод",
            "Системы для прокладки кабеля",
            "Кабельные клеммы, наконечники, муфты",
            "Монтажные коробки",
            "Электроустановочные изделия",
            "Светотехника и лампы"
        ]
        
        main_categories = []
        for i, name in enumerate(main_category_names):
            main_cat = MainCategory.objects.create(
                name=name,
                description=fake.paragraph(nb_sentences=2),
                image=create_dummy_image(f"main_category_{i+1}.png")
            )
            main_categories.append(main_cat)
            self.stdout.write(f"✓ MainCategory yaratildi: {main_cat.name}")

        # 2. SubCategory yaratish (rasm bilan)
        sub_category_data = {
            "Кабель и провод": [
                "Силовой кабель", "Контрольный кабель", "Монтажный провод", "Сетевой кабель"
            ],
            "Системы для прокладки кабеля": [
                "Гофрированные трубы", "Кабель-каналы", "Металлорукав", "Лотки кабельные"
            ],
            "Кабельные клеммы, наконечники, муфты": [
                "Наконечники медные", "Гильзы соединительные", "Клеммные колодки", "Муфты термоусаживаемые"
            ],
            "Монтажные коробки": [
                "Коробки установочные", "Коробки распределительные", "Боксы для автоматов"
            ],
            "Электроустановочные изделия": [
                "Розетки", "Выключатели", "Диммеры", "Автоматические выключатели"
            ],
            "Светотехника и лампы": [
                "Светодиодные лампы", "Прожекторы", "Потолочные светильники", "Уличные фонари"
            ]
        }

        sub_categories = []
        sub_counter = 1
        for main_cat in main_categories:
            for sub_name in sub_category_data.get(main_cat.name, []):
                sub_cat = SubCategory.objects.create(
                    parent=main_cat,
                    name=sub_name,
                    description=fake.paragraph(nb_sentences=1),
                    image=create_dummy_image(f"sub_category_{sub_counter}.png")
                )
                sub_categories.append(sub_cat)
                sub_counter += 1
                self.stdout.write(f"  ✓ SubCategory yaratildi: {sub_cat.name} (Parent: {main_cat.name})")

        if not sub_categories:
            self.stdout.write(self.style.ERROR("SubCategory yaratilmadi. Product yaratib bo'lmaydi."))
            return

        # 3. Product yaratish (10 ta)
        products_to_create = 10
        products = []
        
        # Test user yaratish (agar yo'q bo'lsa)
        if User.objects.count() < 1:
            test_user = User.objects.create_user(
                email='test@example.com',
                username='test@example.com',
                password='test123',
                first_name='Test',
                last_name='User'
            )
            self.stdout.write(f"✓ Test user yaratildi: {test_user.email}")
        
        users = list(User.objects.all())

        # Product nomlari va ma'lumotlari
        product_templates = [
            {
                'name_template': 'Кабель ВВГнг-LS {cores}x{size}',
                'cores': [1, 2, 3, 4, 5],
                'sizes': ['1.5', '2.5', '4', '6', '10'],
                'manufacturers': ['IEK', 'АВВ', 'Schneider Electric', 'Legrand'],
                'countries': ['Россия', 'Китай', 'Германия', 'Франция'],
                'materials': ['Медь', 'Алюминий'],
                'price_range': (50, 500)
            },
            {
                'name_template': 'Кабель ПВС {cores}x{size}',
                'cores': [2, 3, 4],
                'sizes': ['0.75', '1', '1.5', '2.5'],
                'manufacturers': ['IEK', 'АВВ'],
                'countries': ['Россия', 'Китай'],
                'materials': ['Медь'],
                'price_range': (30, 200)
            },
            {
                'name_template': 'Кабель UTP кат. {cat}',
                'cores': [4],
                'sizes': ['5E', '6', '6A'],
                'manufacturers': ['IEK', 'АВВ', 'Hyperline'],
                'countries': ['Китай', 'Россия'],
                'materials': ['Медь'],
                'price_range': (40, 150)
            },
            {
                'name_template': 'Труба гофрированная ПНД D{size}мм',
                'cores': [0],
                'sizes': ['16', '20', '25', '32'],
                'manufacturers': ['DKC', 'IEK'],
                'countries': ['Россия', 'Китай'],
                'materials': ['Пластик'],
                'price_range': (20, 100)
            },
            {
                'name_template': 'Розетка {type} {color}',
                'cores': [0],
                'sizes': ['одинарная', 'двойная', 'тройная'],
                'manufacturers': ['Legrand', 'Schneider Electric', 'IEK'],
                'countries': ['Франция', 'Германия', 'Россия'],
                'materials': ['Пластик'],
                'price_range': (150, 800)
            }
        ]

        for i in range(products_to_create):
            sub_cat = random.choice(sub_categories)
            template = random.choice(product_templates)
            
            # Product nomini yaratish
            if '{cores}' in template['name_template'] and '{size}' in template['name_template']:
                cores = random.choice(template['cores'])
                size = random.choice(template['sizes'])
                name = template['name_template'].format(cores=cores, size=size)
                number_of_cores = cores if cores > 0 else 0
            elif '{cat}' in template['name_template']:
                cat = random.choice(template['sizes'])
                name = template['name_template'].format(cat=cat)
                number_of_cores = 4
            elif '{size}' in template['name_template']:
                size = random.choice(template['sizes'])
                name = template['name_template'].format(size=size)
                number_of_cores = 0
            elif '{type}' in template['name_template'] and '{color}' in template['name_template']:
                ptype = random.choice(template['sizes'])
                color = random.choice(['белый', 'слоновая кость', 'серый', 'черный'])
                name = template['name_template'].format(type=ptype, color=color)
                number_of_cores = 0
            else:
                name = fake.sentence(nb_words=4)[:-1]
                number_of_cores = 0

            manufacturer = random.choice(template['manufacturers'])
            country = random.choice(template['countries'])
            material = random.choice(template['materials']) if number_of_cores > 0 else None
            
            # Yangi fieldlar uchun ma'lumotlar
            cable_cross_section = None
            outer_insulation = None
            conductor_insulation = None
            outer_sheath = None
            color_value = None
            model_ver = None
            
            # Kabel va provod uchun
            if number_of_cores > 0 or 'кабель' in name.lower() or 'провод' in name.lower():
                # Сечение кабеля
                cable_cross_section = Decimal(str(round(random.uniform(0.5, 10.0), 2)))
                # Материал внешней изоляции
                outer_insulation = random.choice(['ПВХ', 'ПЭ', 'Резина', 'Полиэтилен', 'ПВХнг-LS', 'ПВХнг(А)-LS'])
                # Материал изоляции проводника
                conductor_insulation = random.choice(['ПВХ', 'ПЭ', 'Резина', 'Полиэтилен', 'ПВХнг'])
                # Материал внешней оболочки
                outer_sheath = random.choice(['ПВХ', 'ПЭ', 'Резина', 'Полиэтилен', 'ПВХнг-LS'])
                # Цвет
                color_value = random.choice(['серый', 'белый', 'черный', 'синий', 'красный', 'желтый', 'зеленый', 'коричневый'])
                # Модель/исполнение
                model_ver = random.choice(['ВВГ', 'ВВГнг', 'ПВС', 'ПВСнг', 'NYM', 'КГ', 'ВБбШв', 'АВБбШв'])
            
            # Труба va kanal uchun
            elif 'труба' in name.lower() or 'канал' in name.lower() or 'металлорукав' in name.lower() or 'лотк' in name.lower():
                # Материал внешней оболочки
                outer_sheath = random.choice(['ПВХ', 'ПЭ', 'ПНД', 'ПВД', 'Металл'])
                # Цвет
                color_value = random.choice(['серый', 'белый', 'черный', 'синий', 'оранжевый'])
                # Модель/исполнение
                model_ver = random.choice(['ПНД', 'ПВХ', 'Гофрированная', 'Гладкая', 'Гибкая'])
            
            # Rozetka, vikluchatel va boshqa elektronika uchun
            elif 'розетка' in name.lower() or 'выключатель' in name.lower() or 'диммер' in name.lower() or 'автоматический' in name.lower():
                # Цвет
                color_value = random.choice(['белый', 'слоновая кость', 'серый', 'черный', 'коричневый', 'черный'])
                # Модель/исполнение
                model_ver = random.choice(['Стандарт', 'Премиум', 'Эконом', 'Профессиональный', 'Умный'])
            
            # Lampochka va svetilnik uchun
            elif 'лампа' in name.lower() or 'светильник' in name.lower() or 'прожектор' in name.lower() or 'фонарь' in name.lower():
                # Цвет
                color_value = random.choice(['белый', 'теплый белый', 'холодный белый', 'желтый', 'многоцветный'])
                # Модель/исполнение
                model_ver = random.choice(['LED', 'E27', 'GU10', 'MR16', 'G9', 'G4'])
            
            # Klemma, nakonechnik va boshqalar uchun
            elif 'наконечник' in name.lower() or 'гильза' in name.lower() or 'клемм' in name.lower() or 'муфт' in name.lower():
                # Материал внешней оболочки
                outer_sheath = random.choice(['Медь', 'Алюминий', 'Латунь', 'Олово'])
                # Модель/исполнение
                model_ver = random.choice(['ТМЛ', 'НШВИ', 'НКИ', 'ГСИ', 'Стандарт'])
            
            # Korobka va boks uchun
            elif 'коробка' in name.lower() or 'бокс' in name.lower():
                # Материал внешней оболочки
                outer_sheath = random.choice(['Пластик', 'Металл', 'ПВХ'])
                # Цвет
                color_value = random.choice(['белый', 'серый', 'черный'])
                # Модель/исполнение
                model_ver = random.choice(['Стандарт', 'Влагозащищенный', 'Пылезащищенный'])
            
            # Umumiy holat uchun
            else:
                # Цвет (ixtiyoriy)
                if random.choice([True, False]):
                    color_value = random.choice(['белый', 'серый', 'черный', 'синий', 'красный'])
                # Модель/исполнение
                model_ver = fake.bothify(text='MOD-####').upper()
            
            price_min, price_max = template['price_range']
            price = Decimal(str(round(random.uniform(price_min, price_max), 2)))

            product = Product.objects.create(
                sub_category=sub_cat,
                name=name,
                sku=fake.unique.bothify(text='SKU-####-????').upper(),
                description=fake.paragraph(nb_sentences=random.randint(3, 7)),
                price_per_meter=price,
                stock=random.randint(50, 1000),
                manufacturer=manufacturer,
                country_of_origin=country,
                number_of_cores=number_of_cores,
                conductor_material=material,
                cable_cross_section=cable_cross_section,
                outer_insulation_material=outer_insulation,
                conductor_insulation_material=conductor_insulation,
                outer_sheath_material=outer_sheath,
                color=color_value,
                model_version=model_ver,
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            products.append(product)
            self.stdout.write(f"  ✓ Product yaratildi: {product.name}")

            # 4. ProductImage yaratish (3-5 ta rasm)
            num_images = random.randint(3, 5)
            for j in range(num_images):
                is_main = (j == 0)
                ProductImage.objects.create(
                    product=product,
                    image=create_dummy_image(f"product_{product.id}_img_{j+1}.png"),
                    is_main=is_main,
                    order=j
                )

            # 5. ProductMeterage yaratish (agar kerak bo'lsa)
            if number_of_cores > 0 or 'кабель' in name.lower() or 'труба' in name.lower():
                available_meterages = [10, 20, 50, 100, 200, 250, 500]
                num_meterages = random.randint(2, 4)
                selected_meterages = random.sample(available_meterages, k=min(num_meterages, len(available_meterages)))
                
                for value in selected_meterages:
                    if not ProductMeterage.objects.filter(product=product, value=value).exists():
                        ProductMeterage.objects.create(
                            product=product,
                            value=value,
                            is_active=True
                        )

        # 6. Favourite yaratish
        if users and products:
            num_favourites = min(len(users) * 3, len(products), 15)
            for _ in range(num_favourites):
                user = random.choice(users)
                product = random.choice(products)
                if not Favourite.objects.filter(user=user, product=product).exists():
                    Favourite.objects.create(user=user, product=product)

        self.stdout.write(self.style.SUCCESS("\n" + "="*50))
        self.stdout.write(self.style.SUCCESS("Fake ma'lumotlar muvaffaqiyatli yaratildi!"))
        self.stdout.write(self.style.SUCCESS(f"✓ {len(main_categories)} MainCategory"))
        self.stdout.write(self.style.SUCCESS(f"✓ {len(sub_categories)} SubCategory"))
        self.stdout.write(self.style.SUCCESS(f"✓ {len(products)} Product"))
        self.stdout.write(self.style.SUCCESS("="*50))
