window.MantrapEmployeeToggle = (function () {
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute("content") : "";
    }

    async function updateStatus(employeeId, isActive, toggleInput) {
        toggleInput.disabled = true;
        toggleInput.closest(".form-check")?.classList.add("opacity-50");

        try {
            const response = await fetch(`/api/employees/${employeeId}/active`, {
                method: "PATCH",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ is_active: isActive }),
            });

            const payload = await response.json();

            if (!payload.success) {
                toggleInput.checked = !isActive;
                window.alert(payload.error || "Unable to update employee status.");
            }
        } catch (error) {
            toggleInput.checked = !isActive;
            window.alert("Unable to reach employee API.");
            console.error(error);
        } finally {
            toggleInput.disabled = false;
            toggleInput.closest(".form-check")?.classList.remove("opacity-50");
        }
    }

    function bindToggles() {
        document.querySelectorAll(".employee-active-toggle").forEach((toggleInput) => {
            toggleInput.addEventListener("change", () => {
                const employeeId = toggleInput.dataset.employeeId;
                updateStatus(employeeId, toggleInput.checked, toggleInput);
            });
        });
    }

    return { init: bindToggles };
})();
