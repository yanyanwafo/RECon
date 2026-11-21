import re
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Bin, Deposit, SystemSetting, WiFiSession
from .serializers import (
    BinSerializer,
    DepositSerializer,
    SystemSettingSerializer,
    WiFiSessionSerializer,
)

MAC_REGEX = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


@api_view(['POST'])
@permission_classes([AllowAny])  # Remove or change if Wi-Fi connection requires auth
def connect_wifi_view(request):
    raw_code = request.data.get('session_code')
    raw_mac = request.data.get('mac_address', '')

    if not isinstance(raw_code, str) or not raw_code.strip():
        return Response({"error": "Session code is required."}, status=status.HTTP_400_BAD_REQUEST)

    session_code = raw_code.strip()[:64]
    mac_address = raw_mac.strip().upper() if isinstance(raw_mac, str) else ''

    if mac_address and not MAC_REGEX.match(mac_address):
        return Response({"error": "Invalid MAC address format."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        try:
            session = WiFiSession.objects.select_for_update().get(session_code=session_code)
        except WiFiSession.DoesNotExist:
            return Response({"error": "Invalid session code."}, status=status.HTTP_404_NOT_FOUND)

        # Prevent reusing expired/completed sessions or hijacking an active one from another MAC
        if getattr(session, 'status', None) in ['EXPIRED', 'USED', 'COMPLETED']:
            return Response({"error": "Session code is no longer valid."}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(session, 'status', None) == 'ACTIVE' and session.mac_address and mac_address:
            if session.mac_address.upper() != mac_address:
                return Response({"error": "Session code is already active on another device."}, status=status.HTTP_409_CONFLICT)

        remaining = getattr(session, 'time_remaining_sec', None)
        if remaining is not None and remaining <= 0:
            session.status = 'EXPIRED'
            session.save(update_fields=['status'])
            return Response({"error": "Session has expired."}, status=status.HTTP_400_BAD_REQUEST)

        session.status = 'ACTIVE'
        if mac_address:
            session.mac_address = mac_address
        if not session.session_start:
            session.session_start = timezone.now()
        session.save()

    return Response({
        "success": True,
        "message": "Successfully connected to WiFi!",
        "session_code": session.session_code,
        "time_remaining_sec": session.time_remaining_sec,
        "status": session.status,
    }, status=status.HTTP_200_OK)


class DepositListView(generics.ListCreateAPIView):
    queryset = Deposit.objects.all().order_by('-created_at')
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]


class BinListView(generics.ListCreateAPIView):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer
    permission_classes = [IsAuthenticated]


class SystemSettingListView(generics.ListAPIView):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAuthenticated]