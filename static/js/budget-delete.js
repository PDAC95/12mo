/**
 * Alpine.js Component for Budget Deletion
 * Provides confirmation modal, undo functionality, and user experience features
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('budgetDelete', () => ({
        // Modal state
        showModal: false,
        showUndoToast: false,
        isDeleting: false,
        showError: false,

        // Budget data
        budgetId: null,
        budgetName: '',
        expenseCount: 0,
        splitCount: 0,
        memberCount: 0,
        deletedBudgetName: '',
        undoData: null,

        // Confirmation
        confirmationText: '',

        // User info for audit
        userIP: '',

        // Auto-hide timer for toast
        undoTimer: null,

        init() {
            // Get user IP for audit trail
            this.getUserIP();

            // Listen for escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.showModal) {
                    this.closeModal();
                }
            });

            // Auto-hide undo toast after 30 seconds
            this.$watch('showUndoToast', (value) => {
                if (value) {
                    this.undoTimer = setTimeout(() => {
                        this.hideUndoToast();
                    }, 30000);
                } else if (this.undoTimer) {
                    clearTimeout(this.undoTimer);
                    this.undoTimer = null;
                }
            });
        },

        /**
         * Get user IP address for audit trail
         */
        async getUserIP() {
            try {
                const response = await fetch('https://api.ipify.org?format=json');
                const data = await response.json();
                this.userIP = data.ip;
            } catch (error) {
                this.userIP = 'Unknown';
            }
        },

        /**
         * Open delete confirmation modal
         * @param {number} budgetId - Budget ID to delete
         * @param {string} budgetName - Budget name for display
         * @param {number} expenseCount - Number of associated expenses
         * @param {number} splitCount - Number of splits
         * @param {number} memberCount - Number of space members
         */
        openDeleteModal(budgetId, budgetName, expenseCount, splitCount, memberCount) {
            this.budgetId = budgetId;
            this.budgetName = budgetName;
            this.expenseCount = expenseCount || 0;
            this.splitCount = splitCount || 0;
            this.memberCount = memberCount || 0;
            this.confirmationText = '';
            this.showError = false;
            this.showModal = true;

            // Focus on confirmation input after modal opens
            this.$nextTick(() => {
                const input = document.getElementById('confirmationInput');
                if (input) {
                    input.focus();
                }
            });
        },

        /**
         * Close the delete modal
         */
        closeModal() {
            this.showModal = false;
            this.resetModalState();
        },

        /**
         * Reset modal state
         */
        resetModalState() {
            this.budgetId = null;
            this.budgetName = '';
            this.expenseCount = 0;
            this.splitCount = 0;
            this.memberCount = 0;
            this.confirmationText = '';
            this.showError = false;
            this.isDeleting = false;
        },

        /**
         * Confirm budget deletion
         */
        async confirmDelete() {
            // Validate confirmation text
            if (this.confirmationText !== 'ELIMINAR') {
                this.showError = true;
                this.shakeInput();
                return;
            }

            this.isDeleting = true;
            this.showError = false;

            try {
                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ||
                                document.querySelector('meta[name="csrf-token"]');
                if (!csrfToken) {
                    throw new Error('CSRF token not found');
                }

                const csrfValue = csrfToken.value || csrfToken.getAttribute('content');

                // Prepare request data
                const requestData = {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfValue,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        budget_id: this.budgetId,
                        confirmation: this.confirmationText,
                        audit_data: {
                            ip: this.userIP,
                            timestamp: new Date().toISOString(),
                            user_agent: navigator.userAgent
                        }
                    })
                };

                // Make delete request
                const response = await fetch(`/budgets/api/delete/${this.budgetId}/`, requestData);

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();

                if (result.success) {
                    // Store undo data
                    this.undoData = result.undo_data;
                    this.deletedBudgetName = this.budgetName;

                    // Close modal and show success
                    this.closeModal();
                    this.showUndoToast = true;

                    // Remove budget row from DOM with animation
                    this.removeBudgetFromDOM();

                    // Update page totals if provided
                    if (result.updated_totals) {
                        this.updatePageTotals(result.updated_totals);
                    }

                } else {
                    throw new Error(result.error || 'Error desconocido al eliminar el presupuesto');
                }

            } catch (error) {
                console.error('Delete error:', error);
                this.handleDeleteError(error.message);
            } finally {
                this.isDeleting = false;
            }
        },

        /**
         * Handle delete error
         * @param {string} errorMessage - Error message to display
         */
        handleDeleteError(errorMessage) {
            // Show error in modal or as toast
            if (this.showModal) {
                alert(`Error: ${errorMessage}`);
            } else {
                this.showErrorToast(errorMessage);
            }
        },

        /**
         * Show error toast notification
         * @param {string} message - Error message
         */
        showErrorToast(message) {
            // Create temporary error toast
            const toast = document.createElement('div');
            toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg z-50';
            toast.textContent = `Error: ${message}`;
            document.body.appendChild(toast);

            setTimeout(() => {
                toast.remove();
            }, 5000);
        },

        /**
         * Remove budget row from DOM with animation
         */
        removeBudgetFromDOM() {
            const budgetRow = document.querySelector(`tr[data-budget-id="${this.budgetId}"]`);
            if (budgetRow) {
                // Add fade-out animation
                budgetRow.style.transition = 'all 0.3s ease-out';
                budgetRow.style.opacity = '0';
                budgetRow.style.transform = 'translateX(-20px)';

                setTimeout(() => {
                    budgetRow.remove();
                    this.checkEmptyState();
                }, 300);
            } else {
                // Fallback: reload page if DOM manipulation fails
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        },

        /**
         * Check if budget list is empty and show empty state
         */
        checkEmptyState() {
            const budgetRows = document.querySelectorAll('tbody tr');
            if (budgetRows.length === 0) {
                // Reload page to show empty state
                window.location.reload();
            }
        },

        /**
         * Update page totals after deletion
         * @param {Object} totals - Updated totals from server
         */
        updatePageTotals(totals) {
            // Update total budgeted
            const totalBudgetedElement = document.querySelector('[data-total-budgeted]');
            if (totalBudgetedElement && totals.total_budgeted !== undefined) {
                totalBudgetedElement.textContent = `$${parseFloat(totals.total_budgeted).toFixed(2)}`;
            }

            // Update remaining
            const remainingElement = document.querySelector('[data-remaining]');
            if (remainingElement && totals.remaining !== undefined) {
                remainingElement.textContent = `$${parseFloat(totals.remaining).toFixed(2)}`;
            }

            // Update progress percentage
            const progressElement = document.querySelector('[data-spent-percentage]');
            if (progressElement && totals.spent_percentage !== undefined) {
                progressElement.textContent = `${totals.spent_percentage}% spent`;

                // Update progress bar
                const progressBar = document.querySelector('[data-progress-bar]');
                if (progressBar) {
                    const percentage = Math.min(totals.spent_percentage, 100);
                    progressBar.style.width = `${percentage}%`;

                    // Update color based on percentage
                    progressBar.className = progressBar.className.replace(/bg-(red|yellow|green)-\d+/, '');
                    if (percentage > 90) {
                        progressBar.classList.add('bg-red-500');
                    } else if (percentage > 75) {
                        progressBar.classList.add('bg-yellow-500');
                    } else {
                        progressBar.classList.add('bg-green-500');
                    }
                }
            }
        },

        /**
         * Undo budget deletion
         */
        async undoDelete() {
            if (!this.undoData) {
                console.error('No undo data available');
                return;
            }

            try {
                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ||
                                document.querySelector('meta[name="csrf-token"]');
                if (!csrfToken) {
                    throw new Error('CSRF token not found');
                }

                const csrfValue = csrfToken.value || csrfToken.getAttribute('content');

                const response = await fetch('/budgets/api/undo-delete/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfValue,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        undo_data: this.undoData
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();

                if (result.success) {
                    this.hideUndoToast();
                    // Reload page to show restored budget
                    window.location.reload();
                } else {
                    throw new Error(result.error || 'Error al restaurar el presupuesto');
                }

            } catch (error) {
                console.error('Undo error:', error);
                this.showErrorToast(error.message);
            }
        },

        /**
         * Hide undo toast
         */
        hideUndoToast() {
            this.showUndoToast = false;
            this.undoData = null;
            this.deletedBudgetName = '';
        },

        /**
         * Shake input animation for invalid confirmation
         */
        shakeInput() {
            const input = document.getElementById('confirmationInput');
            if (input) {
                input.classList.add('animate-shake');
                setTimeout(() => {
                    input.classList.remove('animate-shake');
                }, 500);
            }
        }
    }));
});

// Global function to open delete modal (called from template)
window.openDeleteModal = function(budgetId, budgetName, expenseCount, splitCount, memberCount) {
    // Find the Alpine component and call its method
    const component = document.querySelector('[x-data*="budgetDelete"]');
    if (component && component._x_dataStack) {
        const data = component._x_dataStack[0];
        data.openDeleteModal(budgetId, budgetName, expenseCount, splitCount, memberCount);
    }
};

// Add required CSS classes for animations
document.addEventListener('DOMContentLoaded', function() {
    // Add shake animation CSS if not present
    if (!document.querySelector('#budget-delete-styles')) {
        const style = document.createElement('style');
        style.id = 'budget-delete-styles';
        style.textContent = `
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
                20%, 40%, 60%, 80% { transform: translateX(10px); }
            }
            .animate-shake {
                animation: shake 0.5s ease-in-out;
            }
            [x-cloak] {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
    }
});