from django.contrib import admin
from .models import DeviceConfig, Telemetry

@admin.register(DeviceConfig)
class DeviceConfigAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'name', 'setpoint', 'last_seen')
    search_fields = ('device_id', 'name')

@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'device', 'temperature', 'duty_cycle', 'relay_active', 'door_open')
    list_filter = ('device', 'relay_active', 'door_open')
    readonly_fields = ('timestamp',)