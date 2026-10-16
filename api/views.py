from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .permissions import IsInternalService
from .serializers import InternalNotificationCreateSerializer, NotificationSerializer

TRUE_VALUES = {"true", "1", "yes"}


def _get_user_notifications(request):
    """Only the caller's own notifications: the core privacy rule."""
    return Notification.objects.filter(recipient_user_id=request.user.id)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Simple liveness endpoint used by Docker / reverse proxy / teammates."""
    return Response({"status": "ok", "service": "notifications"})


class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/: the caller's notifications, newest first."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = _get_user_notifications(self.request)
        unread_param = self.request.query_params.get("unread", "").lower()
        if unread_param in TRUE_VALUES:
            queryset = queryset.filter(read_at__isnull=True)
        return queryset


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/"""

    def get(self, request):
        unread_count = _get_user_notifications(request).filter(read_at__isnull=True).count()
        return Response({"unread_count": unread_count})


class MarkReadView(APIView):
    """PATCH /api/notifications/{id}/read/: idempotent, recipient only."""

    def patch(self, request, pk):
        # Someone else's notification gives 404 (existence is not leaked).
        notification = get_object_or_404(_get_user_notifications(request), pk=pk)

        if notification.read_at is None:
            # Conditional update keeps the first read_at even with concurrent requests.
            _get_user_notifications(request).filter(pk=pk, read_at__isnull=True).update(
                read_at=timezone.now()
            )
            notification.refresh_from_db()

        return Response(NotificationSerializer(notification).data)


class InternalNotificationCreateView(APIView):
    """POST /api/internal/notifications/: trusted services only.

    Idempotent: the same deduplication_key never creates a second notification.
    201 = created, 200 = already existed (the existing one is returned unchanged).
    """

    # User credentials are not accepted here: only the service token counts.
    authentication_classes = []
    permission_classes = [IsInternalService]

    def post(self, request):
        serializer = InternalNotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = dict(serializer.validated_data)
        deduplication_key = data.pop("deduplication_key")

        # get_or_create also survives two simultaneous requests with the same key:
        # the database unique constraint decides and the loser reads the winner's row.
        notification, created = Notification.objects.get_or_create(
            deduplication_key=deduplication_key,
            defaults=data,
        )

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            InternalNotificationCreateSerializer(notification).data,
            status=response_status,
        )
