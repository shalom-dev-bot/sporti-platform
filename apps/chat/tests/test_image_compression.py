"""
Tests de la compression/redimensionnement automatique des images.

Verifie que :
- une grande image est redimensionnee sous la limite maximale ;
- le type de fichier devient bien image/jpeg ;
- la taille du fichier diminue ;
- un GIF n'est jamais touche (pour ne pas casser une animation) ;
- un document (non-image) n'est jamais touche.
"""

import io

from django.core.files.base import ContentFile
from django.test import TestCase

from PIL import Image

from apps.accounts.models import User
from apps.chat.models import Attachment, Conversation, Message
from apps.chat.tasks import compress_image_attachment


class ImageCompressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="compress_test", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation = Conversation.objects.create(client=self.user)
        self.message = Message.objects.create(
            conversation=self.conversation, sender=self.user, content=""
        )

    def _create_attachment(self, size, file_type, file_name, fmt):
        image = Image.new("RGB", size, color="red")
        buffer = io.BytesIO()
        image.save(buffer, format=fmt)
        buffer.seek(0)
        return Attachment.objects.create(
            message=self.message,
            file=ContentFile(buffer.read(), name=file_name),
            file_name=file_name,
            file_type=file_type,
            file_size=buffer.getbuffer().nbytes,
        )

    def test_grande_image_est_redimensionnee(self):
        attachment = self._create_attachment((2000, 2000), "image/png", "grande.png", "PNG")

        compress_image_attachment(attachment.id)

        attachment.refresh_from_db()
        compressed_image = Image.open(attachment.file)
        width, height = compressed_image.size
        self.assertLessEqual(width, 1600)
        self.assertLessEqual(height, 1600)

    def test_type_devient_jpeg(self):
        attachment = self._create_attachment((2000, 2000), "image/png", "grande.png", "PNG")

        compress_image_attachment(attachment.id)

        attachment.refresh_from_db()
        self.assertEqual(attachment.file_type, "image/jpeg")

    def test_taille_du_fichier_diminue(self):
        attachment = self._create_attachment((2000, 2000), "image/png", "grande.png", "PNG")
        original_size = attachment.file_size

        compress_image_attachment(attachment.id)

        attachment.refresh_from_db()
        self.assertLess(attachment.file_size, original_size)

    def test_gif_nest_jamais_compresse(self):
        attachment = self._create_attachment((2000, 2000), "image/gif", "anime.gif", "GIF")
        original_type = attachment.file_type

        compress_image_attachment(attachment.id)

        attachment.refresh_from_db()
        self.assertEqual(attachment.file_type, original_type)

    def test_document_nest_jamais_touche(self):
        attachment = Attachment.objects.create(
            message=self.message,
            file=ContentFile(b"contenu pdf factice", name="document.pdf"),
            file_name="document.pdf",
            file_type="application/pdf",
            file_size=20,
        )
        original_size = attachment.file_size

        compress_image_attachment(attachment.id)

        attachment.refresh_from_db()
        self.assertEqual(attachment.file_size, original_size)
        self.assertEqual(attachment.file_type, "application/pdf")

    def test_attachment_inexistant_ne_plante_pas(self):
        # Ne doit lever aucune exception, meme avec un ID invalide.
        compress_image_attachment(999999)
