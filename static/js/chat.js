(function () {
  const widget = document.getElementById('chat-widget');
  const toggleBtn = document.getElementById('chat-toggle-btn');
  const closeBtn = document.getElementById('chat-close-btn');
  const messagesEl = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');

  if (!widget) return;

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

  // Riwayat & status buka/tutup disimpan di sessionStorage supaya tidak hilang
  // saat pengguna berpindah halaman (situs ini multi-halaman, tiap navigasi
  // memuat ulang JS dari nol). sessionStorage otomatis bersih saat tab ditutup.
  const HISTORY_KEY = 'sorongRayaChatHistory';
  const OPEN_STATE_KEY = 'sorongRayaChatOpen';
  const SCROLL_KEY = 'sorongRayaChatScroll';

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

  function renderMessage(text, sender, sources, isHtml) {
    const wrapper = document.createElement('div');
    wrapper.className = `chat-message ${sender}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    if (isHtml) {
      // Aman: HTML ini dirender & di-escape di server (core/rag_engine.py _render_rich_answer),
      // hanya berisi tag terbatas (p/ul/ol/li/strong), bukan HTML mentah dari input pengguna.
      bubble.innerHTML = text;
    } else {
      bubble.textContent = text;
    }
    wrapper.appendChild(bubble);

    const links = (sources || []).filter((s) => s && s.url);
    if (links.length) {
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
    }

    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendMessage(text, sender, sources, isHtml) {
    renderMessage(text, sender, sources, isHtml);
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
      restoreScrollPosition();
      input.focus();
    }
  });

  closeBtn.addEventListener('click', () => {
    widget.classList.add('closed');
    persistOpenState();
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

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    // Diambil sebelum pesan ini masuk riwayat, supaya tidak terkirim dua kali.
    const previousTurns = historyPayload();

    appendMessage(message, 'user');
    input.value = '';
    sendBtn.disabled = true;
    showTypingBubble();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ message, history: previousTurns }),
      });
      const data = await res.json();
      hideTypingBubble();

      if (res.ok) {
        appendMessage(data.answer, 'bot', data.sources, true);
      } else {
        appendMessage(data.error || 'Maaf, terjadi kesalahan. Silakan coba lagi.', 'bot');
      }
    } catch (err) {
      hideTypingBubble();
      appendMessage('Tidak dapat terhubung ke server. Periksa koneksi Anda.', 'bot');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });
})();
