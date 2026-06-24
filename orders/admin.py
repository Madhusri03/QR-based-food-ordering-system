from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('id', 'table', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'table__table_number')
    readonly_fields = ('created_at',)

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
