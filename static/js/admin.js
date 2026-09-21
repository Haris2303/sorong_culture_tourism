// Interaksi ringan panel admin (dialog konfirmasi ditangani inline via onsubmit).
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach((el) => {
    setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });
});

// Modal tambah/sunting data (dipakai halaman Wisata & Budaya).
function setupAdminModal(overlayId) {
  const overlay = document.getElementById(overlayId);
  if (!overlay) return { open() {}, close() {} };

  function open() {
    overlay.hidden = false;
    document.body.classList.add('modal-open');
  }
  function close() {
    overlay.hidden = true;
    document.body.classList.remove('modal-open');
  }

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !overlay.hidden) close();
  });
  const closeBtn = overlay.querySelector('.modal-close-btn');
  if (closeBtn) closeBtn.addEventListener('click', close);

  return { open, close };
}
