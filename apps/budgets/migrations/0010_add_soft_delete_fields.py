# Generated manually for soft delete functionality

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('budgets', '0009_budgetsplit'),
    ]

    operations = [
        # Add soft delete fields to Budget model
        migrations.AddField(
            model_name='budget',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='When this budget was soft deleted', null=True),
        ),
        migrations.AddField(
            model_name='budget',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who deleted this budget',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deleted_budgets',
                to=settings.AUTH_USER_MODEL
            ),
        ),

        # Create indexes for optimization
        migrations.RunSQL(
            sql=[
                "CREATE INDEX IF NOT EXISTS idx_budget_deleted_at ON budgets (deleted_at);",
                "CREATE INDEX IF NOT EXISTS idx_budget_active_lookup ON budgets (deleted_at, is_active) WHERE deleted_at IS NULL AND is_active = 1;",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS idx_budget_deleted_at;",
                "DROP INDEX IF EXISTS idx_budget_active_lookup;",
            ]
        ),
    ]