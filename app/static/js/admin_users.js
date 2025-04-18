document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const searchInput = document.getElementById('search');
    const departmentSelect = document.getElementById('department');
    const filterForm = document.querySelector('form');
    
    // Add debounce function to avoid excessive requests
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }
    
    // Function to submit the form
    function submitForm() {
        filterForm.submit();
    }
    
    // Add event listeners with debounce
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            // Only submit if at least 3 characters or empty
            if (searchInput.value.length >= 3 || searchInput.value.length === 0) {
                submitForm();
            }
        }, 500));
    }
    
    if (departmentSelect) {
        departmentSelect.addEventListener('change', function() {
            submitForm();
        });
    }
    
    // Table row highlighting and click handling
    const userRows = document.querySelectorAll('tbody tr');
    userRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if they clicked on a button or link
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || 
                e.target.closest('a') || e.target.closest('button')) {
                return;
            }
            
            // Get the view details link from this row and navigate to it
            const detailsLink = this.querySelector('a.btn-outline-primary');
            if (detailsLink) {
                window.location.href = detailsLink.href;
            }
        });
        
        // Add hover cursor to indicate clickable
        row.style.cursor = 'pointer';
    });
});