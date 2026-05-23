window.MantrapEmployeeToggle = (function () {
    function updateStatusLabel(toggleInput, isActive) {
        const row = toggleInput.closest("tr");
        const label = row ? row.querySelector("[data-employee-status-label]") : null;

        if (!label) {
            return;
        }

        label.textContent = isActive ? "Active" : "Inactive";
        label.classList.toggle("is-active", isActive);
        label.classList.toggle("is-inactive", !isActive);
    }

    async function updateStatus(employeeId, isActive, toggleInput) {
        toggleInput.disabled = true;

        const statusWrap = toggleInput.closest(".employees-status-wrap");
        if (statusWrap) {
            statusWrap.classList.add("opacity-50");
        }

        try {
            const response = await fetch(`/api/employees/${employeeId}/active`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.content || ""
                },
                body: JSON.stringify({ is_active: isActive })
            });

            const payload = await response.json();

            if (!response.ok || !payload.success) {
                toggleInput.checked = !isActive;
                updateStatusLabel(toggleInput, !isActive);
                window.alert(payload.error || "Unable to update employee status.");
                return;
            }

            updateStatusLabel(toggleInput, isActive);
        } catch (error) {
            toggleInput.checked = !isActive;
            updateStatusLabel(toggleInput, !isActive);
            window.alert("Unable to contact employee status API.");
        } finally {
            toggleInput.disabled = false;

            if (statusWrap) {
                statusWrap.classList.remove("opacity-50");
            }
        }
    }

    function bindToggles() {
        document.querySelectorAll(".employee-active-toggle").forEach(function (toggleInput) {
            updateStatusLabel(toggleInput, toggleInput.checked);

            toggleInput.addEventListener("change", function () {
                const employeeId = toggleInput.dataset.employeeId;

                if (!employeeId) {
                    return;
                }

                updateStatus(employeeId, toggleInput.checked, toggleInput);
            });
        });
    }

    return {
        init: bindToggles
    };
})();


/* ===== EMPLOYEE SOFT DELETE JS START ===== */
(function () {
    "use strict";

    async function softDeleteEmployee(button) {
        const employeeId = button.dataset.employeeId;
        const employeeName = button.dataset.employeeName || "this employee";

        if (!employeeId) {
            return;
        }

        const confirmed = window.confirm(
            `Delete ${employeeName}?`
        );

        if (!confirmed) {
            return;
        }

        const originalHtml = button.innerHTML;

        try {
            button.disabled = true;
            button.innerHTML = "Deleting...";

            const response = await fetch(`/employees/api/${employeeId}/soft-delete`, {
                method: "POST",
                headers: {
                    "Accept": "application/json"
                }
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Delete failed.");
            }

            const row = document.querySelector(`[data-employee-row="${employeeId}"]`);

            if (row) {
                row.style.transition = "opacity 0.2s ease, transform 0.2s ease";
                row.style.opacity = "0";
                row.style.transform = "translateX(12px)";

                setTimeout(() => {
                    row.remove();
                }, 220);
            }
        } catch (error) {
            alert(error.message);
            button.disabled = false;
            button.innerHTML = originalHtml;
        }
    }

    function bindSoftDeleteButtons() {
        document.querySelectorAll(".employee-delete-btn").forEach((button) => {
            if (button.dataset.boundDelete === "1") {
                return;
            }

            button.dataset.boundDelete = "1";
            button.addEventListener("click", () => softDeleteEmployee(button));
        });
    }

    document.addEventListener("DOMContentLoaded", bindSoftDeleteButtons);
})();
/* ===== EMPLOYEE SOFT DELETE JS END ===== */

