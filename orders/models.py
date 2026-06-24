from django.db import models
from customer.models import Table
from menu.models import Food

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Served', 'Served'),
    )
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - Table {self.table.table_number} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food = models.ForeignKey(Food, on_delete=models.SET_NULL, null=True, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        food_name = self.food.name if self.food else "Deleted Item"
        return f"{self.quantity} x {food_name} for Order #{self.order.id}"

    @property
    def subtotal(self):
        return self.price * self.quantity

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Order)
@receiver(post_delete, sender=Order)
def clear_order_caches(sender, instance, **kwargs):
    cache.delete('kitchen_active_orders')
    cache.delete('kitchen_completed_orders')
    
    # Also delete admin stats cache for current date
    from django.utils import timezone
    now = timezone.now()
    cache.delete(f"admin_stats_{now.strftime('%Y%m%d')}")

@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def clear_best_sellers_cache(sender, instance, **kwargs):
    cache.delete('admin_best_sellers')
