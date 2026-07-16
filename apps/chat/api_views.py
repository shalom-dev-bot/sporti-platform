"""
Vues API du chat :
- Liste des conversations (reservee au staff, pour le dashboard).
- Historique paginee par curseur d'une conversation precise.

Securite : chaque vue verifie explicitement que l'utilisateur a le droit
de voir la conversation demandee (isolation stricte client <-> entreprise).
"""

from rest_framework import permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class MessageCursorPagination(CursorPagination):
    """Pagination par curseur : plus rapide et plus fiable qu'une pagination
    par numero de page sur une conversation qui grossit en continu."""

    page_size = 30
    ordering = "-created_at"


class ConversationListView(APIView):
    """Liste de toutes les conversations -- reservee au staff (dashboard)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"detail": "Acces reserve a l'entreprise."},
                status=status.HTTP_403_FORBIDDEN,
            )

        conversations = (
            Conversation.objects.select_related("client")
            .prefetch_related("messages")
            .order_by("-updated_at")
        )
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class ConversationHistoryView(APIView):
    """Historique paginee des messages d'une conversation precise.

    - Un client ne peut consulter que SA PROPRE conversation.
    - Un membre du staff peut consulter n'importe quelle conversation.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessageCursorPagination

    def get(self, request, conversation_id):
        conversation = Conversation.objects.filter(id=conversation_id).first()
        if conversation is None:
            return Response(
                {"detail": "Conversation introuvable."}, status=status.HTTP_404_NOT_FOUND
            )

        is_owner = conversation.client_id == request.user.id
        if not (is_owner or request.user.is_staff):
            return Response(
                {"detail": "Vous n'avez pas acces a cette conversation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        messages = (
            Message.objects.filter(conversation=conversation)
            .select_related("sender")
            .prefetch_related("attachments", "reactions")
            .order_by("-created_at")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(messages, request, view=self)
        serializer = MessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
