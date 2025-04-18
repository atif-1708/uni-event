// University Event System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize date pickers in filter forms
    initDatePickers();
    
    // Handle filter form submission (for AJAX filtering if implemented)
    initFilterForms();
    
    // Initialize event registration confirmation modal
    initRegistrationModal();
});

/**
 * Initialize date pickers for filter forms
 */
function initDatePickers() {
    // Check if flatpickr is loaded
    if (typeof flatpickr !== 'undefined') {
        // Date range pickers for event filters
        const dateFromPicker = document.getElementById('date-from');
        const dateToPicker = document.getElementById('date-to');
        
        if (dateFromPicker) {
            flatpickr(dateFromPicker, {
                altInput: true,
                altFormat: "F j, Y",
                dateFormat: "Y-m-d",
            });
        }
        
        if (dateToPicker) {
            flatpickr(dateToPicker, {
                altInput: true,
                altFormat: "F j, Y",
                dateFormat: "Y-m-d",
            });
        }
        
        // For event creation/editing
        const eventDatePicker = document.getElementById('date');
        if (eventDatePicker) {
            flatpickr(eventDatePicker, {
                enableTime: true,
                dateFormat: "Y-m-d H:i",
                time_24hr: true
            });
        }
    }
}

/**
 * Initialize filter forms 
 */
function initFilterForms() {
    const filterForm = document.getElementById('filter-form');
    
    if (filterForm) {
        // For now, we're using standard form submission
        // This function can be expanded for AJAX filtering later
        
        // Add reset functionality
        const resetButton = filterForm.querySelector('a[href*="reset"]');
        if (resetButton) {
            resetButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Clear all form inputs
                const inputs = filterForm.querySelectorAll('input');
                inputs.forEach(input => {
                    input.value = '';
                });
                
                // Submit the form
                filterForm.submit();
            });
        }
    }
}

/**
 * Initialize registration confirmation modal
 */
function initRegistrationModal() {
    const registerButtons = document.querySelectorAll('.register-event-btn');
    
    registerButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // This is a placeholder for a potential modal confirmation
            // For now, we're using the default form submission
            
            // If you want to add a confirmation dialog:
            /*
            e.preventDefault();
            const form = this.closest('form');
            const eventTitle = this.getAttribute('data-event-title');
            
            if (confirm(`Are you sure you want to register for "${eventTitle}"?`)) {
                form.submit();
            }
            */
        });
    });
}

/**
 * Toggle attendance status in admin registration view
 */
function toggleAttendance(registrationId, attended) {
    // This is a placeholder for potential AJAX attendance toggling
    // Currently using form submission in the HTML
    console.log('Toggle attendance for registration ID:', registrationId, 'to', attended);
}

/**
 * Filter events via AJAX (for future implementation)
 */
function filterEvents(dateFrom, dateTo) {
    // This is a placeholder for potential AJAX filtering
    // Currently using standard form submission
    
    fetch(`/events/api?date_from=${dateFrom}&date_to=${dateTo}`)
        .then(response => response.json())
        .then(data => {
            console.log('Filtered events:', data);
            // Update the UI with filtered events
            // Implementation would go here
        })
        .catch(error => {
            console.error('Error fetching filtered events:', error);
        });
}

/**
 * Export registrations to CSV (admin function)
 */
function exportRegistrations(eventId) {
    // Direct the browser to the export URL
    window.location.href = `/admin/events/${eventId}/registrations/export`;
}

/**
 * Show/hide admin code field based on role selection in registration form
 */
function toggleAdminCodeField() {
    const roleSelect = document.getElementById('role');
    const adminCodeField = document.querySelector('.admin-code-field');
    
    if (roleSelect && adminCodeField) {
        if (roleSelect.value === 'admin') {
            adminCodeField.style.display = 'block';
        } else {
            adminCodeField.style.display = 'none';
        }
    }
}