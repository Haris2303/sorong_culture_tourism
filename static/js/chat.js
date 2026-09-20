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

  toggleBtn.addEventListener('click', () => {
    widget.classList.toggle('closed');
    if (!widget.classList.contains('closed')) {
      input.focus();
    }
  });

  closeBtn.addEventListener('click', () => {
    widget.classList.add('closed');
  });

  document.querySelectorAll('#chat-quick-replies .chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      input.value = chip.dataset.prompt || chip.textContent.trim();
      form.requestSubmit();
    });
  });

  function appendMessage(text, sender) {
    const wrapper = document.createElement('div');
    wrapper.className = `chat-message ${sender}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
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
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      hideTypingBubble();

      if (res.ok) {
        appendMessage(data.answer, 'bot');
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
