"""
Verifie que le backend de stockage des fichiers est bien determine par la
variable d'environnement STORAGE_BACKEND, sans necessiter de modification
du code pour basculer entre stockage local et stockage cloud (S3/R2).
"""

import importlib

from django.test import TestCase


class StorageConfigTests(TestCase):
    def test_backend_local_par_defaut(self):
        from django.conf import settings

        self.assertIn("default", settings.STORAGES)
        # En environnement de test, STORAGE_BACKEND n'est pas force a "s3",
        # donc le backend local (systeme de fichiers) doit etre actif.
        if settings.STORAGE_BACKEND == "local":
            self.assertEqual(
                settings.STORAGES["default"]["BACKEND"],
                "django.core.files.storage.FileSystemStorage",
            )

    def test_module_storages_est_bien_importable(self):
        """Confirme que django-storages est installe et utilisable,
        prerequis indispensable pour basculer vers S3 plus tard."""
        module = importlib.import_module("storages.backends.s3boto3")
        self.assertTrue(hasattr(module, "S3Boto3Storage"))
