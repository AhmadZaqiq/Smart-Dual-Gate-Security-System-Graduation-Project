window.MantrapEmployeeWizard = (function () {
    const state = {
        step: 1,
        rfidUid: "",
        fingerprintPosition: null,
        faceImagePath: "",
        enrollmentPoll: null,
    };

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute("content") : "";
    }

    function showStep(step) {
        state.step = step;

        document.querySelectorAll(".wizard-step").forEach((panel) => {
            panel.classList.toggle("active", Number(panel.dataset.step) === step);
        });

        document.querySelectorAll(".wizard-step-pill").forEach((pill) => {
            pill.classList.toggle("active", Number(pill.dataset.step) === step);
        });

        const backButton = document.getElementById("wizard-back");
        const nextButton = document.getElementById("wizard-next");
        const saveButton = document.getElementById("wizard-save");

        if (backButton) {
            backButton.disabled = step === 1;
        }

        if (nextButton) {
            nextButton.classList.toggle("d-none", step >= 5);
        }

        if (saveButton) {
            saveButton.classList.toggle("d-none", step !== 5);
        }
    }

    function setEnrollmentBox(message, tone) {
        const box = document.getElementById("enrollment-status-box");
        if (!box) {
            return;
        }

        box.textContent = message;
        box.className = "enrollment-status-box";

        if (tone) {
            box.classList.add(`enrollment-${tone}`);
        }
    }

    async function callEnrollment(path, method) {
        const response = await fetch(path, {
            method,
            headers: {
                "X-CSRFToken": getCsrfToken(),
                "Content-Type": "application/json",
            },
        });

        return response.json();
    }

    function stopEnrollmentPoll() {
        if (state.enrollmentPoll) {
            clearInterval(state.enrollmentPoll);
            state.enrollmentPoll = null;
        }
    }

    function startEnrollmentPoll(onSuccess) {
        stopEnrollmentPoll();

        state.enrollmentPoll = setInterval(async () => {
            try {
                const response = await fetch("/api/enrollment/status");
                const payload = await response.json();
                const data = payload.data || {};

                setEnrollmentBox(data.message || "Waiting...", data.state);

                if (data.state === "success") {
                    stopEnrollmentPoll();
                    onSuccess(data);
                }

                if (data.state === "timeout" || data.state === "error" || data.state === "cancelled") {
                    stopEnrollmentPoll();
                }
            } catch (error) {
                console.warn("Enrollment poll failed", error);
            }
        }, 1000);
    }

    async function startRfidEnrollment() {
        setEnrollmentBox("Starting RFID registration...", "loading");

        const result = await callEnrollment("/api/enrollment/rfid/start", "POST");

        if (!result.success || result.data?.success === false) {
            setEnrollmentBox(result.error || result.data?.message || "Unable to start RFID enrollment.", "error");
            return;
        }

        startEnrollmentPoll((data) => {
            state.rfidUid = data.uid || "";
            document.getElementById("review-rfid").textContent = state.rfidUid || "Not registered";
            document.getElementById("wizard-rfid-preview").textContent = state.rfidUid;
            setEnrollmentBox("RFID card detected successfully.", "success");
            document.getElementById("wizard-rfid-preview")?.classList.add("enrollment-success");
        });
    }

    async function startFingerprintEnrollment() {
        setEnrollmentBox("Place finger on sensor...", "loading");

        const result = await callEnrollment("/api/enrollment/fingerprint/start", "POST");

        if (!result.success || result.data?.success === false) {
            setEnrollmentBox(result.error || result.data?.message || "Unable to start fingerprint enrollment.", "error");
            return;
        }

        startEnrollmentPoll((data) => {
            state.fingerprintPosition = data.position || null;
            document.getElementById("review-fingerprint").textContent = state.fingerprintPosition ?? "Not enrolled";
            setEnrollmentBox("Fingerprint enrolled successfully.", "success");
        });
    }

    async function cancelEnrollment() {
        stopEnrollmentPoll();
        await callEnrollment("/api/enrollment/cancel", "POST");
        setEnrollmentBox("Enrollment cancelled.", "cancelled");
    }

    function validateStep(step) {
        if (step === 1) {
            const required = ["employee_number", "first_name", "second_name", "third_name", "last_name"];
            for (const fieldName of required) {
                const field = document.querySelector(`[name="${fieldName}"]`);
                if (!field || !field.value.trim()) {
                    window.alert("Please complete all employee information fields.");
                    return false;
                }
            }
        }

        return true;
    }

    function populateReview() {
        const mapping = [
            ["review-employee-number", "employee_number"],
            ["review-full-name", null],
            ["review-rfid", null],
            ["review-fingerprint", null],
            ["review-face", null],
        ];

        mapping.forEach(([targetId, fieldName]) => {
            const target = document.getElementById(targetId);
            if (!target) {
                return;
            }

            if (targetId === "review-full-name") {
                const parts = ["first_name", "second_name", "third_name", "last_name"]
                    .map((name) => document.querySelector(`[name="${name}"]`)?.value.trim())
                    .filter(Boolean);
                target.textContent = parts.join(" ");
                return;
            }

            if (targetId === "review-rfid") {
                target.textContent = state.rfidUid || "Not registered";
                return;
            }

            if (targetId === "review-fingerprint") {
                target.textContent = state.fingerprintPosition ?? "Not enrolled";
                return;
            }

            if (targetId === "review-face") {
                target.textContent = state.faceImagePath || "Not uploaded";
                return;
            }

            if (fieldName) {
                target.textContent = document.querySelector(`[name="${fieldName}"]`)?.value.trim() || "—";
            }
        });
    }

    async function saveEmployee() {
        const saveButton = document.getElementById("wizard-save");
        saveButton.disabled = true;
        saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...';

        const payload = {
            employee_number: document.querySelector('[name="employee_number"]').value.trim(),
            first_name: document.querySelector('[name="first_name"]').value.trim(),
            second_name: document.querySelector('[name="second_name"]').value.trim(),
            third_name: document.querySelector('[name="third_name"]').value.trim(),
            last_name: document.querySelector('[name="last_name"]').value.trim(),
            rfid_uid: state.rfidUid || null,
            fingerprint_position: state.fingerprintPosition,
            face_image_path: state.faceImagePath || null,
        };

        try {
            const response = await fetch("/api/employees/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();

            if (!result.success) {
                window.alert(result.error || "Failed to save employee.");
                return;
            }

            window.location.href = `/employees/${result.data.employee_id}`;
        } catch (error) {
            window.alert("Unable to save employee.");
            console.error(error);
        } finally {
            saveButton.disabled = false;
            saveButton.innerHTML = '<i class="ti ti-device-floppy me-1"></i> Save Employee';
        }
    }

    function bindEvents() {
        document.getElementById("wizard-next")?.addEventListener("click", () => {
            if (!validateStep(state.step)) {
                return;
            }

            if (state.step === 4) {
                const faceInput = document.querySelector('[name="face_image_path"]');
                state.faceImagePath = faceInput?.value.trim() || "";
                populateReview();
            }

            showStep(Math.min(state.step + 1, 5));
        });

        document.getElementById("wizard-back")?.addEventListener("click", () => {
            showStep(Math.max(state.step - 1, 1));
        });

        document.getElementById("wizard-save")?.addEventListener("click", saveEmployee);

        document.getElementById("rfid-start-btn")?.addEventListener("click", startRfidEnrollment);
        document.getElementById("rfid-retry-btn")?.addEventListener("click", startRfidEnrollment);
        document.getElementById("rfid-cancel-btn")?.addEventListener("click", cancelEnrollment);

        document.getElementById("fingerprint-start-btn")?.addEventListener("click", startFingerprintEnrollment);
        document.getElementById("fingerprint-retry-btn")?.addEventListener("click", startFingerprintEnrollment);
        document.getElementById("fingerprint-cancel-btn")?.addEventListener("click", cancelEnrollment);
    }

    return {
        init() {
            bindEvents();
            showStep(1);
        },
    };
})();
