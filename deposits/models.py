import math
from decimal import Decimal
from django.db import models


class Bin(models.Model):
    bin_code = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('READY', 'Ready'),
            ('FULL', 'Full'),
            ('MAINTENANCE', 'Maintenance'),
        ],
        default='READY',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bin_code} ({self.status})"


class SystemSetting(models.Model):
    minimum_deposit_grams = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    tier_one_max_grams = models.DecimalField(max_digits=6, decimal_places=2, default=20.00)
    tier_one_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=3.00)
    tier_two_max_grams = models.DecimalField(max_digits=6, decimal_places=2, default=50.00)
    tier_two_base_minutes = models.IntegerField(default=60)
    tier_two_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=2.00)
    maximum_minutes_per_transaction = models.IntegerField(default=480)
    session_expiry_hours = models.IntegerField(default=24)
    bin_fill_alert_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=90.00)
    daily_session_limit = models.IntegerField(default=3)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"System Settings (Updated {self.updated_at:%Y-%m-%d %H:%M})" if self.updated_at else "System Settings"


class Deposit(models.Model):
    deposit_code = models.CharField(max_length=50, unique=True)
    bin_id = models.CharField(max_length=50)
    weight_g = models.FloatField(default=0.0, help_text="Weight of paper in grams")
    status = models.CharField(
        max_length=20,
        choices=[
            ('VALID', 'Valid'),
            ('TOO_LIGHT', 'Too Light'),
            ('INVALID', 'Invalid / Non-paper'),
        ],
        default='VALID',
    )
    min_earned = models.FloatField(default=0.0, help_text="WiFi reward minutes earned")
    created_at = models.DateTimeField(auto_now_add=True)

    def _calculate_reward(self):
        raw_weight = float(self.weight_g)
        if math.isnan(raw_weight) or math.isinf(raw_weight) or raw_weight < 0:
            raise ValueError("weight_g must be a valid non-negative number.")

        settings_obj = SystemSetting.objects.order_by('-id').first()
        min_grams = float(settings_obj.minimum_deposit_grams) if settings_obj else 5.0
        t1_max = float(settings_obj.tier_one_max_grams) if settings_obj else 20.0
        t1_mult = float(settings_obj.tier_one_multiplier) if settings_obj else 3.0
        t2_max = float(settings_obj.tier_two_max_grams) if settings_obj else 50.0
        t2_base = float(settings_obj.tier_two_base_minutes) if settings_obj else 60.0
        t2_mult = float(settings_obj.tier_two_multiplier) if settings_obj else 2.0
        max_mins = float(settings_obj.maximum_minutes_per_transaction) if settings_obj else 480.0

        # Keep INVALID status if explicitly set on a non-positive/invalid record
        if self.status == 'INVALID' and raw_weight <= 0:
            return 'INVALID', 0.0

        if raw_weight < min_grams:
            return 'TOO_LIGHT', 0.0

        if raw_weight < t1_max:
            earned = raw_weight * t1_mult
        elif raw_weight < t2_max:
            earned = t2_base + ((raw_weight - t1_max) * t2_mult)
        else:
            earned = max_mins

        earned = min(max(0.0, earned), max_mins)
        return 'VALID', round(earned, 2)

    def save(self, *args, **kwargs):
        status_val, earned_mins = self._calculate_reward()
        self.status = status_val
        self.min_earned = earned_mins
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.deposit_code} - {self.weight_g}g ({self.status})"


class WiFiSession(models.Model):
    session_code = models.CharField(max_length=50, unique=True)
    deposit = models.ForeignKey(Deposit, on_delete=models.CASCADE, null=True, blank=True)
    deposit_code = models.CharField(max_length=50, blank=True, null=True)
    mac_address = models.CharField(max_length=50, blank=True, null=True)
    minutes_allocated = models.IntegerField(default=30)
    time_remaining_sec = models.IntegerField(default=1800)
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('PAUSED', 'Paused'),
            ('EXPIRED', 'Expired'),
        ],
        default='ACTIVE',
    )
    session_start = models.DateTimeField(blank=True, null=True)
    session_end = models.DateTimeField(blank=True, null=True)
    paused_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.deposit and not self.deposit_code:
            self.deposit_code = self.deposit.deposit_code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.session_code} - {self.status}"