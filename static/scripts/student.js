// ── Helpers ───────────────────────────────────────────────────────────────────
/**
 * shows the error message 
 * @param {*} id 
 * @param {*} msg 
 * @returns: None
 */
function showError(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.style.display = 'block';
  const sib = el.parentElement.querySelector('.success-msg');
  if (sib) sib.style.display = 'none';
}

/**
 * shows the success message in the specified element and hides any sibling error message.
 * @param {*} id the element id
 * @param {*} msg the message shown in the block
 * @returns none
 */
function showSuccess(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.style.display = 'block';
  const sib = el.parentElement.querySelector('.error-msg');
  if (sib) sib.style.display = 'none';
}

/**
 * clears the message
 * @param {*} id 
 * @returns  none
 */

function clearMsg(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = '';
  el.style.display = 'none';
}

// ── Tab switching ─────────────────────────────────────────────────────────────
/**
 * Switches between the login and sign-up panels based on the selected tab.
 * @param {*} tab tab which can be switched
 * @returns none. Switches between the login and sign-up panels based on the selected tab.
 */
function switchTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('panel-login').style.display  = isLogin ? '' : 'none';
  document.getElementById('panel-signup').style.display = isLogin ? 'none' : '';
  document.getElementById('tab-login').classList.toggle('active',  isLogin);
  document.getElementById('tab-signup').classList.toggle('active', !isLogin);
  clearMsg('login-error');
  clearMsg('signup-error');
}

// ── Forgot Password Modal ─────────────────────────────────────────────────────
/**
 * Opens the forgot password modal, pre-fills the email field if possible, 
 * and clears any existing messages.
 * @param: None 
 * @returns: None. Opens the forgot password modal, 
 * pre-fills the email field if possible,
 */
function openForgotModal() {
  document.getElementById('forgot-modal').style.display = 'flex';
  document.getElementById('forgot-email').value = document.getElementById('email').value || '';
  clearMsg('forgot-error');
  clearMsg('forgot-success');
}

/**
 * closes the forgot password modal when clicking outside the 
 * content area or on the close button.
 * @param {*} event 
 * @returns: None. Closes the forgot password modal when clicking 
 * outside the content area or on the close button.
 */
function closeForgotModal(event) {
  if (!event || event.target === document.getElementById('forgot-modal') || event.currentTarget === document.querySelector('.modal-close')) {
    document.getElementById('forgot-modal').style.display = 'none';
  }
}

/**
 * Handles the forgot password form submission by validating the 
 * email input and sending a reset request to the server.
 * @param: None 
 * @returns None
 */
async function handleForgotPassword() {
  const email = (document.getElementById('forgot-email').value || '').trim().toLowerCase();
  clearMsg('forgot-error');
  clearMsg('forgot-success');

  if (!email) return showError('forgot-error', 'Please enter your email.');
  if (!email.endsWith('@davidson.edu')) return showError('forgot-error', 'Use your @davidson.edu email.');

  // Tries to send a forgot password request to the server. 
  // On success, it shows a confirmation message. On failure, it shows an error message.
  try {
    const res  = await fetch('/api/forgot-password', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email }),
    });
    const data = await res.json();
    if (!res.ok) return showError('forgot-error', data.error || 'Something went wrong.');
    showSuccess('forgot-success', 'Check your inbox — a reset link has been sent!');
  } catch {
    showError('forgot-error', 'Unable to reach server.');
  }
}

// ── Login ─────────────────────────────────────────────────────────────────────
document.getElementById('loginForm').onsubmit = async (e) => {
  e.preventDefault();
  clearMsg('login-error');

  const email    = (document.getElementById('email').value || '').trim().toLowerCase();
  const password = document.getElementById('pwd').value;

  if (!email)                              return showError('login-error', 'Enter your Davidson email.');
  if (!email.endsWith('@davidson.edu'))    return showError('login-error', 'Use your @davidson.edu email.');
  if (!password)                           return showError('login-error', 'Password is required.');
  // Tries to send a login request to the server. On success, it redirects 
  // to the selection page.
  try {
    const res  = await fetch('/api/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (res.status === 404) {
      // No account — nudge toward sign up
      switchTab('signup');
      document.getElementById('su-email').value = email;
      showError('signup-error', "No account found for that email — please sign up below.");
      return;
    }
    if (!res.ok) return showError('login-error', data.error || 'Invalid credentials.');

    window.location.href = '/selection';
    // On success, it redirects to the selection page. On failure, it shows an error message.
  } catch {
    showError('login-error', 'Unable to reach server.');
  }
};

// ── Sign Up ───────────────────────────────────────────────────────────────────
/*
 * Handles the sign-up form submission by validating the input fields and 
 * sending a registration request to the server.
 */
document.getElementById('signupForm').onsubmit = async (e) => {
  e.preventDefault();
  clearMsg('signup-error');

  const firstName = (document.getElementById('su-fname').value || '').trim();
  const lastName  = (document.getElementById('su-lname').value || '').trim();
  const email     = (document.getElementById('su-email').value || '').trim().toLowerCase();
  const password  = document.getElementById('su-pwd').value;
  const password2 = document.getElementById('su-pwd2').value;

  if (!firstName || !lastName)          return showError('signup-error', 'Enter your first and last name.');
  if (!email.endsWith('@davidson.edu')) return showError('signup-error', 'Use your @davidson.edu email.');
  if (password.length < 6)             return showError('signup-error', 'Password must be at least 6 characters.');
  if (password !== password2)           return showError('signup-error', 'Passwords do not match.');
  // Tries to send a sign-up request to the server. 
  // On success, it redirects to the selection page.
  try {
    const res  = await fetch('/api/signup', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, password, firstName, lastName }),
    });
    const data = await res.json();

    if (!res.ok) return showError('signup-error', data.error || 'Sign-up failed.');

    window.location.href = '/selection';
  } catch {
    showError('signup-error', 'Unable to reach server.');
  }
};