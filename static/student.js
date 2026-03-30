// JavaScript for student.html
// validates inputs and redirects when data is valid

window.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('loginForm');
    if (form) {
        form.addEventListener('submit', submit_function);
    }
});

function submit_function(event) {
    const email_input      = document.getElementById("email");
    const student_id_input = document.getElementById("studentID");
    const password_input   = document.getElementById("pwd");

    // require either email or student id
    if (email_input.value === "" && student_id_input.value === "") {
        alert("Please enter either your davidson email or student ID.");
        event.preventDefault();
        return false;
    }

    if (email_input.value === "" &&student_id_input.value && !/^\d{9}$/.test(student_id_input.value)) {
        alert("Please enter your 9-digit student ID.");
        event.preventDefault();
        return false;
    }

    if (email_input.value && !email_input.value.includes("@davidson.edu")) {
        alert("Please enter your @davidson.edu email.");
        event.preventDefault();
        return false;
    }

    if (password_input.value === "") {
        alert("Please enter your password.");
        event.preventDefault();
        return false;
    }

    // prevent normal submission until credentials are checked
    event.preventDefault();

    const email = email_input.value.trim().toLowerCase();
    const studentId = student_id_input.value.trim();
    const pwd = password_input.value;

    // Load the static JSON (copied to /static/subs_copy.json) and verify
    fetch('/data/subs_copy.json')
        .then(resp => resp.json())
        .then(jsonData => {
            const match = jsonData.find(student => {
                const emailMatch = email && student.email && student.email.toLowerCase() === email;
                const idMatch = studentId && student.studentId === studentId;
                return (emailMatch || idMatch) && student.password === pwd;
            });

            if (match) {
                // credentials valid — proceed
                window.location.href = 'https://www.espn.com/';
            } else {
                alert('Invalid email/ID or password.');
            }
        })
        .catch(err => {
            console.error('Failed to load credentials file:', err);
            alert('Unable to validate credentials at this time.');
        });

    return false;
}

function handleCredentialResponse(response) {
    console.log("Encoded JWT ID token: " + response.credential);

    // Decode JWT (basic client-side decode)
    const data = parseJwt(response.credential);

    console.log("User Info:", data);

    // Example:
    document.getElementById("user-info").innerText =
        `Welcome ${data.name} (${data.email})`;
    
    const email = data.email ? data.email.trim().toLowerCase() : "";
    console.log(email);
    // Load the static JSON (copied to /static/subs_copy.json) and verify
    fetch('/data/subs_copy.json')
        .then(resp => resp.json())
        .then(jsonData => {
            const match = jsonData.find(student => {
                const emailMatch = email && student.email && student.email.toLowerCase() === email;
                
                return (emailMatch);
            });

            if (match) {
                // credentials valid — proceed
                window.location.href = 'https://www.espn.com/';
            } else {
                alert('Invalid email');
            }
        })
        .catch(err => {
            console.error('Failed to load credentials file:', err);
            alert('Unable to validate credentials at this time.');
        });

    return false;
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