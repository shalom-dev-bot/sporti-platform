"""
Tests de l'upload de pieces jointes (images, documents, messages vocaux).

Verifie que :
- un client peut envoyer une piece jointe dans SA conversation ;
- un fichier audio (vocal) est accepte ;
- un type de fichier non autorise est rejete ;
- un client ne peut pas envoyer de fichier dans la conversation d'un AUTRE client ;
- le message + l'attachment sont bien crees en base.
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

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
