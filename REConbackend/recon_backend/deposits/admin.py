from django.contrib import admin
from .models import Bin, Deposit, SystemSetting, WiFiSession


@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('bin_code', 'status', 'created_at')
    search_fields = ('bin_code',)
    ordering = ('-created_at',)


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'minimum_deposit_grams',
        'tier_one_max_grams',
        'tier_one_multiplier',
        'tier_two_max_grams',
        'maximum_minutes_per_transaction',
        'daily_session_limit',
        'updated_at',
    )
    ordering = ('-updated_at',)


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('deposit_code', 'bin_id', 'weight_g', 'status', 'min_earned', 'created_at')
    search_fields = ('deposit_code', 'bin_id')
    ordering = ('-created_at',)


@admin.register(WiFiSession)
class WiFiSessionAdmin(admin.ModelAdmin):
    list_display = (
        'session_code',
        'deposit_code',
        'mac_address',
        'minutes_allocated',
        'time_remaining_sec',
        'status',
        'created_at',
    )
    search_fields = ('session_code', 'deposit_code', 'mac_address')
    ordering = ('-created_at',)