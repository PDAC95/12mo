from rest_framework import serializers


class BudgetDeleteRequestSerializer(serializers.Serializer):
    """Serializer for budget deletion request validation"""

    confirmation_text = serializers.CharField(
        max_length=20,
        required=True,
        help_text="Must be 'ELIMINAR' to confirm deletion"
    )
    notify_members = serializers.BooleanField(
        default=True,
        help_text="Whether to notify space members about deletion"
    )
    soft_delete = serializers.BooleanField(
        default=False,
        help_text="Whether to perform soft delete (can be restored)"
    )

    def validate_confirmation_text(self, value):
        """Validate confirmation text is correct"""
        if value != "ELIMINAR":
            raise serializers.ValidationError(
                "Confirmation text must be 'ELIMINAR' to proceed with deletion"
            )
        return value


class BudgetDeleteResponseSerializer(serializers.Serializer):
    """Serializer for budget deletion response"""

    success = serializers.BooleanField(
        help_text="Whether deletion was successful"
    )
    message = serializers.CharField(
        help_text="Human-readable status message"
    )
    deleted_splits = serializers.IntegerField(
        help_text="Number of budget splits deleted"
    )
    deleted_expenses = serializers.IntegerField(
        help_text="Number of actual expenses deleted"
    )
    budget_id = serializers.IntegerField(
        help_text="ID of the deleted budget"
    )
    space_id = serializers.IntegerField(
        help_text="ID of the space the budget belonged to"
    )
    category_name = serializers.CharField(
        help_text="Name of the budget category"
    )
    month_period = serializers.CharField(
        help_text="Month period of the deleted budget"
    )
    deleted_at = serializers.DateTimeField(
        help_text="Timestamp when deletion occurred"
    )
    audit_log_id = serializers.IntegerField(
        required=False,
        help_text="ID of the audit log entry"
    )


class BudgetDeletionSummarySerializer(serializers.Serializer):
    """Serializer for pre-deletion summary information"""

    budget_id = serializers.IntegerField()
    budget_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_name = serializers.CharField()
    month_period = serializers.CharField()
    space_name = serializers.CharField()

    total_splits = serializers.IntegerField(
        help_text="Number of budget splits that will be deleted"
    )
    total_expenses = serializers.IntegerField(
        help_text="Number of actual expenses that will be deleted"
    )
    total_expense_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount of expenses that will be deleted"
    )

    affected_users = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of usernames who will be affected by deletion"
    )

    can_delete = serializers.BooleanField(
        help_text="Whether user has permission to delete this budget"
    )
    warning_messages = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of warning messages for this deletion"
    )