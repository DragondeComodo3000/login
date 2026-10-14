const page = document.body.dataset.page;
const message = document.getElementById('message');

if (page === 'login') {
  document.getElementById('toggle-password').addEventListener('click', () => {
    const field = document.getElementById('password');
    field.type = field.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    message.textContent = '';
    const button = event.currentTarget.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: document.getElementById('email').value,
          password: document.getElementById('password').value,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'No se pudo iniciar sesión.');
      window.location.assign('/profile');
    } catch (error) {
      message.textContent = error.message;
      button.disabled = false;
    }
  });
}

if (page === 'profile') {
  fetch('/api/profile').then(async (response) => {
    if (response.status === 401) return window.location.replace('/');
    if (!response.ok) throw new Error('No se pudo cargar el perfil.');
    const profile = await response.json();
    document.getElementById('profile-name').textContent = profile.name;
    document.getElementById('profile-email').textContent = profile.email;
    document.getElementById('profile-id').textContent = `#${String(profile.id).padStart(4, '0')}`;
    document.getElementById('profile-role').textContent = profile.role;
    document.getElementById('avatar').textContent = profile.name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase();
  }).catch((error) => { message.textContent = error.message; });

  document.getElementById('logout').addEventListener('click', async () => {
    try {
      await fetch('/api/logout', { method: 'POST' });
      window.location.assign('/');
    } catch (error) { message.textContent = 'No se pudo cerrar la sesión.'; }
  });
}
