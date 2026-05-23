document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("password-toggle");
    const passwordInput = document.getElementById("password-input");

    if (!toggle || !passwordInput) {
        return;
    }

    toggle.addEventListener("click", function () {
        const isHidden = passwordInput.type === "password";
        passwordInput.type = isHidden ? "text" : "password";
        toggle.innerHTML = isHidden
            ? '<i class="ti ti-eye-off"></i>'
            : '<i class="ti ti-eye"></i>';
        toggle.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
    });
});
