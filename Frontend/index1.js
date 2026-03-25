
  const API_URL = 'http://localhost:5000/api';
  let userRegisterData = {};

  function showModal(type) {
    document.getElementById('authModal').classList.add('active');
    clearMsg();
    switchPane(type);
  }
  function closeModal() {
    document.getElementById('authModal').classList.remove('active');
  }
 
  function switchPane(type) {
    document.getElementById('loginPane').style.display = type === 'login' ? 'block' : 'none';
    document.getElementById('registerPane').style.display = type === 'register' ? 'block' : 'none';
    clearMsg();
  }

  function showMsg(msg, type) {
    const el = document.getElementById('msgBanner');
    el.textContent = msg;
    el.className = 'msg-banner ' + (type === 'error' ? 'msg-error' : 'msg-success');
  }
  function clearMsg() {
    const el = document.getElementById('msgBanner');
    el.className = 'msg-banner';
    el.textContent = '';
  }

  async function doLogin() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    if (!email || !password) return showMsg('Please fill in all fields.', 'error');
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (res.ok) {
        showMsg('Login successful! Redirecting...', 'success');
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 1000);
      } else {
        showMsg(data.error || 'Invalid email or password.', 'error');
      }
    } catch {
      showMsg('Cannot reach server. Please try again.', 'error');
    }
  }

  async function doRegister() {
  const userData = {
    name: document.getElementById('regName').value,
    email: document.getElementById('regEmail').value,
    password: document.getElementById('regPassword').value,
    phone: document.getElementById('regPhone').value   // ✅ FIX
  };

  if (!userData.name || !userData.email || !userData.password || !userData.phone) {
    return showMsg('Please fill in all fields.', 'error');
  }

  try {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });

    const data = await res.json();

    if (res.ok) {
      showMsg('Registration successful! Please login.', 'success');
      setTimeout(() => switchPane('login'), 1000);  // ✅ no OTP
    } else {
      showMsg(data.error || 'Registration failed.', 'error');
    }

  } catch {
    showMsg('Cannot reach server. Please try again.', 'error');
  }
}

