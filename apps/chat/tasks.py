"""
Taches Celery du chat : traitement en arriere-plan, jamais pendant la
requete de l'utilisateur, pour que l'envoi d'un message reste instantane
quel que soit le nombre d'utilisateurs actifs en meme temps.
"""

import io
import os

from django.core.files.base import ContentFile

from celery import shared_task
from PIL import Image

MAX_WIDTH = 1600
MAX_HEIGHT = 1600
JPEG_QUALITY = 85


@shared_task
def compress_image_attachment(attachment_id):
    """Redimensionne et recompresse une image uploadee, en arriere-plan.
    Ne touche jamais aux documents (PDF, Word) -- uniquement aux images."""
    from apps.chat.models import Attachment

    try:
        attachment = Attachment.objects.get(id=attachment_id)
    except Attachment.DoesNotExist:
        return

    if not attachment.file_type.startswith("image/"):
        return

    # Les GIF (souvent animes) ne sont pas recompresses pour ne pas
    # perdre l'animation -- on les laisse tels quels.
    if attachment.file_type == "image/gif":
        return

    try:
        image = Image.open(attachment.file)
        image = image.convert("RGB")
        image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        buffer.seek(0)

        original_name = os.path.splitext(attachment.file_name)[0]
        new_name = f"{original_name}.jpg"

        attachment.file.save(new_name, ContentFile(buffer.read()), save=False)
        attachment.file_type = "image/jpeg"
        attachment.file_size = attachment.file.size
        attachment.save(update_fields=["file", "file_type", "file_size"])
    except Exception:
        # Si la compression echoue pour une raison quelconque (image
        # corrompue, format inattendu...), on garde le fichier original
        # plutot que de faire echouer tout le processus.
        pass
