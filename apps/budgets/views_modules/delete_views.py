import logging
import json
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from ..models import Budget
from ..serializers.delete_serializers import (
    BudgetDeleteRequestSerializer,
    BudgetDeleteResponseSerializer,
    BudgetDeletionSummarySerializer
)
from ..utils.deletion_utils import BudgetDeletionUtils
from spaces.models import SpaceMember

logger = logging.getLogger('budget_deletion')


class BudgetDeleteView(APIView):
    """
    API View for budget deletion with comprehensive security validations

    DELETE /api/budgets/{id}/
    """
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='user', rate='10/h', method='DELETE'))
    def delete(self, request, budget_id):
        """
        Handle budget deletion with security validations and audit logging

        Args:
            request: HTTP request object
            budget_id: ID of budget to delete

        Returns:
            JsonResponse: Deletion result with comprehensive details
        """
        try:
            # Get budget instance
            budget = get_object_or_404(Budget, id=budget_id, is_active=True)

            # Validate request data
            serializer = BudgetDeleteRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'message': 'Invalid request data',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            # Validate user permissions
            has_permission, permission_error = BudgetDeletionUtils.validate_user_permission(
                budget, request.user
            )
            if not has_permission:
                logger.warning(
                    f"Unauthorized budget deletion attempt - "
                    f"User: {request.user.username}, "
                    f"Budget: {budget.id}, "
                    f"Error: {permission_error}"
                )
                return Response(
                    {
                        'success': False,
                        'message': permission_error
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate deletion safety
            is_safe, safety_errors = BudgetDeletionUtils.validate_deletion_safety(budget)
            if not is_safe and not validated_data.get('soft_delete', False):
                return Response(
                    {
                        'success': False,
                        'message': 'Deletion not recommended',
                        'warnings': safety_errors,
                        'suggestion': 'Consider using soft_delete=true instead'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Perform deletion with atomic transaction
            with transaction.atomic():
                deletion_result = BudgetDeletionUtils.perform_deletion(
                    budget=budget,
                    user=request.user,
                    soft_delete=validated_data.get('soft_delete', False),
                    notify_members=validated_data.get('notify_members', True)
                )

                if not deletion_result['success']:
                    return Response(
                        deletion_result,
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                # Serialize response
                response_serializer = BudgetDeleteResponseSerializer(data=deletion_result)
                if response_serializer.is_valid():
                    logger.info(
                        f"Budget deletion successful - "
                        f"User: {request.user.username}, "
                        f"Budget: {budget_id}, "
                        f"Soft: {validated_data.get('soft_delete', False)}"
                    )
                    return Response(
                        response_serializer.validated_data,
                        status=status.HTTP_200_OK
                    )
                else:
                    # Fallback response if serialization fails
                    return Response(
                        deletion_result,
                        status=status.HTTP_200_OK
                    )

        except Budget.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': f'Budget with ID {budget_id} not found or already deleted'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Unexpected error in budget deletion: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': 'Internal server error during deletion'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@login_required
@ratelimit(key='user', rate='10/h', method='DELETE')
@require_http_methods(["DELETE"])
@csrf_exempt
@transaction.atomic
def budget_delete_api(request, budget_id):
    """
    Function-based view for budget deletion (alternative to class-based view)

    Args:
        request: HTTP request object
        budget_id: ID of budget to delete

    Returns:
        JsonResponse: Deletion result
    """
    try:
        # Parse request body
        try:
            request_data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Invalid JSON in request body'
                },
                status=400
            )

        # Get budget instance
        try:
            budget = Budget.objects.get(id=budget_id, is_active=True)
        except Budget.DoesNotExist:
            return JsonResponse(
                {
                    'success': False,
                    'message': f'Budget with ID {budget_id} not found or already deleted'
                },
                status=404
            )

        # Validate request data
        serializer = BudgetDeleteRequestSerializer(data=request_data)
        if not serializer.is_valid():
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Invalid request data',
                    'errors': serializer.errors
                },
                status=400
            )

        validated_data = serializer.validated_data

        # Validate user permissions
        has_permission, permission_error = BudgetDeletionUtils.validate_user_permission(
            budget, request.user
        )
        if not has_permission:
            logger.warning(
                f"Unauthorized budget deletion attempt - "
                f"User: {request.user.username}, "
                f"Budget: {budget.id}, "
                f"Error: {permission_error}"
            )
            return JsonResponse(
                {
                    'success': False,
                    'message': permission_error
                },
                status=403
            )

        # Validate deletion safety
        is_safe, safety_errors = BudgetDeletionUtils.validate_deletion_safety(budget)
        if not is_safe and not validated_data.get('soft_delete', False):
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Deletion not recommended',
                    'warnings': safety_errors,
                    'suggestion': 'Consider using soft_delete=true instead'
                },
                status=400
            )

        # Perform deletion
        deletion_result = BudgetDeletionUtils.perform_deletion(
            budget=budget,
            user=request.user,
            soft_delete=validated_data.get('soft_delete', False),
            notify_members=validated_data.get('notify_members', True)
        )

        if deletion_result['success']:
            logger.info(
                f"Budget deletion successful - "
                f"User: {request.user.username}, "
                f"Budget: {budget_id}, "
                f"Soft: {validated_data.get('soft_delete', False)}"
            )
            return JsonResponse(deletion_result, status=200)
        else:
            return JsonResponse(deletion_result, status=500)

    except Exception as e:
        logger.error(f"Unexpected error in budget deletion: {str(e)}")
        return JsonResponse(
            {
                'success': False,
                'message': 'Internal server error during deletion'
            },
            status=500
        )


@login_required
@ratelimit(key='user', rate='30/h', method='GET')
@require_http_methods(["GET"])
def budget_deletion_summary(request, budget_id):
    """
    Get summary of what will be affected by budget deletion

    Args:
        request: HTTP request object
        budget_id: ID of budget to analyze

    Returns:
        JsonResponse: Summary of deletion impact
    """
    try:
        # Get budget instance
        try:
            budget = Budget.objects.get(id=budget_id, is_active=True)
        except Budget.DoesNotExist:
            return JsonResponse(
                {
                    'success': False,
                    'message': f'Budget with ID {budget_id} not found or already deleted'
                },
                status=404
            )

        # Validate user permissions
        has_permission, permission_error = BudgetDeletionUtils.validate_user_permission(
            budget, request.user
        )

        # Get deletion summary
        summary = BudgetDeletionUtils.get_deletion_summary(budget)
        summary['can_delete'] = has_permission

        if not has_permission:
            summary['permission_error'] = permission_error

        # Validate deletion safety
        is_safe, safety_errors = BudgetDeletionUtils.validate_deletion_safety(budget)
        summary['is_safe_to_delete'] = is_safe
        summary['safety_warnings'] = safety_errors

        # Get affected users detail
        summary['affected_users_detail'] = BudgetDeletionUtils.get_affected_users_detail(budget)

        # Serialize response
        try:
            serializer = BudgetDeletionSummarySerializer(data=summary)
            if serializer.is_valid():
                return JsonResponse(
                    {
                        'success': True,
                        'summary': serializer.validated_data
                    },
                    status=200
                )
            else:
                # Fallback to raw summary if serialization fails
                return JsonResponse(
                    {
                        'success': True,
                        'summary': summary,
                        'serialization_errors': serializer.errors
                    },
                    status=200
                )
        except Exception as serialization_error:
            logger.warning(f"Serialization error in deletion summary: {str(serialization_error)}")
            return JsonResponse(
                {
                    'success': True,
                    'summary': summary
                },
                status=200
            )

    except Exception as e:
        logger.error(f"Error getting budget deletion summary: {str(e)}")
        return JsonResponse(
            {
                'success': False,
                'message': 'Failed to generate deletion summary'
            },
            status=500
        )