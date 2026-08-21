import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LearningModule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=300)),
                ("order", models.PositiveIntegerField()),
                ("is_user_edited", models.BooleanField(default=False)),
                ("document", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="modules",
                    to="documents.document",
                )),
            ],
            options={"ordering": ["order"]},
        ),
        migrations.CreateModel(
            name="Chapter",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=300)),
                ("order", models.PositiveIntegerField()),
                ("is_user_edited", models.BooleanField(default=False)),
                ("module", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chapters",
                    to="learning.learningmodule",
                )),
            ],
            options={"ordering": ["order"]},
        ),
        migrations.AddConstraint(
            model_name="learningmodule",
            constraint=models.UniqueConstraint(
                fields=("document", "order"),
                name="unique_module_order_per_document",
            ),
        ),
        migrations.AddConstraint(
            model_name="chapter",
            constraint=models.UniqueConstraint(
                fields=("module", "order"),
                name="unique_chapter_order_per_module",
            ),
        ),
    ]
