from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0003_storefrontconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="storefrontconfig",
            name="hero_effect",
            field=models.CharField(
                choices=[
                    ("none", "No animation"),
                    ("rise", "Rise and fade"),
                    ("fade", "Soft fade"),
                    ("zoom", "Gentle zoom"),
                    ("focus", "Focus reveal"),
                ],
                default="rise",
                max_length=10,
                verbose_name="Hero text effect",
            ),
        ),
    ]
