// General POS System JavaScript Functions

// Initialize POS system
document.addEventListener('DOMContentLoaded', function() {
    initializePOS();
    setupEventListeners();
    checkUserSession();
});

function initializePOS() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Setup auto-refresh for certain pages
    setupAutoRefresh();
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
}

function setupEventListeners() {
    // Search functionality
    setupSearchFunctionality();
    
    // Form validations
    setupFormValidations();
    
    // Auto-save functionality
    setupAutoSave();
    
    // Confirm dialogs for destructive actions
    setupConfirmDialogs();
}

function setupSearchFunctionality() {
    // Generic search functionality for tables
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableBody = this.closest('.card').querySelector('tbody');
            
            if (tableBody) {
                const rows = tableBody.querySelectorAll('tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }
        });
    });
}

function setupFormValidations() {
    // Add custom validation to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Show first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    showToast('Please fill in all required fields correctly.', 'error');
                }
            }
            
            form.classList.add('was-validated');
        });
    });

    // Real-time validation for specific fields
    setupRealTimeValidation();
}

function setupRealTimeValidation() {
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !isValidEmail(this.value)) {
                this.setCustomValidity('Please enter a valid email address.');
            } else {
                this.setCustomValidity('');
            }
        });
    });

    // Phone validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !isValidPhone(this.value)) {
                this.setCustomValidity('Please enter a valid phone number.');
            } else {
                this.setCustomValidity('');
            }
        });
    });

    // Price validation
    const priceInputs = document.querySelectorAll('input[name*="price"], input[name*="cost"]');
    priceInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value < 0) {
                this.setCustomValidity('Price cannot be negative.');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

function setupAutoSave() {
    // Auto-save for forms with the auto-save class
    const autoSaveForms = document.querySelectorAll('.auto-save');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                saveFormData(form);
            });
        });
    });
}

function setupConfirmDialogs() {
    // Add confirmation dialogs to dangerous actions
    const dangerousActions = document.querySelectorAll('.confirm-action');
    dangerousActions.forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.dataset.confirmMessage || 'Are you sure you want to perform this action?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N - New Order
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newOrderLink = document.querySelector('a[href*="new_order"]');
            if (newOrderLink) {
                window.location.href = newOrderLink.href;
            }
        }
        
        // Ctrl/Cmd + S - Save (if form is present)
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const submitButton = document.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.click();
            }
        }
        
        // Escape - Close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
    });
}

function setupAutoRefresh() {
    // Auto-refresh for dashboard and orders page
    const currentPath = window.location.pathname;
    
    if (currentPath === '/' || currentPath.includes('orders')) {
        setInterval(function() {
            // Only refresh if user is active (not idle)
            if (isUserActive()) {
                refreshPageData();
            }
        }, 60000); // Refresh every minute
    }
}

// Utility Functions

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

function formatCurrency(amount, currency = 'USD') {
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    });
    return formatter.format(amount);
}

function formatDate(date, format = 'short') {
    const options = format === 'long' ? 
        { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' } :
        { year: 'numeric', month: 'short', day: 'numeric' };
    
    return new Intl.DateTimeFormat('en-US', options).format(new Date(date));
}

function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 
                   type === 'error' ? 'bg-danger' : 
                   type === 'warning' ? 'bg-warning' : 'bg-info';
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });
    
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function showLoader(element) {
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
    }
}

function hideLoader(element) {
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

function saveFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem('formData_' + form.id, JSON.stringify(data));
}

function loadFormData(form) {
    const savedData = localStorage.getItem('formData_' + form.id);
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            for (let [key, value] of Object.entries(data)) {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = value;
                }
            }
        } catch (error) {
            console.error('Error loading form data:', error);
        }
    }
}

function clearFormData(form) {
    localStorage.removeItem('formData_' + form.id);
}

let lastActivity = Date.now();
let userActive = true;

function isUserActive() {
    return userActive && (Date.now() - lastActivity < 300000); // 5 minutes
}

function updateUserActivity() {
    lastActivity = Date.now();
    userActive = true;
}

// Track user activity
document.addEventListener('mousedown', updateUserActivity);
document.addEventListener('mousemove', updateUserActivity);
document.addEventListener('keypress', updateUserActivity);
document.addEventListener('scroll', updateUserActivity);
document.addEventListener('touchstart', updateUserActivity);

// Idle detection
setInterval(function() {
    if (Date.now() - lastActivity > 300000) { // 5 minutes
        userActive = false;
    }
}, 60000); // Check every minute

function checkUserSession() {
    // Check if user session is still valid
    fetch('/auth/check_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 401) {
            // Session expired, redirect to login
            window.location.href = '/auth/login';
        }
    })
    .catch(error => {
        console.error('Error checking session:', error);
    });
}

function refreshPageData() {
    // Refresh specific page data without full page reload
    const currentPath = window.location.pathname;
    
    if (currentPath === '/') {
        // Refresh dashboard data
        refreshDashboardData();
    } else if (currentPath.includes('/orders')) {
        // Refresh orders data
        refreshOrdersData();
    }
}

function refreshDashboardData() {
    // This would typically make AJAX calls to get updated data
    // For now, just show that refresh is happening
    console.log('Refreshing dashboard data...');
}

function refreshOrdersData() {
    // This would typically make AJAX calls to get updated orders
    // For now, just show that refresh is happening
    console.log('Refreshing orders data...');
}

// Export functions for use in other scripts
window.POS = {
    showToast,
    formatCurrency,
    formatDate,
    isValidEmail,
    isValidPhone,
    showLoader,
    hideLoader,
    saveFormData,
    loadFormData,
    clearFormData
};

// Handle online/offline status
window.addEventListener('online', function() {
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showToast('Connection lost. Some features may not work.', 'warning');
});

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
                    <style>
                        body { margin: 20px; }
                        @media print { body { margin: 0; } }
                    </style>
                </head>
                <body>
                    ${element.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// Make print function globally available
window.printElement = printElement;
