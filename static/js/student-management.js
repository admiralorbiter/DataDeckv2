/**
 * Student Management JavaScript
 * Handles student operations like PIN reset, deletion, and bulk actions
 */

// Global variables
let currentStudentId = null;
let currentStudentName = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeStudentManagement();
});

function initializeStudentManagement() {
    // Initialize select all checkbox
    const selectAllCheckbox = document.getElementById('selectAllStudents');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', handleSelectAll);
    }

    // Initialize individual checkboxes
    const studentCheckboxes = document.querySelectorAll('.student-checkbox');
    studentCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });

    // Initialize delete selected button
    const deleteSelectedBtn = document.getElementById('deleteSelectedStudents');
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', handleDeleteSelected);
    }

    // Initialize modal event listeners
    initializeModals();
}

function handleSelectAll(event) {
    const isChecked = event.target.checked;
    const studentCheckboxes = document.querySelectorAll('.student-checkbox');

    studentCheckboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
    });

    updateSelectedCount();
}

function updateSelectedCount() {
    const selectedCheckboxes = document.querySelectorAll('.student-checkbox:checked');
    const count = selectedCheckboxes.length;
    const totalCheckboxes = document.querySelectorAll('.student-checkbox');

    // Update count display
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = count;
    }

    // Update delete button state
    const deleteBtn = document.getElementById('deleteSelectedStudents');
    if (deleteBtn) {
        deleteBtn.disabled = count === 0;
    }

    // Update select all checkbox state
    const selectAllCheckbox = document.getElementById('selectAllStudents');
    if (selectAllCheckbox) {
        if (count === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (count === totalCheckboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
        }
    }
}

function confirmDeleteStudent(studentId, studentName) {
    currentStudentId = studentId;
    currentStudentName = studentName;

    // Update modal content
    document.getElementById('deleteStudentName').textContent = studentName;

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('deleteStudentModal'));
    modal.show();
}

function handleDeleteSelected() {
    const selectedCheckboxes = document.querySelectorAll('.student-checkbox:checked');
    const studentNames = Array.from(selectedCheckboxes).map(cb =>
        cb.getAttribute('data-student-name')
    );

    if (studentNames.length === 0) return;

    const message = studentNames.length === 1
        ? `Are you sure you want to delete ${studentNames[0]}?`
        : `Are you sure you want to delete ${studentNames.length} students?`;

    if (confirm(message)) {
        const studentIds = Array.from(selectedCheckboxes).map(cb => cb.value);
        deleteMultipleStudents(studentIds);
    }
}

function resetStudentPin(studentId, studentName) {
    if (!confirm(`Reset PIN for ${studentName}?`)) return;

    // Show loading state
    const button = event.target.closest('button');
    const originalHtml = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    button.disabled = true;

    fetch(`/students/${studentId}/reset-pin`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show new PIN in modal
            document.getElementById('pinResetStudentName').textContent = studentName;
            document.getElementById('newPinDisplay').textContent = data.new_pin;

            const modal = new bootstrap.Modal(document.getElementById('pinResetModal'));
            modal.show();

            showToast('PIN reset successful', 'success');
        } else {
            showToast(data.message || 'Failed to reset PIN', 'danger');
        }
    })
    .catch(error => {
        console.error('Error resetting PIN:', error);
        showToast('Error resetting PIN', 'danger');
    })
    .finally(() => {
        // Restore button state
        button.innerHTML = originalHtml;
        button.disabled = false;
    });
}

function deleteStudent(studentId) {
    fetch(`/students/${studentId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove student row from table
            const row = document.querySelector(`input[value="${studentId}"]`).closest('tr');
            if (row) {
                row.remove();
            }

            showToast('Student deleted successfully', 'success');
            updateSelectedCount();
        } else {
            showToast(data.message || 'Failed to delete student', 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting student:', error);
        showToast('Error deleting student', 'danger');
    });
}

function deleteMultipleStudents(studentIds) {
    fetch('/students/delete-multiple', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ student_ids: studentIds })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove student rows from table
            studentIds.forEach(id => {
                const row = document.querySelector(`input[value="${id}"]`).closest('tr');
                if (row) row.remove();
            });

            showToast(`${data.deleted_count} students deleted successfully`, 'success');
            updateSelectedCount();
        } else {
            showToast(data.message || 'Failed to delete students', 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting students:', error);
        showToast('Error deleting students', 'danger');
    });
}

function generatePinCards() {
    const sessionId = getSessionIdFromUrl();
    if (!sessionId) {
        showToast('Session not found', 'danger');
        return;
    }

    // Open PIN cards in new window
    window.open(`/students/pin-cards/${sessionId}`, '_blank');
}

function initializeModals() {
    // Delete confirmation modal
    const deleteModal = document.getElementById('deleteStudentModal');
    if (deleteModal) {
        const confirmBtn = document.getElementById('confirmDeleteStudent');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', function() {
                if (currentStudentId) {
                    deleteStudent(currentStudentId);
                    bootstrap.Modal.getInstance(deleteModal).hide();
                }
            });
        }
    }
}

// Utility functions
function getCSRFToken() {
    const token = document.querySelector('meta[name=csrf-token]');
    return token ? token.getAttribute('content') : '';
}

function getSessionIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    const sessionIndex = pathParts.indexOf('sessions');
    return sessionIndex !== -1 && pathParts[sessionIndex + 1] ? pathParts[sessionIndex + 1] : null;
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"
                    data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    // Add to toast container or create one
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }

    toastContainer.appendChild(toast);

    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}
