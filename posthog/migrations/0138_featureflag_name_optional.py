# Generated by Django 3.0.11 on 2021-03-19 23:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0137_team_timezone"),
    ]

    operations = [
        migrations.AlterField(model_name="featureflag", name="name", field=models.TextField(blank=True),),
    ]
