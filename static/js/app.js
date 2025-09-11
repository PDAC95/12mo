// Wallai Main Application JavaScript

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Wallai App initialized');
    
    // Initialize PWA features
    initializePWA();
    
    // Initialize UI components
    initializeUI();
});

// PWA Initialization
function initializePWA() {
    // Check if app is running in standalone mode
    if (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) {
        document.body.classList.add('pwa-mode');
        console.log('Running in PWA mode');
    }
    
    // Handle online/offline status
    window.addEventListener('online', handleOnlineStatus);
    window.addEventListener('offline', handleOfflineStatus);
    
    // Initial status check
    if (navigator.onLine) {
        handleOnlineStatus();
    } else {
        handleOfflineStatus();
    }
}

// Online status handler
function handleOnlineStatus() {
    console.log('App is online');
    document.body.classList.remove('offline-mode');
    
    // Hide offline banner if exists
    const offlineBanner = document.getElementById('offline-banner');
    if (offlineBanner) {
        offlineBanner.style.display = 'none';
    }
}

// Offline status handler
function handleOfflineStatus() {
    console.log('App is offline');
    document.body.classList.add('offline-mode');
    
    // Show offline banner
    showOfflineBanner();
}

// Show offline notification banner
function showOfflineBanner() {
    let banner = document.getElementById('offline-banner');
    
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.className = 'fixed top-0 left-0 right-0 bg-warning-500 text-white text-center py-2 px-4 text-sm z-50';
        banner.innerHTML = '⚠️ No connection - Working in offline mode';
        document.body.insertBefore(banner, document.body.firstChild);
    }
    
    banner.style.display = 'block';
}

// UI Components initialization
function initializeUI() {
    // Initialize mobile menu toggles
    initializeMobileMenu();
    
    // Initialize form enhancements
    initializeForms();
    
    // Initialize tooltips and popovers
    initializeTooltips();
}

// Mobile menu functionality
function initializeMobileMenu() {
    const mobileMenuButton = document.querySelector('[data-mobile-menu-toggle]');
    const mobileMenu = document.querySelector('[data-mobile-menu]');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            const isOpen = mobileMenu.classList.contains('show');
            
            if (isOpen) {
                mobileMenu.classList.remove('show');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
            } else {
                mobileMenu.classList.add('show');
                mobileMenuButton.setAttribute('aria-expanded', 'true');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!mobileMenu.contains(event.target) && !mobileMenuButton.contains(event.target)) {
                mobileMenu.classList.remove('show');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
            }
        });
    }
}

// Form enhancements
function initializeForms() {
    // Add loading states to form submissions
    const forms = document.querySelectorAll('form[data-loading]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.classList.add('loading');
                
                // Re-enable after a timeout as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.classList.remove('loading');
                }, 5000);
            }
        });
    });
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', autoResizeTextarea);
        autoResizeTextarea.call(textarea); // Initial resize
    });
}

// Auto resize textarea function
function autoResizeTextarea() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
}

// Tooltip initialization
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        let tooltip = null;
        
        element.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            
            tooltip = document.createElement('div');
            tooltip.className = 'absolute bg-gray-800 text-white text-xs px-2 py-1 rounded shadow-lg z-50 pointer-events-none';
            tooltip.textContent = text;
            
            document.body.appendChild(tooltip);
            
            // Position tooltip
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        });
        
        element.addEventListener('mouseleave', function() {
            if (tooltip) {
                document.body.removeChild(tooltip);
                tooltip = null;
            }
        });
    });
}

// Utility functions
const Wallai = {
    // Show notification
    showNotification: function(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-sm transform transition-all duration-300 translate-x-full opacity-0`;
        
        // Set type-specific styles
        const typeClasses = {
            'success': 'bg-success-50 border border-success-200 text-success-800',
            'error': 'bg-danger-50 border border-danger-200 text-danger-800',
            'warning': 'bg-warning-50 border border-warning-200 text-warning-800',
            'info': 'bg-primary-50 border border-primary-200 text-primary-800'
        };
        
        notification.className += ' ' + (typeClasses[type] || typeClasses.info);
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="flex-1">${message}</span>
                <button class="ml-2 text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
        }, 10);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.add('translate-x-full', 'opacity-0');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.parentElement.removeChild(notification);
                    }
                }, 300);
            }, duration);
        }
    },
    
    // Confirm dialog
    confirm: function(message, callback) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4">
                <p class="text-gray-800 mb-4">${message}</p>
                <div class="flex justify-end space-x-3">
                    <button class="btn-secondary" onclick="this.closest('.fixed').remove()">Cancel</button>
                    <button class="btn-primary" id="confirm-yes">Confirm</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('#confirm-yes').addEventListener('click', function() {
            modal.remove();
            if (callback) callback(true);
        });
        
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.remove();
                if (callback) callback(false);
            }
        });
    },
    
    // Format currency
    formatCurrency: function(amount, currency = 'USD', locale = 'en-US') {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    // API helper
    api: {
        async request(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            };
            
            // Add CSRF token if available
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (csrfToken) {
                defaultOptions.headers['X-CSRFToken'] = csrfToken;
            }
            
            const mergedOptions = {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers
                }
            };
            
            try {
                const response = await fetch(url, mergedOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }
                
                return await response.text();
            } catch (error) {
                console.error('API request failed:', error);
                
                if (!navigator.onLine) {
                    Wallai.showNotification('No internet connection', 'error');
                } else {
                    Wallai.showNotification('Request error', 'error');
                }
                
                throw error;
            }
        }
    }
};

// Make Wallai globally available
window.Wallai = Wallai;