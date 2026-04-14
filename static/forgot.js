// forgot.js — two-step password reset
// Step 1: student enters email → backend sends 6-digit code to their inbox
// Step 2: student enters code + new password → backend verifies and updates

let submittedEmail = "";

window.addEventListener("DOMContentLoaded", () => {
    document.getElementById("requestForm").addEventListener("submit", handleRequest);
    document.getElementById("verifyForm").addEventListener("submit", handleVerify);
});

// ── Step 1: request code ──────────────────────────────────────────────────────

function handleRequest(event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim().toLowerCase();

    if (!email) {
        alert("Please enter your Davidson email.");
        return false;
    }
    if (!email.endsWith("@davidson.edu")) {
        alert("Please enter your @davidson.edu email.");
        return false;
    }

    const btn = document.querySelector("#requestForm input[type=submit]");
    btn.value    = "Sending...";
    btn.disabled = true;

    fetch("/api/forgot-password/request", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ email })
    })
    .then(res => {
        if (!res.ok) throw new Error("server");
        return res.json();
    })
    .then(() => {
        // Always show step 2 regardless of whether email exists —
        // prevents attackers from knowing which emails are registered
        submittedEmail = email;
        document.getElementById("step1").style.display = "none";
        document.getElementById("step2").style.display = "block";
    })
    .catch(() => {
        alert("Unable to reach the server. Please try again.");
        btn.value    = "Send Code";
        btn.disabled = false;
    });

    return false;
}

// ── Step 2: verify code and reset password ────────────────────────────────────

function handleVerify(event) {
    event.preventDefault();

    const code       = document.getElementById("code").value.trim();
    const newPwd     = document.getElementById("newPwd").value;
    const confirmPwd = document.getElementById("confirmPwd").value;

    if (!code || code.length !== 6 || !/^\d{6}$/.test(code)) {
        alert("Please enter the 6-digit code from your email.");
        return false;
    }
    if (!newPwd) {
        alert("Please enter a new password.");
        return false;
    }
    if (newPwd.length < 6) {
        alert("Password must be at least 6 characters.");
        return false;
    }
    if (newPwd !== confirmPwd) {
        alert("Passwords do not match. Please try again.");
        return false;
    }

    const btn = document.querySelector("#verifyForm input[type=submit]");
    btn.value    = "Resetting...";
    btn.disabled = true;

    fetch("/api/forgot-password/verify", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
            email:       submittedEmail,
            code:        code,
            newPassword: newPwd
        })
    })
    .then(res => {
        if (res.status === 400) return res.json().then(d => { throw new Error(d.error); });
        if (res.status === 404) throw new Error("Account not found.");
        if (!res.ok)            throw new Error("Server error. Please try again.");
        return res.json();
    })
    .then(() => {
        alert("Password reset successfully! You can now log in with your new password.");
        window.location.href = "/student";
    })
    .catch(err => {
        alert(err.message);
        btn.value    = "Reset Password";
        btn.disabled = false;
    });

    return false;
}
