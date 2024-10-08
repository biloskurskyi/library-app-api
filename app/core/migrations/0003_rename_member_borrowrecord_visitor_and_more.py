# Generated by Django 4.2 on 2024-09-04 16:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_book_borrowrecord'),
    ]

    operations = [
        migrations.RenameField(
            model_name='borrowrecord',
            old_name='member',
            new_name='visitor',
        ),
        migrations.AlterUniqueTogether(
            name='book',
            unique_together={('title', 'author')},
        ),
    ]
