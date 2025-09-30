// JSON Textarea Helper Functions
function formatJSON() {
    const textarea = document.getElementById('xfJsonInput');
    try {
        const json = JSON.parse(textarea.value);
        textarea.value = JSON.stringify(json, null, 2);
        showJSONValidation('✓ Formatted successfully', 'success');
    } catch (e) {
        showJSONValidation('✗ Invalid JSON: ' + e.message, 'error');
    }
}

function validateJSON() {
    const textarea = document.getElementById('xfJsonInput');
    const value = textarea.value.trim();
    
    if (!value) {
        showJSONValidation('⚠ No JSON to validate', 'warning');
        return false;
    }
    
    try {
        const json = JSON.parse(value);
        
        // Validate XF schema structure
        if (json.name !== 'xf:form') {
            showJSONValidation('✗ Must be xf:form at root', 'error');
            return false;
        }
        
        if (!json.props || !json.props.children) {
            showJSONValidation('✗ Missing props.children', 'error');
            return false;
        }
        
        showJSONValidation('✓ Valid XF Schema', 'success');
        return true;
    } catch (e) {
        showJSONValidation('✗ Invalid JSON: ' + e.message, 'error');
        return false;
    }
}

function clearJSON() {
    document.getElementById('xfJsonInput').value = '';
    updateJSONCharCount();
    showJSONValidation('', '');
}

function updateJSONCharCount() {
    const textarea = document.getElementById('xfJsonInput');
    document.getElementById('jsonCharCount').textContent = textarea.value.length;
}

function showJSONValidation(message, type) {
    const el = document.getElementById('jsonValidation');
    const colors = {
        success: 'text-green-600',
        error: 'text-red-600',
        warning: 'text-yellow-600'
    };
    el.textContent = message;
    el.className = `text-xs ${colors[type] || ''}`;
}

// Update char count on input
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('xfJsonInput');
    if (textarea) {
        textarea.addEventListener('input', updateJSONCharCount);
    }
});
