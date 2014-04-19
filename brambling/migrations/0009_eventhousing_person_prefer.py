# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0008_eventhousing_home'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I/We would love to host', blank=True),
            preserve_default=True,
        ),
    ]