// Main JavaScript for RBAC Blog System

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Add confirmation to delete buttons
    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Character counter for textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        if (!textarea.closest('.comment-item')) {
            const maxLength = textarea.getAttribute('maxlength');
            if (maxLength) {
                const counter = document.createElement('div');
                counter.className = 'text-muted small mt-1';
                counter.textContent = `0 / ${maxLength} characters`;
                textarea.parentNode.appendChild(counter);
                
                textarea.addEventListener('input', function() {
                    const length = this.value.length;
                    counter.textContent = `${length} / ${maxLength} characters`;
                    if (length > maxLength * 0.9) {
                        counter.style.color = 'orange';
                    } else {
                        counter.style.color = '#6c757d';
                    }
                });
            }
        }
    });
    
    // Smooth scroll to comments
    const commentLinks = document.querySelectorAll('a[href="#comments"]');
    commentLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector('#comments-section').scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing...';
            }
        });
    });
});

// Function to format timestamps
function timeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    let interval = seconds / 31536000;
    
    if (interval > 1) return Math.floor(interval) + ' years ago';
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + ' months ago';
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + ' days ago';
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + ' hours ago';
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + ' minutes ago';
    return Math.floor(seconds) + ' seconds ago';
}

// Function to copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

// Function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    const toastContainerElem = document.querySelector('.toast-container');
    toastContainerElem.insertAdjacentHTML('beforeend', toastHTML);
    const toastElem = toastContainerElem.lastElementChild;
    const toast = new bootstrap.Toast(toastElem, { autohide: true, delay: 3000 });
    toast.show();
    
    toastElem.addEventListener('hidden.bs.toast', () => {
        toastElem.remove();
    });
}

// Function to preview post content
function previewContent() {
    const content = document.getElementById('content')?.value;
    const preview = document.getElementById('preview');
    if (preview && content) {
        preview.innerHTML = content.replace(/\n/g, '<br>');
    }
}

// Export functions for global use
window.copyToClipboard = copyToClipboard;
window.showToast = showToast;
window.timeAgo = timeAgo;
window.previewContent = previewContent;