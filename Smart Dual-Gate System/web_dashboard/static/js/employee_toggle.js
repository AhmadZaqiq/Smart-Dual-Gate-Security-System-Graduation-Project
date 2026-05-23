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
