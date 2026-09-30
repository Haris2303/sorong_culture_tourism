// Notifikasi (toast) & dialog konfirmasi/peringatan admin, menggantikan alert()/confirm() bawaan browser.
//
//   AdminUI.toast('success' | 'error' | 'warning' | 'info', 'Pesan', { title, duration })
//   await AdminUI.confirm({ title, message, confirmText, tone: 'danger' | 'primary' })  -> true/false
//   await AdminUI.alert('Pesan', { title, type })
//
// Form dengan atribut data-confirm="Pesan" otomatis meminta konfirmasi sebelum dikirim.
(function () {
  const ICONS = {
    success: 'fa-circle-check',
    error: 'fa-circle-xmark',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info',
  };
  const TITLES = { success: 'Berhasil', error: 'Gagal', warning: 'Perhatian', info: 'Informasi' };

  function normalizeType(type) {
    if (type === 'danger') return 'error';
    return ICONS[type] ? type : 'info';
  }

  // ---------- Toast ----------
  let stack = null;
  function getStack() {
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      stack.setAttribute('aria-live', 'polite');
      stack.setAttribute('aria-atomic', 'false');
      document.body.appendChild(stack);
    }
    return stack;
  }

  function toast(type, message, options = {}) {
    type = normalizeType(type);
    const duration = options.duration ?? (type === 'error' ? 7000 : 4500);

    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const icon = document.createElement('span');
    icon.className = 'toast-icon';
    icon.innerHTML = `<i class="fa-solid ${ICONS[type]}"></i>`;

    const body = document.createElement('div');
    body.className = 'toast-body';
    const title = document.createElement('strong');
    title.textContent = options.title || TITLES[type];
    const text = document.createElement('p');
    text.textContent = message;
    body.append(title, text);

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'toast-close';
    close.setAttribute('aria-label', 'Tutup notifikasi');
    close.innerHTML = '<i class="fa-solid fa-xmark"></i>';

    el.append(icon, body, close);

    let bar = null;
    if (duration > 0) {
      bar = document.createElement('span');
      bar.className = 'toast-progress';
      bar.style.animationDuration = `${duration}ms`;
      el.appendChild(bar);
    }

    let timer = null;
    function dismiss() {
      clearTimeout(timer);
      if (!el.isConnected || el.classList.contains('is-leaving')) return;
      el.classList.add('is-leaving');
      const remove = () => el.remove();
      el.addEventListener('animationend', remove, { once: true });
      setTimeout(remove, 400);
    }
    close.addEventListener('click', dismiss);

    if (duration > 0) {
      let remaining = duration;
      let startedAt = Date.now();
      const start = () => { startedAt = Date.now(); timer = setTimeout(dismiss, remaining); };
      el.addEventListener('mouseenter', () => {
        clearTimeout(timer);
        remaining -= Date.now() - startedAt;
        if (bar) bar.style.animationPlayState = 'paused';
      });
      el.addEventListener('mouseleave', () => {
        if (bar) bar.style.animationPlayState = 'running';
        start();
      });
      start();
    }

    getStack().appendChild(el);
    return { dismiss };
  }

  // ---------- Dialog ----------
  function openDialog({ title, message, confirmText, cancelText, tone, icon, showCancel }) {
    return new Promise((resolve) => {
      const previouslyFocused = document.activeElement;

      const overlay = document.createElement('div');
      overlay.className = 'ui-dialog-overlay';

      const dialog = document.createElement('div');
      dialog.className = `ui-dialog ui-dialog--${tone}`;
      dialog.setAttribute('role', showCancel ? 'alertdialog' : 'dialog');
      dialog.setAttribute('aria-modal', 'true');

      const iconEl = document.createElement('span');
      iconEl.className = 'ui-dialog-icon';
      iconEl.innerHTML = `<i class="fa-solid ${icon}"></i>`;

      const titleEl = document.createElement('h3');
      titleEl.textContent = title;
      titleEl.id = `ui-dialog-title-${Date.now()}`;
      dialog.setAttribute('aria-labelledby', titleEl.id);

      const msgEl = document.createElement('p');
      msgEl.textContent = message;

      const actions = document.createElement('div');
      actions.className = 'ui-dialog-actions';

      const cancelBtn = document.createElement('button');
      cancelBtn.type = 'button';
      cancelBtn.className = 'btn btn-outline';
      cancelBtn.textContent = cancelText;

      const okBtn = document.createElement('button');
      okBtn.type = 'button';
      okBtn.className = `btn ${tone === 'danger' ? 'btn-danger' : 'btn-primary'}`;
      okBtn.textContent = confirmText;

      if (showCancel) actions.appendChild(cancelBtn);
      actions.appendChild(okBtn);
      dialog.append(iconEl, titleEl, msgEl, actions);
      overlay.appendChild(dialog);
      document.body.appendChild(overlay);
      document.body.classList.add('dialog-open');

      function finish(result) {
        document.removeEventListener('keydown', onKey, true);
        overlay.classList.add('is-leaving');
        document.body.classList.remove('dialog-open');
        setTimeout(() => overlay.remove(), 160);
        if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus({ preventScroll: true });
        resolve(result);
      }
      function onKey(e) {
        if (e.key === 'Escape') {
          e.preventDefault();
          e.stopPropagation();
          finish(false);
        } else if (e.key === 'Tab') {
          const focusable = [cancelBtn, okBtn].filter((b) => b.isConnected);
          const idx = focusable.indexOf(document.activeElement);
          e.preventDefault();
          const next = e.shiftKey ? idx - 1 : idx + 1;
          focusable[(next + focusable.length) % focusable.length].focus();
        }
      }
      document.addEventListener('keydown', onKey, true);
      overlay.addEventListener('mousedown', (e) => { if (e.target === overlay && showCancel) finish(false); });
      cancelBtn.addEventListener('click', () => finish(false));
      okBtn.addEventListener('click', () => finish(true));

      // Fokus awal ke tombol aman (Batal) untuk aksi berbahaya, agar Enter tidak menghapus tak sengaja.
      (showCancel && tone === 'danger' ? cancelBtn : okBtn).focus({ preventScroll: true });
    });
  }

  function confirmDialog(options = {}) {
    const tone = options.tone || 'primary';
    return openDialog({
      title: options.title || (tone === 'danger' ? 'Hapus data?' : 'Konfirmasi'),
      message: options.message || 'Apakah Anda yakin?',
      confirmText: options.confirmText || (tone === 'danger' ? 'Ya, Hapus' : 'Ya, Lanjutkan'),
      cancelText: options.cancelText || 'Batal',
      tone,
      icon: options.icon || (tone === 'danger' ? 'fa-trash-can' : 'fa-circle-question'),
      showCancel: true,
    });
  }

  function alertDialog(message, options = {}) {
    const type = normalizeType(options.type || 'warning');
    return openDialog({
      title: options.title || TITLES[type],
      message,
      confirmText: options.confirmText || 'Mengerti',
      cancelText: '',
      tone: type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'primary',
      icon: ICONS[type],
      showCancel: false,
    });
  }

  window.AdminUI = { toast, confirm: confirmDialog, alert: alertDialog };

  // ---------- Form dengan data-confirm ----------
  document.addEventListener('submit', async (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement) || !form.dataset.confirm || form.dataset.confirmed === '1') return;
    e.preventDefault();
    const ok = await confirmDialog({
      title: form.dataset.confirmTitle,
      message: form.dataset.confirm,
      confirmText: form.dataset.confirmOk,
      tone: form.dataset.confirmTone || 'danger',
    });
    if (!ok) return;
    form.dataset.confirmed = '1';
    if (e.submitter && e.submitter.name) {
      // Pertahankan nilai tombol submit (jika ada) saat kirim manual.
      const hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = e.submitter.name;
      hidden.value = e.submitter.value;
      form.appendChild(hidden);
    }
    form.submit();
  });

  // ---------- Flash message server -> toast ----------
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.flash-container');
    if (!container) return;
    container.querySelectorAll('.flash').forEach((flash, i) => {
      const type = flash.classList.contains('flash-error') ? 'error'
        : flash.classList.contains('flash-warning') ? 'warning'
        : flash.classList.contains('flash-success') ? 'success' : 'info';
      setTimeout(() => toast(type, flash.textContent.trim()), i * 120);
    });
    container.remove();
  });
})();
