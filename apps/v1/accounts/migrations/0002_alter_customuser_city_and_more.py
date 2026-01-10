# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Город'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='street',
            field=models.TextField(blank=True, null=True, verbose_name='Улица'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='flat',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Квартира'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='house',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Дом'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='index',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Индекс'),
        ),
    ]
