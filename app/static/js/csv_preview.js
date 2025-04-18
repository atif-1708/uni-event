document.addEventListener('DOMContentLoaded', function() {
    const csvFile = document.getElementById('csvFile');
    const filePreview = document.getElementById('filePreview');
    const previewHeader = document.getElementById('previewHeader');
    const previewBody = document.getElementById('previewBody');
    const previewError = document.getElementById('previewError');
    const uploadBtn = document.getElementById('uploadBtn');
    
    const requiredFields = ['title', 'description', 'date', 'end_date', 'registration_deadline', 'location', 'max_participants'];
    
    // Handle file selection
    csvFile.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (!file) {
            filePreview.style.display = 'none';
            return;
        }
        
        // Check file extension
        if (!file.name.endsWith('.csv')) {
            previewError.textContent = 'Please upload a CSV file.';
            filePreview.style.display = 'block';
            previewHeader.innerHTML = '';
            previewBody.innerHTML = '';
            uploadBtn.disabled = true;
            return;
        }
        
        // Parse CSV file
        parseCSV(file);
    });
    
    // Parse and preview CSV
    function parseCSV(file) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const contents = e.target.result;
            
            // Basic parsing
            const lines = contents.split(/\r\n|\n/);
            
            // Check if file is empty
            if (lines.length === 0 || (lines.length === 1 && lines[0].trim() === '')) {
                previewError.textContent = 'The CSV file is empty.';
                filePreview.style.display = 'block';
                previewHeader.innerHTML = '';
                previewBody.innerHTML = '';
                uploadBtn.disabled = true;
                return;
            }
            
            // Parse header
            const headers = lines[0].split(',').map(header => header.trim().toLowerCase());
            
            // Validate required headers
            const missingHeaders = requiredFields.filter(field => !headers.includes(field));
            
            if (missingHeaders.length > 0) {
                previewError.textContent = `Missing required headers: ${missingHeaders.join(', ')}`;
                uploadBtn.disabled = true;
            } else {
                previewError.textContent = '';
                uploadBtn.disabled = false;
            }
            
            // Generate header row
            let headerRow = '<tr>';
            headers.forEach(header => {
                const isRequired = requiredFields.includes(header);
                headerRow += `<th>${header}${isRequired ? ' *' : ''}</th>`;
            });
            headerRow += '</tr>';
            previewHeader.innerHTML = headerRow;
            
            // Generate preview rows (up to 5)
            let bodyRows = '';
            const maxRows = Math.min(5, lines.length - 1);
            
            for (let i = 1; i <= maxRows; i++) {
                if (lines[i].trim() === '') continue;
                
                const cells = parseCSVLine(lines[i]);
                
                let row = '<tr>';
                for (let j = 0; j < headers.length; j++) {
                    const cellValue = j < cells.length ? cells[j] : '';
                    row += `<td>${cellValue}</td>`;
                }
                row += '</tr>';
                bodyRows += row;
            }
            
            previewBody.innerHTML = bodyRows;
            
            // If more rows exist, add indicator
            if (lines.length - 1 > maxRows) {
                const remainingRows = lines.length - 1 - maxRows;
                const additionalRow = `<tr><td colspan="${headers.length}" class="text-center text-muted">+ ${remainingRows} more rows</td></tr>`;
                previewBody.innerHTML += additionalRow;
            }
            
            filePreview.style.display = 'block';
        };
        
        reader.readAsText(file);
    }
    
    // Helper function to handle quoted values in CSV
    function parseCSVLine(line) {
        const result = [];
        let currentValue = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"' && (i === 0 || line[i-1] !== '\\')) {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(currentValue.trim());
                currentValue = '';
            } else {
                currentValue += char;
            }
        }
        
        result.push(currentValue.trim());
        return result;
    }
    
    // Form submission
    const bulkUploadForm = document.getElementById('bulkUploadForm');
    bulkUploadForm.addEventListener('submit', function(e) {
        if (!csvFile.files[0]) {
            e.preventDefault();
            alert('Please select a CSV file.');
            return false;
        }
        
        // Show loading state
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
    });
});