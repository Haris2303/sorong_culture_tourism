(function () {
  const section = document.getElementById('rating-section');
  if (!section) return;

  const wisataId = section.dataset.wisataId;
  const starInput = document.getElementById('star-input');
  const stars = starInput.querySelectorAll('.star');
  const komentarEl = document.getElementById('rating-komentar');
  const form = document.getElementById('rating-form');
  const submitBtn = document.getElementById('rating-submit-btn');
  const feedbackEl = document.getElementById('rating-feedback');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

  const storageKey = `rated_wisata_${wisataId}`;
  let selectedScore = 0;

  // Tambahkan ulasan baru ke daftar (tanpa reload) begitu server membalas
  // rating yang langsung "approved". Dibangun lewat DOM API (bukan innerHTML)
  // supaya komentar pengguna otomatis di-escape, sama seperti autoescape Jinja.
  function prependReview(review) {
    const list = document.getElementById('review-items');
    if (!list) return;

    const emptyState = document.getElementById('review-empty-state');
    if (emptyState) emptyState.remove();

    const item = document.createElement('div');
    item.className = 'review-item';

    const starsWrap = document.createElement('div');
    starsWrap.className = 'review-stars';
    for (let i = 0; i < review.skor_bintang; i++) {
      const icon = document.createElement('i');
      icon.className = 'fa-solid fa-star';
      starsWrap.appendChild(icon);
    }
    item.appendChild(starsWrap);

    if (review.komentar) {
      const p = document.createElement('p');
      p.textContent = review.komentar;
      item.appendChild(p);
    }

    const dateEl = document.createElement('span');
    dateEl.className = 'review-date';
    dateEl.textContent = review.created_at;
    item.appendChild(dateEl);

    list.insertBefore(item, list.firstChild);
  }

  function updateRatingSummary(summary) {
    const avgEl = document.getElementById('rating-summary-average');
    const countEl = document.getElementById('rating-summary-count');
    if (avgEl) avgEl.textContent = summary.average;
    if (countEl) countEl.textContent = summary.count;
  }

  function lockForm(message) {
    // Input dihapus dari tampilan (bukan cuma dinonaktifkan) supaya pengunjung
    // yang sudah memberi ulasan tidak melihat form abu-abu yang tidak bisa dipakai.
    starInput.style.display = 'none';
    komentarEl.style.display = 'none';
    submitBtn.style.display = 'none';
    feedbackEl.textContent = '';
    const icon = document.createElement('i');
    icon.className = 'fa-solid fa-circle-check';
    feedbackEl.appendChild(icon);
    feedbackEl.append(' ' + message);
    feedbackEl.className = 'rating-feedback rating-locked';
  }

  // Layer 1 (Client): kunci form via localStorage jika sudah pernah rating.
  if (localStorage.getItem(storageKey)) {
    lockForm('Anda sudah pernah memberi ulasan untuk destinasi ini.');
    return;
  }

  stars.forEach((star) => {
    star.addEventListener('click', () => {
      selectedScore = parseInt(star.dataset.value, 10);
      stars.forEach((s) => {
        const value = parseInt(s.dataset.value, 10);
        s.classList.toggle('active', value <= selectedScore);
        s.setAttribute('aria-pressed', String(value === selectedScore));
      });
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (selectedScore < 1 || selectedScore > 5) {
      feedbackEl.textContent = 'Silakan pilih skor bintang terlebih dahulu.';
      feedbackEl.className = 'rating-feedback rating-error';
      return;
    }

    submitBtn.disabled = true;
    feedbackEl.textContent = 'Mengirim ulasan...';
    feedbackEl.className = 'rating-feedback';

    try {
      const res = await fetch('/api/rating', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          wisata_id: parseInt(wisataId, 10),
          skor_bintang: selectedScore,
          komentar: komentarEl.value.trim(),
        }),
      });
      const data = await res.json();

      if (res.status === 201) {
        localStorage.setItem(storageKey, '1');
        lockForm(data.message || 'Terima kasih atas ulasan Anda!');
        // Ulasan "pending" (kena filter kata kasar) belum tampil ke publik,
        // jadi cuma tambahkan ke daftar kalau server balas status "approved".
        if (data.status === 'approved' && data.review && data.summary) {
          prependReview(data.review);
          updateRatingSummary(data.summary);
        }
      } else if (res.status === 429) {
        feedbackEl.textContent = 'Terlalu banyak percobaan. Silakan coba lagi dalam 1 jam.';
        feedbackEl.className = 'rating-feedback rating-error';
        submitBtn.disabled = false;
      } else if (res.status === 409) {
        localStorage.setItem(storageKey, '1');
        lockForm(data.error);
      } else {
        feedbackEl.textContent = data.error || 'Gagal mengirim ulasan.';
        feedbackEl.className = 'rating-feedback rating-error';
        submitBtn.disabled = false;
      }
    } catch (err) {
      feedbackEl.textContent = 'Tidak dapat terhubung ke server.';
      feedbackEl.className = 'rating-feedback rating-error';
      submitBtn.disabled = false;
    }
  });
})();
