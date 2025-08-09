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

    // Initialize delete selected button (legacy)
    const deleteSelectedBtn = document.getElementById('deleteSelectedStudents');
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', handleDeleteSelected);
    }

    // Initialize new bulk actions
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', handleDeleteSelected);
    }

    const deselectAllBtn = document.getElementById('deselectAllBtn');
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', deselectAll);
    }

    const bulkResetPinsBtn = document.getElementById('bulkResetPinsBtn');
    if (bulkResetPinsBtn) {
        bulkResetPinsBtn.addEventListener('click', handleBulkResetPins);
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

    // Update count displays
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = count;
    }

    const countDisplayElement = document.getElementById('selectedCountDisplay');
    if (countDisplayElement) {
        countDisplayElement.textContent = count;
    }

    // Update delete button states
    const deleteBtn = document.getElementById('deleteSelectedStudents');
    if (deleteBtn) {
        deleteBtn.disabled = count === 0;
    }

    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.disabled = count === 0;
    }

    // Show/hide bulk actions bar
    const bulkActionsBar = document.getElementById('bulkActionsBar');
    if (bulkActionsBar) {
        bulkActionsBar.style.display = count > 0 ? 'block' : 'none';
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

function deselectAll() {
    const studentCheckboxes = document.querySelectorAll('.student-checkbox');
    studentCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });

    const selectAllCheckbox = document.getElementById('selectAllStudents');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }

    updateSelectedCount();
}

function handleBulkResetPins() {
    const selectedCheckboxes = document.querySelectorAll('.student-checkbox:checked');
    const studentNames = Array.from(selectedCheckboxes).map(cb =>
        cb.getAttribute('data-student-name')
    );

    if (studentNames.length === 0) return;

    const message = studentNames.length === 1
        ? `Reset PIN for ${studentNames[0]}?`
        : `Reset PINs for ${studentNames.length} students?`;

    if (confirm(message)) {
        const studentIds = Array.from(selectedCheckboxes).map(cb => cb.value);
        resetMultipleStudentPins(studentIds);
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
    // Show loading state
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const originalText = bulkDeleteBtn ? bulkDeleteBtn.innerHTML : '';
    if (bulkDeleteBtn) {
        bulkDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
        bulkDeleteBtn.disabled = true;
    }

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
            // Remove student rows from table with animation
            studentIds.forEach(id => {
                const row = document.querySelector(`input[value="${id}"]`).closest('tr');
                if (row) {
                    row.style.transition = 'opacity 0.3s';
                    row.style.opacity = '0.5';
                    setTimeout(() => row.remove(), 300);
                }
            });

            const message = data.deleted_count === 1
                ? '1 student deleted successfully'
                : `${data.deleted_count} students deleted successfully`;

            showToast(message, 'success');

            // Update counts after animation
            setTimeout(() => {
                updateSelectedCount();

                // Check if no students left and show empty state
                const remainingStudents = document.querySelectorAll('.student-checkbox').length;
                if (remainingStudents === 0) {
                    location.reload(); // Reload to show empty state
                }
            }, 400);
        } else {
            showToast(data.message || 'Failed to delete students', 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting students:', error);
        showToast('Error deleting students', 'danger');
    })
    .finally(() => {
        // Restore button state
        if (bulkDeleteBtn) {
            bulkDeleteBtn.innerHTML = originalText;
            bulkDeleteBtn.disabled = false;
        }
    });
}

function resetMultipleStudentPins(studentIds) {
    // Show loading state
    const bulkResetBtn = document.getElementById('bulkResetPinsBtn');
    const originalText = bulkResetBtn ? bulkResetBtn.innerHTML : '';
    if (bulkResetBtn) {
        bulkResetBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
        bulkResetBtn.disabled = true;
    }

    // Reset PINs sequentially to avoid overwhelming the server
    let completed = 0;
    let newPins = [];

    const resetNext = (index) => {
        if (index >= studentIds.length) {
            // All done - show results
            if (bulkResetBtn) {
                bulkResetBtn.innerHTML = originalText;
                bulkResetBtn.disabled = false;
            }

            if (newPins.length > 0) {
                showBulkPinResetResults(newPins);
                showToast(`${newPins.length} PINs reset successfully`, 'success');
            }
            return;
        }

        const studentId = studentIds[index];
        const studentCheckbox = document.querySelector(`input[value="${studentId}"]`);
        const studentName = studentCheckbox ? studentCheckbox.getAttribute('data-student-name') : 'Unknown';

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
                newPins.push({
                    studentId: studentId,
                    studentName: studentName,
                    newPin: data.new_pin
                });
            }
            completed++;
            resetNext(index + 1);
        })
        .catch(error => {
            console.error(`Error resetting PIN for student ${studentId}:`, error);
            completed++;
            resetNext(index + 1);
        });
    };

    resetNext(0);
}

function showBulkPinResetResults(results) {
    // Create a modal to display all the new PINs
    const modalHtml = `
        <div class="modal fade" id="bulkPinResetModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-key text-success"></i>
                            Bulk PIN Reset Results
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-success">
                            <i class="fas fa-info-circle"></i>
                            <strong>${results.length} PINs have been reset successfully.</strong>
                            Please write down these PINs and distribute them to students.
                        </div>

                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Student</th>
                                        <th>New PIN</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${results.map(result => `
                                        <tr>
                                            <td><strong>${result.studentName}</strong></td>
                                            <td><code class="fs-5">${result.newPin}</code></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Got It</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('bulkPinResetModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('bulkPinResetModal'));
    modal.show();

    // Clean up modal after hiding
    document.getElementById('bulkPinResetModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

function generatePinCards() {
    const sessionId = getSessionIdFromUrl();
    if (!sessionId) {
        showToast('Session not found', 'danger');
        return;
    }

    // Navigate to PIN cards preview page
    window.location.href = `/students/pin-cards/${sessionId}/preview`;
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
