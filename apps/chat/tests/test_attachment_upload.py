"""
Tests de l'upload de pieces jointes (images, documents, messages vocaux).

Verifie que :
- un client peut envoyer une piece jointe dans SA conversation ;
- un fichier audio (vocal) est accepte ;
- un type de fichier non autorise est rejete ;
- un client ne peut pas envoyer de fichier dans la conversation d'un AUTRE client ;
- le message + l'attachment sont bien crees en base ;
- le contenu reel du fichier est valide, pas seulement son extension.
"""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from PIL import Image

from apps.accounts.models import User
from apps.chat.models import Attachment, Conversation, Message


class AttachmentUploadTests(TestCase):
    def setUp(self):
        self.client1 = User.objects.create_user(
            username="client_upload_a", password="MotDePasseSolide123", is_staff=False
        )
        self.client2 = User.objects.create_user(
            username="client_upload_b", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation = Conversation.objects.create(client=self.client1)

    def test_client_peut_envoyer_un_message_vocal(self):
        self.client.login(username="client_upload_a", password="MotDePasseSolide123")
        audio_file = SimpleUploadedFile(
            "message_vocal.mp3", b"contenu audio factice", content_type="audio/mpeg"
        )
        response = self.client.post(
            reverse("chat:api_attachment_upload", args=[self.conversation.id]),
            {"file": audio_file},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Attachment.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)

    def test_fichier_non_autorise_est_rejete(self):
        self.client.login(username="client_upload_a", password="MotDePasseSolide123")
        bad_file = SimpleUploadedFile(
            "virus.exe", b"contenu suspect", content_type="application/octet-stream"
        )
        response = self.client.post(
            reverse("chat:api_attachment_upload", args=[self.conversation.id]),
            {"file": bad_file},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_client_ne_peut_pas_envoyer_dans_conversation_dun_autre(self):
        self.client.login(username="client_upload_b", password="MotDePasseSolide123")
        audio_file = SimpleUploadedFile("vocal.mp3", b"contenu audio", content_type="audio/mpeg")
        response = self.client.post(
            reverse("chat:api_attachment_upload", args=[self.conversation.id]),
            {"file": audio_file},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_aucun_fichier_fourni_renvoie_erreur(self):
        self.client.login(username="client_upload_a", password="MotDePasseSolide123")
        response = self.client.post(
            reverse("chat:api_attachment_upload", args=[self.conversation.id]), {}
        )
        self.assertEqual(response.status_code, 400)


class UploadContentValidationTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="content_val_client", password="MotDePasseSolide123", is_staff=False
        )
        self.conversation = Conversation.objects.create(client=self.client_user)

    def test_faux_fichier_image_est_rejete_malgre_extension_correcte(self):
        """Un fichier texte renomme en .jpg doit etre detecte et rejete,
        meme si son extension semble valide."""
        self.client.login(username="content_val_client", password="MotDePasseSolide123")
        fake_image = SimpleUploadedFile(
            "photo.jpg",
            b"ceci n'est pas une image, juste du texte brut",
            content_type="image/jpeg",
        )
        response = self.client.post(
            reverse("chat:api_attachment_upload", args=[self.conversation.id]),
            {"file": fake_image},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_vraie_image_est_acceptee(self):
        """Une vraie image, meme minuscule, doit passer la validation."""
        self.client.login(username="content_val_client", password="MotDePasseSolide123")

        image = Image.new("RGB", (10, 10), color="blue")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        real_image = SimpleUploadedFile("vraie_photo.jpg", buffer.read(), content_type="image/jpeg")
        response = self.client.post(
            reverse("chat:api_attachment_upload", args=[self.conversation.id]),
            {"file": real_image},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Attachment.objects.count(), 1)
