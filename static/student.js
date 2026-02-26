

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

    // all valid – do not let the form submit normally; redirect manually
    event.preventDefault();
    window.location.href = 'https://www.espn.com/';
    return true;
}
