/**
 * Reaction Badges JavaScript
 * Handles badge interactions with single-select behavior
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add a visual affordance for clickable containers
    document.querySelectorAll('.reaction-badges[data-clickable="true"]').forEach(function(container){
        container.classList.add('is-clickable');
    });

    // Add click handlers to all reaction badges
    document.addEventListener('click', function(e) {
        if (e.target.closest('.reaction-badge')) {
            const badgeElement = e.target.closest('.reaction-badge');
            const reactionContainer = badgeElement.closest('.reaction-badges');

            // Only handle clicks on clickable badges
            if (reactionContainer && reactionContainer.dataset.clickable === 'true') {
                const mediaId = reactionContainer.dataset.mediaId;
                const badgeType = badgeElement.dataset.badgeType;

                handleBadgeClick(mediaId, badgeType, badgeElement);
            }
        }
    });
});

function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

/**
 * Handle badge click with single-select behavior
 */
function handleBadgeClick(mediaId, badgeType, badgeElement) {
    // Show loading state
    const originalIcon = badgeElement.querySelector('.badge-icon');
    originalIcon.style.opacity = '0.5';

    // Make AJAX request
    fetch(`/media/${mediaId}/react/${badgeType}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBadgeDisplay(mediaId, data.counts, data.user_like);
        } else {
            console.error('Reaction failed:', data.error);
            showError(data.error || 'Failed to update reaction. Please try again.');
        }
    })
    .catch(error => {
        console.error('Reaction error:', error);
        showError('Network error. Please check your connection.');
    })
    .finally(() => {
        // Restore original state
        originalIcon.style.opacity = '';
    });
}

/**
 * Update badge display with new counts and user selection
 */
function updateBadgeDisplay(mediaId, counts, userLike) {
    const reactionContainer = document.querySelector(`[data-media-id="${mediaId}"]`);
    if (!reactionContainer) return;

    // Update counts
    const graphBadge = reactionContainer.querySelector('[data-badge-type="graph"] .badge-count');
    const eyeBadge = reactionContainer.querySelector('[data-badge-type="eye"] .badge-count');
    const readBadge = reactionContainer.querySelector('[data-badge-type="read"] .badge-count');

    if (graphBadge) graphBadge.textContent = counts.graph;
    if (eyeBadge) eyeBadge.textContent = counts.eye;
    if (readBadge) readBadge.textContent = counts.read;

    // Update selection states
    updateBadgeSelection(reactionContainer, 'graph', userLike.graph);
    updateBadgeSelection(reactionContainer, 'eye', userLike.eye);
    updateBadgeSelection(reactionContainer, 'read', userLike.read);

    // Show success feedback
    showSuccess('Reaction updated successfully!');
}

/**
 * Update individual badge selection state
 */
function updateBadgeSelection(container, badgeType, isSelected) {
    const badge = container.querySelector(`[data-badge-type="${badgeType}"] .badge-icon`);
    if (badge) {
        if (isSelected) {
            badge.classList.add('selected');
        } else {
            badge.classList.remove('selected');
        }
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    // You can customize this to use your preferred notification system
    // Prefer Bootstrap toast if available
    const containerId = 'toast-container';
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    toastEl.className = 'toast align-items-center text-bg-success border-0';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `<div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>`;
    container.appendChild(toastEl);
    try {
        const toast = new bootstrap.Toast(toastEl, { delay: 1800 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    } catch (e) {
        console.log('Success:', message);
    }
}

/**
 * Show error message
 */
function showError(message) {
    // You can customize this to use your preferred notification system
    const containerId = 'toast-container';
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    const toastEl = document.createElement('div');
    toastEl.className = 'toast align-items-center text-bg-danger border-0';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `<div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>`;
    container.appendChild(toastEl);
    try {
        const toast = new bootstrap.Toast(toastEl, { delay: 2000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    } catch (e) {
        console.error('Error:', message);
    }
}

/**
 * Initialize reactions for dynamically loaded content
 * Call this after loading new content via AJAX
 */
function initializeReactions() {
    // Re-initialize tooltips for new content
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        if (!tooltipTriggerEl._tooltip) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        }
    });
}

// Export for use in other scripts
window.ReactionBadges = {
    initialize: initializeReactions,
    handleClick: handleBadgeClick
};
