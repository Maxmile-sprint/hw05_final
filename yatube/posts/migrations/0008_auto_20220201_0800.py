# Generated by Django 2.2.16 on 2022-02-01 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220131_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, help_text='Загрузите картинку', upload_to='posts/', verbose_name='Картинка'),
        ),
    ]
