from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer

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
