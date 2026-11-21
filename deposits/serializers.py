from rest_framework import serializers
from .models import Bin, Deposit, SystemSetting, WiFiSession


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = '__all__'
        # Prevent clients from spoofing server-managed timestamps or computed values
        read_only_fields = ['id', 'created_at']

    def validate_weight(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Deposit weight must be greater than zero.")
        return value

    def validate(self, attrs):
        bin_obj = attrs.get('bin')
        if bin_obj is not None and getattr(bin_obj, 'is_active', True) is False:
            raise serializers.ValidationError({"bin": "Cannot record a deposit for an inactive bin."})
        return attrs


class WiFiSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WiFiSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'session_start']


class BinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = '__all__'
        read_only_fields = ['id']