(function () {
    "use strict";

    const Wizard = {
        currentStep: 1,
        totalSteps: 5,
        pollTimer: null,

        data: {
            employee_number: "",
            first_name: "",
            second_name: "",
            third_name: "",
            last_name: "",
            rfid_uid: "",
            fingerprint_position: "",
            face_image_path: ""
        },

        init() {
            this.cacheElements();
            this.bindEvents();
            this.showStep(1);
            this.updateReview();
        },

        cacheElements() {
            this.stepPills = document.querySelectorAll(".wizard-step-pill");
            this.stepPanels = document.querySelectorAll(".wizard-step");

            this.backBtn = document.getElementById("wizard-back");
            this.nextBtn = document.getElementById("wizard-next");
            this.saveBtn = document.getElementById("wizard-save");

            this.rfidStartBtn = document.getElementById("rfid-start-btn");
            this.rfidRetryBtn = document.getElementById("rfid-retry-btn");
            this.rfidCancelBtn = document.getElementById("rfid-cancel-btn");

            this.fingerprintStartBtn = document.getElementById("fingerprint-start-btn");
            this.fingerprintRetryBtn = document.getElementById("fingerprint-retry-btn");
            this.fingerprintCancelBtn = document.getElementById("fingerprint-cancel-btn");

            this.rfidStatusBox = document.getElementById("enrollment-status-box");
            this.fingerprintStatusBox = document.getElementById("fingerprint-status-box");

            this.rfidPreview = document.getElementById("wizard-rfid-preview");
            this.fingerprintPreview = document.getElementById("wizard-fingerprint-preview");

            this.inputs = {
                employee_number: document.querySelector('[name="employee_number"]'),
                first_name: document.querySelector('[name="first_name"]'),
                second_name: document.querySelector('[name="second_name"]'),
                third_name: document.querySelector('[name="third_name"]'),
                last_name: document.querySelector('[name="last_name"]'),
                face_image_path: document.querySelector('[name="face_image_path"]')
            };

            this.review = {
                employee_number: document.getElementById("review-employee-number"),
                full_name: document.getElementById("review-full-name"),
                rfid: document.getElementById("review-rfid"),
                fingerprint: document.getElementById("review-fingerprint"),
                face: document.getElementById("review-face")
            };
        },

        bindEvents() {
            if (this.backBtn) {
                this.backBtn.addEventListener("click", () => this.previousStep());
            }

            if (this.nextBtn) {
                this.nextBtn.addEventListener("click", () => this.nextStep());
            }

            if (this.saveBtn) {
                this.saveBtn.addEventListener("click", () => this.saveEmployee());
            }

            if (this.rfidStartBtn) {
                this.rfidStartBtn.addEventListener("click", () => this.startRfidEnrollment());
            }

            if (this.rfidRetryBtn) {
                this.rfidRetryBtn.addEventListener("click", () => this.startRfidEnrollment());
            }

            if (this.rfidCancelBtn) {
                this.rfidCancelBtn.addEventListener("click", () => this.cancelEnrollment("rfid"));
            }

            if (this.fingerprintStartBtn) {
                this.fingerprintStartBtn.addEventListener("click", () => this.startFingerprintEnrollment());
            }

            if (this.fingerprintRetryBtn) {
                this.fingerprintRetryBtn.addEventListener("click", () => this.startFingerprintEnrollment());
            }

            if (this.fingerprintCancelBtn) {
                this.fingerprintCancelBtn.addEventListener("click", () => this.cancelEnrollment("fingerprint"));
            }

            Object.values(this.inputs).forEach((input) => {
                if (!input) {
                    return;
                }

                input.addEventListener("input", () => {
                    this.collectFormData();
                    this.updateReview();
                });
            });
        },

        collectFormData() {
            Object.keys(this.inputs).forEach((key) => {
                if (this.inputs[key]) {
                    this.data[key] = this.inputs[key].value.trim();
                }
            });
        },

        showStep(step) {
            this.currentStep = Math.max(1, Math.min(this.totalSteps, step));

            this.stepPills.forEach((pill) => {
                const pillStep = Number(pill.dataset.step);
                pill.classList.toggle("active", pillStep === this.currentStep);
                pill.classList.toggle("completed", pillStep < this.currentStep);
            });

            this.stepPanels.forEach((panel) => {
                const panelStep = Number(panel.dataset.step);
                panel.classList.toggle("active", panelStep === this.currentStep);
            });

            if (this.backBtn) {
                this.backBtn.disabled = this.currentStep === 1;
            }

            if (this.nextBtn) {
                this.nextBtn.classList.toggle("d-none", this.currentStep === this.totalSteps);
            }

            if (this.saveBtn) {
                this.saveBtn.classList.toggle("d-none", this.currentStep !== this.totalSteps);
            }

            this.collectFormData();
            this.updateReview();
        },

        nextStep() {
            this.collectFormData();

            if (this.currentStep === 1 && !this.validateInformation()) {
                return;
            }

            this.showStep(this.currentStep + 1);
        },

        previousStep() {
            this.showStep(this.currentStep - 1);
        },

        validateInformation() {
            const requiredKeys = ["employee_number", "first_name", "second_name", "third_name", "last_name"];
            const missing = requiredKeys.filter((key) => !this.data[key]);

            if (missing.length > 0) {
                this.showMessage("Please fill all employee information fields.", "error");
                return false;
            }

            return true;
        },

        setStatus(type, message, state) {
            const box = type === "fingerprint" ? this.fingerprintStatusBox : this.rfidStatusBox;

            if (!box) {
                return;
            }

            box.textContent = message || "";
            box.classList.remove("is-success", "is-error", "is-warning", "is-running");

            if (state === "success") {
                box.classList.add("is-success");
            } else if (state === "error") {
                box.classList.add("is-error");
            } else if (state === "cancelled") {
                box.classList.add("is-warning");
            } else {
                box.classList.add("is-running");
            }
        },

        async startRfidEnrollment() {
            this.data.rfid_uid = "";
            this.updateRfidPreview("—");
            this.setStatus("rfid", "Starting RFID registration...", "running");

            await this.postJson("/employees/api/enrollment/rfid/start", {});
            this.startPolling("rfid");
        },

        async startFingerprintEnrollment() {
            this.data.fingerprint_position = "";
            this.updateFingerprintPreview("—");
            this.setStatus("fingerprint", "Starting fingerprint enrollment...", "running");

            await this.postJson("/employees/api/enrollment/fingerprint/start", {});
            this.startPolling("fingerprint");
        },

        async cancelEnrollment(type) {
            try {
                await this.postJson("/employees/api/enrollment/cancel", {});
                this.stopPolling();
                this.setStatus(type, "Enrollment cancelled.", "cancelled");
            } catch (error) {
                this.setStatus(type, error.message, "error");
            }
        },

        startPolling(expectedType) {
            this.stopPolling();

            this.pollTimer = setInterval(() => {
                this.fetchEnrollmentStatus(expectedType);
            }, 900);

            this.fetchEnrollmentStatus(expectedType);
        },

        stopPolling() {
            if (this.pollTimer) {
                clearInterval(this.pollTimer);
                this.pollTimer = null;
            }
        },

        async fetchEnrollmentStatus(expectedType) {
            try {
                const response = await fetch("/employees/api/enrollment/status", {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    }
                });

                const data = await response.json();

                if (data.type && data.type !== expectedType) {
                    return;
                }

                const state = data.state || "idle";
                const message = data.message || "Waiting for enrollment status...";

                this.setStatus(expectedType, message, state);

                if (expectedType === "rfid") {
                    const uid = data.rfid_uid || data.uid || data.uid_id || data.rfid_id || data.id || data.RFIDUID;

                    if (uid) {
                        this.data.rfid_uid = String(uid);
                        this.updateRfidPreview(this.data.rfid_uid);
                    }
                }

                if (expectedType === "fingerprint") {
                    const position = data.fingerprint_position ?? data.position ?? data.slot ?? data.FingerprintPosition;

                    if (position !== undefined && position !== null && position !== "") {
                        this.data.fingerprint_position = String(position);
                        this.updateFingerprintPreview(this.data.fingerprint_position);
                    }
                }

                this.updateReview();

                if (state === "success" || state === "error" || state === "cancelled") {
                    this.stopPolling();
                }
            } catch (error) {
                this.setStatus(expectedType, error.message, "error");
                this.stopPolling();
            }
        },

        updateRfidPreview(value) {
            if (this.rfidPreview) {
                this.rfidPreview.textContent = value || "—";
            }
        },

        updateFingerprintPreview(value) {
            if (this.fingerprintPreview) {
                this.fingerprintPreview.textContent = value || "—";
            }
        },

        updateReview() {
            this.collectFormData();

            const fullName = [
                this.data.first_name,
                this.data.second_name,
                this.data.third_name,
                this.data.last_name
            ].filter(Boolean).join(" ");

            if (this.review.employee_number) {
                this.review.employee_number.textContent = this.data.employee_number || "—";
            }

            if (this.review.full_name) {
                this.review.full_name.textContent = fullName || "—";
            }

            if (this.review.rfid) {
                this.review.rfid.textContent = this.data.rfid_uid || "—";
            }

            if (this.review.fingerprint) {
                this.review.fingerprint.textContent = this.data.fingerprint_position || "—";
            }

            if (this.review.face) {
                this.review.face.textContent = this.data.face_image_path || "—";
            }
        },

        async saveEmployee() {
            this.collectFormData();

            if (!this.validateInformation()) {
                this.showStep(1);
                return;
            }

            const payload = {
                employee_number: this.data.employee_number,
                first_name: this.data.first_name,
                second_name: this.data.second_name,
                third_name: this.data.third_name,
                last_name: this.data.last_name,
                rfid_uid: this.data.rfid_uid,
                fingerprint_position: this.data.fingerprint_position,
                face_image_path: this.data.face_image_path
            };

            try {
                this.setButtonLoading(this.saveBtn, true, "Saving...");
                const result = await this.postJson("/employees/api/enrollment/save", payload);

                if (!result.success) {
                    throw new Error(result.message || "Save failed.");
                }

                this.showMessage(result.message || "Employee saved successfully.", "success");

                setTimeout(() => {
                    window.location.href = "/employees";
                }, 900);
            } catch (error) {
                this.showMessage(error.message, "error");
            } finally {
                this.setButtonLoading(this.saveBtn, false);
            }
        },

        async postJson(url, payload) {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify(payload || {})
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.message || "Request failed.");
            }

            return data;
        },

        setButtonLoading(button, isLoading, loadingText) {
            if (!button) {
                return;
            }

            if (isLoading) {
                button.dataset.originalText = button.innerHTML;
                button.disabled = true;
                button.innerHTML = loadingText || "Loading...";
            } else {
                button.disabled = false;

                if (button.dataset.originalText) {
                    button.innerHTML = button.dataset.originalText;
                }
            }
        },

        showMessage(message, type) {
            const alertClass = type === "success" ? "alert-success" : "alert-danger";

            const wrapper = document.createElement("div");
            wrapper.className = `alert ${alertClass} alert-dismissible fade show mt-3`;
            wrapper.innerHTML = `
                <div>${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            const cardBody = document.querySelector(".card .card-body");

            if (cardBody) {
                cardBody.prepend(wrapper);
            } else {
                alert(message);
            }

            setTimeout(() => {
                wrapper.remove();
            }, 5000);
        }
    };

    window.MantrapEmployeeWizard = Wizard;
})();
