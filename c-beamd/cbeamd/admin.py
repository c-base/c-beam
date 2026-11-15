from cbeamd.models import User, LTE, Subscription, Device
from cbeamd.devices import assign_key
from django.contrib import admin, messages

admin.site.register(User)
admin.site.register(LTE)
admin.site.register(Subscription)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    registration of rfid readers. the key is generated when a device is added
    and shown once, in the success message; `rotate key` issues a new one for
    the selected devices the same way.
    """
    list_display = ('name', 'device_id', 'location', 'enabled', 'last_seen', 'last_ip')
    list_filter = ('enabled',)
    search_fields = ('name', 'device_id', 'location')
    readonly_fields = ('created', 'last_seen', 'last_ip')
    actions = ('rotate_key',)

    def save_model(self, request, obj, form, change):
        if not change:
            key = assign_key(obj)
            self._show_key(request, obj, key)
        super().save_model(request, obj, form, change)

    @admin.action(description="rotate key (issues a new key, the old one stops working)")
    def rotate_key(self, request, queryset):
        for device in queryset:
            key = assign_key(device)
            device.save(update_fields=['key_hash'])
            self._show_key(request, device, key)

    @staticmethod
    def _show_key(request, device, key):
        messages.warning(
            request,
            "key fu:r %s: %s — wird nur dieses eine mal angezeigt, jetzt in das gera:t u:bertragen"
            % (device, key),
        )
