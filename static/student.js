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

    // Call the API to validate login
    fetch('/api/validate-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            email: email, 
            studentId: studentId, 
            password: pwd 
        })
    })
        .then(resp => resp.json())
        .then(data => {
            if (data.success) {
                // Save student info to localStorage
                localStorage.setItem('loggedInStudent', JSON.stringify(data.student));
                
                // Redirect to exam selection page
                window.location.href = '/exam-selection';
            } else {
                alert('Invalid email/ID or password.');
            }
        })
        .catch(err => {
            console.error('Login error:', err);
            alert('Unable to validate credentials at this time.');
        });

    return false;
}
