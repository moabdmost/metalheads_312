// JavaScript for student.html
// Calls /api/login which validates credentials against subs_copy.json
// and stamps the student's email onto their submission record so the
// staff dashboard knows where to send the receipt on completion.

window.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('loginForm');
    if (form) {
        form.addEventListener('submit', submit_function);
    }
});

function submit_function(event) {
    event.preventDefault();

    const email_input      = document.getElementById("email");
    const student_id_input = document.getElementById("studentID");
    const password_input   = document.getElementById("pwd");

    const email     = email_input.value.trim().toLowerCase();
    const studentId = student_id_input.value.trim();
    const pwd       = password_input.value;

    // ── Client-side validation ────────────────────────────────────────────
    if (!email && !studentId) {
        alert("Please enter either your @davidson.edu email or your Student ID.");
        return false;
    }

    if (!email && studentId && !/^\d{9}$/.test(studentId)) {
        alert("Please enter your 9-digit Student ID.");
        return false;
    }

    if (email && !email.endsWith("@davidson.edu")) {
        alert("Please enter your @davidson.edu email.");
        return false;
    }

    if (!pwd) {
        alert("Please enter your password.");
        return false;
    }

    // ── POST to /api/login ────────────────────────────────────────────────
    // Backend validates credentials and stamps login_email onto the
    // submission — this is the link between student login and staff dashboard.
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, studentId, password: pwd })
    })
    .then(res => {
        if (res.status === 401) throw new Error('invalid');
        if (!res.ok)            throw new Error('server');
        return res.json();
    })
    .then(student => {
        // Show a simple confirmation alert then redirect
        alert(`Checked in successfully! Your exam session has started, ${student.studentName}.`);
        window.location.href = '/student'; // stay on page or redirect wherever you want
    })
    .catch(err => {
        if (err.message === 'invalid') {
            alert('Invalid email/ID or password. Please try again.');
        } else {
            alert('Unable to reach the server. Please try again.');
            console.error('Login error:', err);
        }
    });

    return false;
}

function handleCredentialResponse(response) {
    console.log("Encoded JWT ID token: " + response.credential);

    // Decode JWT (basic client-side decode)
    const data = parseJwt(response.credential);

    console.log("User Info:", data);
    const email = data.email;
    if (email && email.endsWith("@davidson.edu")) {
        // Optionally, you could auto-fill the email field and submit the form here
        document.getElementById("email").value = email;
        // You could also trigger the form submission if desired
        // document.getElementById("loginForm").submit();
    

    // Example:
    document.getElementById("user-info").innerText =
        `Welcome ${data.name} (${data.email})`;
    } else {
        alert("Please sign in with a @davidson.edu account.");
    }
}

function parseJwt(token) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
        atob(base64)
            .split('')
            .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
    );

    return JSON.parse(jsonPayload);
}