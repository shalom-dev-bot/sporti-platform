"""
Vues API du chat :
- Liste des conversations (reservee au staff, pour le dashboard).
- Historique paginee par curseur d'une conversation precise.
- Upload de pieces jointes (images, documents, messages vocaux).

Securite : chaque vue verifie explicitement que l'utilisateur a le droit
de voir/modifier la conversation demandee (isolation stricte client <-> entreprise).
"""

import os

from django.conf import settings
from django.utils.decorators import method_decorator

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Attachment, Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .tasks import compress_image_attachment


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


@method_decorator(ratelimit(key="user", rate="20/m", method="POST", block=True), name="post")
class AttachmentUploadView(APIView):
    """Upload d'une piece jointe (image, document, ou message vocal) dans
    une conversation. Cree le Message + l'Attachment, puis diffuse le
    resultat en temps reel aux deux parties via WebSocket.

    Limite a 20 uploads par minute et par utilisateur, pour eviter le
    spam et la saturation du stockage/traitement Celery."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, conversation_id):
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

        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            return Response({"detail": "Aucun fichier fourni."}, status=status.HTTP_400_BAD_REQUEST)

        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            return Response(
                {"detail": f"Type de fichier non autorise : {extension}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validation du contenu reel du fichier, pas seulement de son
        # extension : un fichier malveillant renomme en .jpg doit etre
        # rejete, meme si l'extension semble correcte.
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        if extension in image_extensions:
            from PIL import Image, UnidentifiedImageError

            try:
                uploaded_file.seek(0)
                with Image.open(uploaded_file) as img:
                    img.verify()
                uploaded_file.seek(0)
            except (UnidentifiedImageError, OSError):
                return Response(
                    {"detail": "Le fichier ne correspond pas a une image valide."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if uploaded_file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            return Response(
                {"detail": "Fichier trop volumineux (max 10 Mo)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = Message.objects.create(conversation=conversation, sender=request.user, content="")
        attachment = Attachment.objects.create(
            message=message,
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_type=uploaded_file.content_type or "application/octet-stream",
            file_size=uploaded_file.size,
        )

        payload = {
            "id": message.id,
            "sender_id": request.user.id,
            "sender_name": str(request.user),
            "is_staff": request.user.is_staff,
            "content": "",
            "status": message.status,
            "created_at": message.created_at.isoformat(),
            "attachment": {
                "id": attachment.id,
                "file_url": attachment.file.url,
                "file_name": attachment.file_name,
                "file_type": attachment.file_type,
                "file_size": attachment.file_size,
            },
        }

        if attachment.file_type.startswith("image/") and attachment.file_type != "image/gif":
            compress_image_attachment.delay(attachment.id)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conversation_{conversation.id}",
            {"type": "chat.message", "payload": payload},
        )

        return Response(payload, status=status.HTTP_201_CREATED)
