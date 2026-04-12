// ── Helpers ───────────────────────────────────────────────────────────────────
/**
 * Displays an inline login error message to the student.
 * @param {string} msg - The error text to show.
 */
function showError(msg) {
  const el = document.getElementById('login-error');
  el.textContent = msg;
  el.style.display = 'block';
}

/**
 * Clears any visible login error message from the form.
 */
function clearError() {
  const el = document.getElementById('login-error');
  el.textContent = '';
  el.style.display = 'none';
}

// ── Progressive signup reveal ─────────────────────────────────────────────────
/**
 * Reveals the registration fields and pre-fills values when an account is not found.
 * @param {string} email - The email address to prepopulate.
 * @param {string} studentId - The student ID to prepopulate.
 * @param {string} password - The password to prepopulate.
 */
function showRegistrationFields(email, studentId, password) {
  if (email)     document.getElementById('su-email').value = email;
  if (studentId) document.getElementById('su-sid').value   = studentId;
                 document.getElementById('su-pwd').value   = password;

  document.getElementById('card-subtitle').textContent =
    "We didn't find an account — fill in the details below to register.";

  document.getElementById('reg-fields').style.display = '';
  document.querySelector('#loginForm .btn-primary').textContent = 'Create Account & Sign In';
  document.getElementById('loginForm').dataset.mode = 'signup';
  clearError();
}

// ── Single submit handler ─────────────────────────────────────────────────────
document.getElementById('loginForm').onsubmit = async (e) => {
  e.preventDefault();
  clearError();

  const mode = document.getElementById('loginForm').dataset.mode || 'login';

  if (mode === 'login') {
    await handleLogin();
  } else {
    await handleSignup();
  }
};

// ── Sign In ───────────────────────────────────────────────────────────────────
/**
 * Attempts to authenticate the student and either logs them in or prompts account creation.
 */
async function handleLogin() {
  const email     = document.getElementById('email').value.trim().toLowerCase();
  const studentId = document.getElementById('studentID').value.trim();
  const password  = document.getElementById('pwd').value;

  if (!email && !studentId) return showError('Enter your email or Student ID.');
  if (email && !email.endsWith('@davidson.edu')) return showError('Use your @davidson.edu email.');
  if (!password) return showError('Password is required.');

  try {
    const res  = await fetch('/api/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, studentId, password }),
    });
    const data = await res.json();

    if (res.status === 404) {
      showRegistrationFields(email, studentId, password);
      return;
    }
    if (!res.ok) return showError(data.error || 'Invalid credentials.');

    window.location.href = '/selection';
  } catch {
    showError('Unable to reach server.');
  }
}

// ── Sign Up ───────────────────────────────────────────────────────────────────
/**
 * Submits a new student signup request to the backend.
 * Performs client-side validation before sending the request.
 */
async function handleSignup() {
  const firstName = document.getElementById('su-fname').value.trim();
  const lastName  = document.getElementById('su-lname').value.trim();
  const email     = document.getElementById('su-email').value.trim().toLowerCase();
  const studentId = document.getElementById('su-sid').value.trim();
  const password  = document.getElementById('su-pwd').value;
  const password2 = document.getElementById('su-pwd2').value;

  if (!firstName || !lastName)         return showError('Enter your first and last name.');
  if (!email.endsWith('@davidson.edu')) return showError('Use your @davidson.edu email.');
  if (!/^\d{9}$/.test(studentId))      return showError('Student ID must be 9 digits.');
  if (password.length < 6)             return showError('Password must be at least 6 characters.');
  if (password !== password2)          return showError('Passwords do not match.');

  try {
    const res  = await fetch('/api/signup', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, studentId, password, firstName, lastName }),
    });
    const data = await res.json();

    if (!res.ok) return showError(data.error || 'Sign-up failed.');

    window.location.href = '/selection';
  } catch {
    showError('Unable to reach server.');
  }
}