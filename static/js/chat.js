(function () {
  const widget = document.getElementById('chat-widget');
  const toggleBtn = document.getElementById('chat-toggle-btn');
  const closeBtn = document.getElementById('chat-close-btn');
  const messagesEl = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const quickReplies = document.getElementById('chat-quick-replies');
  const unreadBadge = document.getElementById('chat-unread-badge');

  if (!widget) return;

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const prefersReducedMotion =
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Riwayat & status buka/tutup disimpan di sessionStorage supaya tidak hilang
  // saat pengguna berpindah halaman (situs ini multi-halaman, tiap navigasi
  // memuat ulang JS dari nol). sessionStorage otomatis bersih saat tab ditutup.
  const HISTORY_KEY = 'sorongRayaChatHistory';
  const OPEN_STATE_KEY = 'sorongRayaChatOpen';
  const SCROLL_KEY = 'sorongRayaChatScroll';
  // job_id jawaban yang masih diproses server (lihat catatan di bagian polling
  // di bawah) — disimpan terpisah dari riwayat supaya bisa dilanjutkan dari
  // halaman manapun, bukan cuma dipulihkan saat kembali ke halaman yang sama.
  const PENDING_JOB_KEY = 'sorongRayaChatPendingJob';

  function loadHistory() {
    try {
      const raw = sessionStorage.getItem(HISTORY_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (err) {
      return [];
    }
  }

  function saveHistory() {
    try {
      sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (err) {
      // sessionStorage penuh/diblokir (mis. mode privat) — chat tetap berfungsi, hanya tidak persist.
    }
  }

  let history = loadHistory();

  // Posisi scroll disimpan terpisah dari riwayat supaya saat pindah halaman (situs
  // ini multi-halaman) chat tidak selalu lompat ke pesan paling awal. Elemen dengan
  // display:none (kondisi panel saat masih tertutup) selalu melaporkan scrollTop/
  // scrollHeight sebagai 0, jadi posisi scroll HANYA bisa diterapkan setelah panel
  // benar-benar terlihat — lihat pemanggilan restoreScrollPosition() di bawah.
  function loadScrollPosition() {
    try {
      const raw = sessionStorage.getItem(SCROLL_KEY);
      return raw === null ? null : Number(raw);
    } catch (err) {
      return null;
    }
  }

  function saveScrollPosition() {
    try {
      sessionStorage.setItem(SCROLL_KEY, String(messagesEl.scrollTop));
    } catch (err) {
      // abaikan jika sessionStorage tidak tersedia
    }
  }

  function restoreScrollPosition() {
    const saved = loadScrollPosition();
    messagesEl.scrollTop = saved === null ? messagesEl.scrollHeight : saved;
  }

  let scrollSaveQueued = false;
  messagesEl.addEventListener('scroll', () => {
    if (scrollSaveQueued) return;
    scrollSaveQueued = true;
    requestAnimationFrame(() => {
      saveScrollPosition();
      scrollSaveQueued = false;
    });
  });

  // Mengetik ulang HTML jawaban bot tanpa merusak tag: struktur DOM final
  // dibangun sekaligus (link & formatting langsung valid), lalu tiap text
  // node-nya dikosongkan dan diisi berangsur dari node pertama ke terakhir.
  // Durasi total dibatasi (bukan kecepatan per-karakter tetap) supaya jawaban
  // panjang tidak butuh waktu lama untuk selesai tampil — ini murni animasi
  // tampilan setelah jawaban lengkap diterima, jadi tidak menunda respons.
  function typeIntoBubble(bubble, text, isHtml, onDone) {
    const template = document.createElement('template');
    if (isHtml) {
      // Aman: HTML ini dirender & di-escape di server (core/rag_engine.py _render_rich_answer),
      // hanya berisi tag terbatas (p/ul/ol/li/strong), bukan HTML mentah dari input pengguna.
      template.innerHTML = text;
    } else {
      template.content.appendChild(document.createTextNode(text));
    }

    const textQueue = [];
    function cloneEmpty(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        const liveNode = document.createTextNode('');
        textQueue.push({ node: liveNode, full: node.textContent });
        return liveNode;
      }
      const clone = node.cloneNode(false);
      node.childNodes.forEach((child) => clone.appendChild(cloneEmpty(child)));
      return clone;
    }

    const liveFragment = document.createDocumentFragment();
    template.content.childNodes.forEach((child) => liveFragment.appendChild(cloneEmpty(child)));
    bubble.appendChild(liveFragment);

    const totalChars = textQueue.reduce((sum, item) => sum + item.full.length, 0);
    if (totalChars === 0) {
      onDone();
      return;
    }

    const TARGET_DURATION_MS = 700;
    const FRAME_MS = 16;
    const targetFrames = Math.max(1, Math.round(TARGET_DURATION_MS / FRAME_MS));
    const charsPerTick = Math.max(2, Math.ceil(totalChars / targetFrames));

    let qi = 0;
    let ci = 0;

    function tick() {
      let remaining = charsPerTick;
      while (remaining > 0 && qi < textQueue.length) {
        const item = textQueue[qi];
        const take = Math.min(remaining, item.full.length - ci);
        item.node.textContent += item.full.slice(ci, ci + take);
        ci += take;
        remaining -= take;
        if (ci >= item.full.length) {
          qi += 1;
          ci = 0;
        }
      }
      messagesEl.scrollTop = messagesEl.scrollHeight;
      if (qi < textQueue.length) {
        requestAnimationFrame(tick);
      } else {
        onDone();
      }
    }
    requestAnimationFrame(tick);
  }

  function renderMessage(text, sender, sources, isHtml, options) {
    const animate = !!(options && options.animate);
    const wrapper = document.createElement('div');
    wrapper.className = `chat-message ${sender}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);

    const links = (sources || []).filter((s) => s && s.url);
    function appendSources() {
      if (!links.length) return;
      const linksEl = document.createElement('div');
      linksEl.className = 'chat-sources';
      links.forEach((s) => {
        const a = document.createElement('a');
        a.href = s.url;
        a.textContent = `📍 ${s.title}`;
        a.className = 'chat-source-link';
        linksEl.appendChild(a);
      });
      wrapper.appendChild(linksEl);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    if (animate && sender === 'bot' && !prefersReducedMotion) {
      bubble.classList.add('is-typing');
      typeIntoBubble(bubble, text, isHtml, () => {
        bubble.classList.remove('is-typing');
        appendSources();
      });
    } else {
      if (isHtml) {
        bubble.innerHTML = text;
      } else {
        bubble.textContent = text;
      }
      appendSources();
    }

    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendMessage(text, sender, sources, isHtml, options) {
    renderMessage(text, sender, sources, isHtml, options);
    history.push({ text, sender, sources: sources || [], isHtml: !!isHtml });
    saveHistory();
  }

  if (history.length) {
    // Ganti bubble sambutan bawaan dengan riwayat percakapan sebelumnya.
    messagesEl.innerHTML = '';
    history.forEach((msg) => renderMessage(msg.text, msg.sender, msg.sources, msg.isHtml));
  } else {
    // Kunjungan pertama di tab ini: simpan bubble sambutan bawaan sebagai riwayat awal.
    const welcomeBubble = messagesEl.querySelector('.bubble');
    if (welcomeBubble) {
      history.push({ text: welcomeBubble.textContent, sender: 'bot', sources: [], isHtml: false });
      saveHistory();
    }
  }

  // Saran pertanyaan cepat cuma berguna sebelum obrolan dimulai — begitu pengguna
  // sudah mengirim pertanyaan apa pun (lewat chip ataupun ketik manual), baris ini
  // disembunyikan permanen untuk sesi tab ini supaya tidak menumpuk di setiap pesan.
  function hideQuickReplies() {
    if (quickReplies) quickReplies.hidden = true;
  }
  if (history.length > 1) hideQuickReplies();

  try {
    if (sessionStorage.getItem(OPEN_STATE_KEY) === 'true') {
      widget.classList.remove('closed');
      restoreScrollPosition();
    }
  } catch (err) {
    // abaikan jika sessionStorage tidak tersedia
  }

  function persistOpenState() {
    try {
      sessionStorage.setItem(OPEN_STATE_KEY, (!widget.classList.contains('closed')).toString());
    } catch (err) {
      // abaikan jika sessionStorage tidak tersedia
    }
  }

  toggleBtn.addEventListener('click', () => {
    widget.classList.toggle('closed');
    persistOpenState();
    if (!widget.classList.contains('closed')) {
      if (unreadBadge) unreadBadge.hidden = true;
      restoreScrollPosition();
      input.focus();
    }
  });

  function closeWidget() {
    widget.classList.add('closed');
    persistOpenState();
  }

  closeBtn.addEventListener('click', closeWidget);

  // Panel chat berlaku seperti dialog, jadi harus bisa ditutup lewat Escape
  // sama seperti modal admin (lihat static/js/admin.js).
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !widget.classList.contains('closed')) {
      closeWidget();
      toggleBtn.focus();
    }
  });

  document.querySelectorAll('#chat-quick-replies .chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      input.value = chip.dataset.prompt || chip.textContent.trim();
      form.requestSubmit();
    });
  });

  // Beberapa giliran terakhir dikirim ke server tiap request supaya chatbot paham
  // pertanyaan lanjutan ("berapa tiketnya?") tanpa pengguna mengulang nama tempatnya.
  // Jawaban bot disimpan sebagai HTML, jadi tag-nya dilucuti dulu jadi teks polos.
  const HISTORY_TURNS_SENT = 6;

  function toPlainText(msg) {
    if (!msg.isHtml) return msg.text || '';
    const tmp = document.createElement('div');
    tmp.innerHTML = msg.text || '';
    return (tmp.textContent || '').trim();
  }

  function historyPayload() {
    return history
      .slice(-HISTORY_TURNS_SENT)
      .map((msg) => ({
        role: msg.sender === 'user' ? 'user' : 'bot',
        text: toPlainText(msg).slice(0, 600),
      }))
      .filter((msg) => msg.text);
  }

  function showTypingBubble() {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message bot';
    wrapper.id = 'chat-typing-bubble';
    const bubble = document.createElement('div');
    bubble.className = 'bubble typing-bubble';
    bubble.innerHTML = '<span></span><span></span><span></span>';
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideTypingBubble() {
    document.getElementById('chat-typing-bubble')?.remove();
  }

  // --- Job jawaban di background (lihat core/chat_jobs.py) -----------------
  // /api/chat cuma memulai job & langsung membalas job_id (tidak menunggu LLM
  // selesai), supaya request-nya sendiri tidak sempat terputus saat pengguna
  // pindah halaman. job_id disimpan di sessionStorage; begitu ada halaman baru
  // dimuat, polling dilanjutkan dari situ — jawabannya tetap sampai walau
  // pengguna sudah berpindah beberapa kali sebelum LLM selesai memproses.
  const JOB_POLL_INTERVAL_MS = 1200;

  function savePendingJob(jobId) {
    try {
      sessionStorage.setItem(PENDING_JOB_KEY, jobId);
    } catch (err) {
      // abaikan jika sessionStorage tidak tersedia
    }
  }

  function loadPendingJob() {
    try {
      return sessionStorage.getItem(PENDING_JOB_KEY);
    } catch (err) {
      return null;
    }
  }

  function clearPendingJob() {
    try {
      sessionStorage.removeItem(PENDING_JOB_KEY);
    } catch (err) {
      // abaikan jika sessionStorage tidak tersedia
    }
  }

  function pollJob(jobId) {
    return new Promise((resolve) => {
      async function tick() {
        try {
          const res = await fetch(`/api/chat/status/${jobId}`);
          if (res.status === 404) {
            resolve({
              answer: 'Maaf, sesi jawaban sebelumnya sudah kedaluwarsa. Silakan tanyakan kembali.',
              sources: [],
            });
            return;
          }
          const data = await res.json();
          if (data.status === 'done') {
            resolve(data.result);
            return;
          }
        } catch (err) {
          // gangguan jaringan sesaat — coba lagi di tick berikutnya, jangan menyerah.
        }
        setTimeout(tick, JOB_POLL_INTERVAL_MS);
      }
      tick();
    });
  }

  function showUnreadBadge() {
    if (widget.classList.contains('closed') && unreadBadge) {
      unreadBadge.hidden = false;
    }
  }

  async function resolveJob(jobId) {
    sendBtn.disabled = true;
    showTypingBubble();
    const result = await pollJob(jobId);
    clearPendingJob();
    hideTypingBubble();
    appendMessage(result.answer, 'bot', result.sources, true, { animate: true });
    sendBtn.disabled = false;
    showUnreadBadge();
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    // Diambil sebelum pesan ini masuk riwayat, supaya tidak terkirim dua kali.
    const previousTurns = historyPayload();

    appendMessage(message, 'user');
    hideQuickReplies();
    input.value = '';
    sendBtn.disabled = true;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ message, history: previousTurns }),
      });
      if (!res.ok) throw new Error('Gagal memulai permintaan jawaban.');
      const data = await res.json();
      savePendingJob(data.job_id);
      await resolveJob(data.job_id);
    } catch (err) {
      clearPendingJob();
      sendBtn.disabled = false;
      appendMessage('Tidak dapat terhubung ke server. Periksa koneksi Anda.', 'bot', null, false, {
        animate: true,
      });
    } finally {
      input.focus();
    }
  });

  // Kalau ada job yang belum selesai saat halaman ini dimuat (mis. pengguna
  // bertanya di halaman lain lalu berpindah ke sini sebelum jawabannya
  // datang), lanjutkan polling-nya di sini alih-alih membiarkannya hilang.
  const pendingJobId = loadPendingJob();
  if (pendingJobId) {
    resolveJob(pendingJobId);
  }
})();
