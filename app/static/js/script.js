function toggleMenu() {
  document.querySelector('.nav-links').classList.toggle('open');
}

async function enviarFormulario(e) {
  e.preventDefault();
  const usuario = JSON.parse(sessionStorage.getItem('sn_usuario') || sessionStorage.getItem('usuario') || 'null');
  if (!usuario) {
    document.getElementById('modal-registro-contacto').style.display = 'flex';
    return;
  }
  const form = e.target;
  const nombre  = form.querySelector('input[type="text"]').value;
  const email   = form.querySelector('input[type="email"]').value;
  const mensaje = form.querySelector('textarea').value;
  const res = await fetch('/api/contacto', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ nombre, email, mensaje, id_usuario: usuario.id_usuario })
  });
  const data = await res.json();
  if (data.ok) {
    document.getElementById('form-msg').style.display = 'block';
    form.reset();
  }
}

function cerrarModalContacto() {
  document.getElementById('modal-registro-contacto').style.display = 'none';
}

// Scroll suave del indicador
document.querySelector('.scroll-indicator')?.addEventListener('click', () => {
  document.getElementById('pilares').scrollIntoView({ behavior: 'smooth' });
});

// Animación de entrada en scroll
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });

document.querySelectorAll('.pilar-card, .lote-card, .grimorio-content').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  observer.observe(el);
});

document.addEventListener('scroll', () => {
  document.querySelectorAll('.visible').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });
});
