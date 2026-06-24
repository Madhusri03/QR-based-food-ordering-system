from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Food(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='dishes')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='foods/')
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver([post_save, post_delete], sender=Category)
def clear_category_cache(sender, instance, **kwargs):
    cache.delete('menu_categories')

@receiver([post_save, post_delete], sender=Food)
def clear_food_cache(sender, instance, **kwargs):
    cache.delete('menu_foods')
