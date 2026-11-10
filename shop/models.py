from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return f"{self.brand} - {self.name}"

class StorefrontConfig(models.Model):
    HERO_EFFECT_CHOICES = [
        ("none", "No animation"),
        ("rise", "Rise and fade"),
        ("fade", "Soft fade"),
        ("zoom", "Gentle zoom"),
        ("focus", "Focus reveal"),
    ]

    title = models.CharField(max_length=200, default="REVOLUTIONARY TAILORING")
    subtitle = models.CharField(max_length=200, default="The Autumn / Winter Collection")
    banner_image = models.ImageField(upload_to='storefront/', help_text="Upload your main full-page header image here.")
    hero_effect = models.CharField(
        max_length=10,
        choices=HERO_EFFECT_CHOICES,
        default="rise",
        verbose_name="Hero text effect",
    )

    class Meta:
        verbose_name = "Storefront Configuration"
        verbose_name_plural = "Storefront Configuration"

    def __str__(self):
        return "Main Storefront Settings"
# Create your models here.
