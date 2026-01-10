import os
import random
import io
from PIL import Image

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from faker import Faker

from apps.v1.sites.models import Contact, Partner

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
    help = 'База данныхни Contact va Partner fake ma\'lumotlari bilan to\'ldiradi'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Mavjud ma\'lumotlarni tozalash',
        )
        parser.add_argument(
            '--partners',
            type=int,
            default=5,
            help='Yaratiladigan partnerlar soni (default: 5)',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        num_partners = options['partners']
        
        # 1. Contact ma'lumotlarini yaratish
        self.stdout.write(self.style.WARNING("Contact ma'lumotlari yaratilmoqda..."))
        
        if clear_data:
            Contact.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Mavjud Contact ma'lumotlari tozalandi."))
        
        # Contact yaratish (faqat bitta bo'lishi kerak)
        if not Contact.objects.exists():
            contact = Contact.objects.create(
                zip_code=fake.postcode(),
                city=fake.city(),
                street=fake.street_name(),
                building_number=str(random.randint(1, 200)),
                office_number=str(random.randint(1, 50)) if random.choice([True, False]) else None,
                phone=fake.phone_number(),
                email=fake.company_email(),
                working_hours_weekday="Пн - Пт: 9.00 - 18.00",
                working_hours_weekend="Сб - Вс: выходные",
                map_iframe='<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2996.3634803458!2d69.24045131528767!3d41.31108197927046!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x38ae8b0cc379e9c3%3A0xa5a9323b4aa5cb98!2z0KLQsNGI0LrQtdC90YI!5e0!3m2!1sru!2s!4v1234567890" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>'
            )
            self.stdout.write(self.style.SUCCESS(f"[OK] Contact yaratildi: {contact.get_full_address()}"))
        else:
            self.stdout.write(self.style.WARNING("Contact allaqachon mavjud. O'zgartirish uchun --clear flag'ini ishlating."))
        
        # 2. Partner ma'lumotlarini yaratish
        self.stdout.write(self.style.WARNING(f"\nPartner ma'lumotlari yaratilmoqda ({num_partners} ta)..."))
        
        if clear_data:
            Partner.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Mavjud Partner ma'lumotlari tozalandi."))
        
        partners_created = 0
        for i in range(num_partners):
            partner = Partner.objects.create(
                image=create_dummy_image(f"partner_{i+1}.png", size=(400, 300))
            )
            partners_created += 1
            self.stdout.write(f"  [OK] Partner #{partner.id} yaratildi")
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*50))
        self.stdout.write(self.style.SUCCESS("Fake ma'lumotlar muvaffaqiyatli yaratildi!"))
        self.stdout.write(self.style.SUCCESS(f"[OK] {Contact.objects.count()} Contact"))
        self.stdout.write(self.style.SUCCESS(f"[OK] {Partner.objects.count()} Partner"))
        self.stdout.write(self.style.SUCCESS("="*50))
