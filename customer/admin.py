from django.contrib import admin
from .models import Table


class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'is_occupied', 'occupied_at', 'qr_code')
    list_filter = ('is_occupied',)
    readonly_fields = ('qr_code', 'occupied_at')
    actions = ['free_tables']

    @admin.action(description='Free selected tables (mark as available)')
    def free_tables(self, request, queryset):
        updated = queryset.update(is_occupied=False, occupied_at=None)
        self.message_user(request, f"{updated} table(s) freed successfully.")


admin.site.register(Table, TableAdmin)
