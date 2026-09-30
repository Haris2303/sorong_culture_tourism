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

// Tombol dengan data-click-target meneruskan klik ke elemen lain (mis. CTA keadaan kosong -> tombol Tambah).
// Didelegasikan ke document karena isi tabel diganti lewat AJAX saat pencarian.
document.addEventListener('click', (e) => {
  const trigger = e.target.closest('[data-click-target]');
  if (!trigger) return;
  const target = document.getElementById(trigger.dataset.clickTarget);
  if (target) target.click();
});

// Perbarui angka total di header daftar setelah isi tabel diganti lewat AJAX.
function syncListTotal(container) {
  const marker = container && container.querySelector('[data-list-total]');
  const pill = document.getElementById('list-total');
  if (marker && pill) pill.textContent = marker.dataset.listTotal;
}

// Tekan "/" untuk langsung fokus ke kolom pencarian daftar.
document.addEventListener('keydown', (e) => {
  if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey) return;
  const tag = (document.activeElement && document.activeElement.tagName) || '';
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag) || (document.activeElement && document.activeElement.isContentEditable)) return;
  const input = document.querySelector('.table-search input[name="q"]');
  if (!input) return;
  e.preventDefault();
  input.focus();
  input.select();
});

// Jam & tanggal topbar dalam WIT (Asia/Jayapura).
document.addEventListener('DOMContentLoaded', () => {
  const timeEl = document.getElementById('topbar-time');
  const dateEl = document.getElementById('topbar-date');
  if (!timeEl || !dateEl) return;
  const timeFmt = new Intl.DateTimeFormat('id-ID', { timeZone: 'Asia/Jayapura', hour: '2-digit', minute: '2-digit', hour12: false });
  const dateFmt = new Intl.DateTimeFormat('id-ID', { timeZone: 'Asia/Jayapura', weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' });
  function tick() {
    const now = new Date();
    timeEl.textContent = `${timeFmt.format(now).replace('.', ':')} WIT`;
    dateEl.textContent = dateFmt.format(now);
  }
  tick();
  setInterval(tick, 15000);
});

// Modal tambah/sunting data (dipakai halaman Wisata & Budaya).
function setupAdminModal(overlayId) {
  const overlay = document.getElementById(overlayId);
  if (!overlay) return { open() {}, close() {} };

  function open() {
    overlay.hidden = false;
    document.body.classList.add('modal-open');
    const body = overlay.querySelector('.modal-body');
    if (body) body.scrollTop = 0;
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
  // Pengaman: panel modal tidak boleh ter-scroll sendiri (hanya .modal-body yang scroll).
  const panel = overlay.querySelector('.modal-panel');
  if (panel) panel.addEventListener('scroll', () => { panel.scrollTop = 0; panel.scrollLeft = 0; });
  const closeBtn = overlay.querySelector('.modal-close-btn');
  if (closeBtn) closeBtn.addEventListener('click', close);

  return { open, close };
}
