// Local2Farm JavaScript Utilities

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss flash alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // 2. Initialize Bootstrap Tooltips if available
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 3. Quick Demo Login Fillers
    const fillFarmerBtn = document.getElementById('fillFarmerDemo');
    if (fillFarmerBtn) {
        fillFarmerBtn.addEventListener('click', function () {
            const emailInput = document.getElementById('email');
            const passInput = document.getElementById('password');
            const roleSelect = document.getElementById('role');
            if (emailInput && passInput) {
                emailInput.value = 'ramesh@farmer.com';
                passInput.value = 'farmer123';
                if (roleSelect) roleSelect.value = 'farmer';
            }
        });
    }

    const fillAdminBtn = document.getElementById('fillAdminDemo');
    if (fillAdminBtn) {
        fillAdminBtn.addEventListener('click', function () {
            const emailInput = document.getElementById('email');
            const passInput = document.getElementById('password');
            const roleSelect = document.getElementById('role');
            if (emailInput && passInput) {
                emailInput.value = 'admin@local2farm.com';
                passInput.value = 'admin123';
                if (roleSelect) roleSelect.value = 'admin';
            }
        });
    }

    // 4. Form confirmation for deletions
    const deleteForms = document.querySelectorAll('.confirm-delete');
    deleteForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});
