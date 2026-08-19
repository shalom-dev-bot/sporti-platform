from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def clear_old_visits(apps, schema_editor):
    # L'ancien modele (un compteur agrege par jour, incremente a chaque
    # requete, admin inclus) ne correspond a rien dans le nouveau schema
    # (une ligne par client distinct et par jour) -- ces donnees etaient
    # de toute facon fausses (comptaient chaque requete API/AJAX et les
    # visites de l'admin lui-meme), on repart simplement a zero.
    SiteVisit = apps.get_model("dashboard", "SiteVisit")
    SiteVisit.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(clear_old_visits, migrations.RunPython.noop),
        migrations.RemoveField(model_name="sitevisit", name="count"),
        migrations.AlterField(
            model_name="sitevisit",
            name="date",
            field=models.DateField(db_index=True),
        ),
        migrations.AddField(
            model_name="sitevisit",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=None, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sitevisit",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                null=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="sitevisit",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="sitevisit",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddConstraint(
            model_name="sitevisit",
            constraint=models.UniqueConstraint(
                fields=["date", "user"], name="unique_visit_per_user_per_day"
            ),
        ),
    ]
