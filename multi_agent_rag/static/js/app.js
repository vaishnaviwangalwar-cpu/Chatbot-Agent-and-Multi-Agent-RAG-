document.addEventListener('DOMContentLoaded', () => {
  const sourcesList = document.getElementById('sourcesList');
  const topKSlider = document.getElementById('topKSlider');
  const topKValue = document.getElementById('topKValue');
  const reingestBtn = document.getElementById('reingestBtn');
  const healthCount = document.getElementById('healthCount');
  
  const messagesContainer = document.getElementById('messagesContainer');
  const welcomeCard = document.getElementById('welcomeCard');
  const typingIndicator = document.getElementById('typingIndicator');
  
  const chatForm = document.getElementById('chatForm');
  const userInput = document.getElementById('userInput');
  const uploadTriggerBtn = document.getElementById('uploadTriggerBtn');
  const docUploadInput = document.getElementById('docUploadInput');

  // ─── Toast Notification System ───────────────────────────────────────────
  function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icon = type === 'success'
      ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`
      : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;

    toast.innerHTML = `<span class="toast-icon">${icon}</span><span class="toast-msg">${escapeHtml(message)}</span>`;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => toast.classList.add('toast-visible'));

    // Auto-dismiss after 3.5s
    setTimeout(() => {
      toast.classList.remove('toast-visible');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ─── File Upload ──────────────────────────────────────────────────────────
  uploadTriggerBtn.addEventListener('click', () => docUploadInput.click());

  docUploadInput.addEventListener('change', async () => {
    const file = docUploadInput.files[0];
    if (!file) return;

    const allowedExtensions = ['.txt', '.pdf', '.png', '.jpg', '.jpeg'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
      showToast('Only TXT, PDF, PNG, and JPG files are supported.', 'error');
      docUploadInput.value = '';
      return;
    }

    uploadTriggerBtn.disabled = true;
    uploadTriggerBtn.querySelector('span').textContent = 'Uploading & indexing...';

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/rag/upload', { method: 'POST', body: formData });
      if (res.ok) {
        showToast(`Indexed: ${file.name}`, 'success');
        updateSystemStatus();
        loadSourceDocuments();
      } else {
        const err = await res.json();
        showToast(`Upload failed: ${err.detail || 'Server error'}`, 'error');
      }
    } catch (err) {
      showToast('Upload failed: Could not connect to server.', 'error');
    } finally {
      uploadTriggerBtn.disabled = false;
      uploadTriggerBtn.querySelector('span').textContent = 'Upload TXT / PDF / Image';
      docUploadInput.value = '';
    }
  });

  // SVG Icons
  const docIconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`;
  const userSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
  const assistantSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>`;

  // ─── Server Health & Source Documents ────────────────────────────────────
  async function updateSystemStatus() {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        healthCount.textContent = `${data.chunk_count} policy chunks indexed`;
      }
    } catch (err) {
      healthCount.textContent = 'Server disconnected';
      console.error(err);
    }
  }

  async function loadSourceDocuments() {
    try {
      const res = await fetch('/api/rag/sources');
      if (res.ok) {
        const files = await res.json();
        sourcesList.innerHTML = '';
        if (files.length === 0) {
          sourcesList.innerHTML = '<div class="source-loading">No documents found.</div>';
          return;
        }
        files.forEach(file => {
          const item = document.createElement('div');
          item.className = 'source-item';
          item.innerHTML = `${docIconSvg}<span>${escapeHtml(file)}</span>`;
          sourcesList.appendChild(item);
        });
      }
    } catch (err) {
      sourcesList.innerHTML = '<div class="source-loading">Failed to load sources.</div>';
      console.error(err);
    }
  }

  // ─── Re-index / Rebuild ───────────────────────────────────────────────────
  reingestBtn.addEventListener('click', async () => {
    reingestBtn.disabled = true;
    reingestBtn.querySelector('span').textContent = 'Rebuilding index...';
    try {
      const res = await fetch('/api/rag/ingest', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        showToast(`Re-indexed ${data.document_count} docs → ${data.chunk_count} chunks`, 'success');
        updateSystemStatus();
        loadSourceDocuments();
      } else {
        showToast('Ingestion failed. Check sample_docs/ folder.', 'error');
      }
    } catch (err) {
      showToast('Error: Could not connect to API.', 'error');
      console.error(err);
    } finally {
      reingestBtn.disabled = false;
      reingestBtn.querySelector('span').textContent = 'Rebuild Vector Index';
    }
  });

  // ─── Slider ───────────────────────────────────────────────────────────────
  topKSlider.addEventListener('input', (e) => {
    topKValue.textContent = e.target.value;
  });

  // ─── Suggestion Chips ─────────────────────────────────────────────────────
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      userInput.value = chip.getAttribute('data-msg');
      userInput.focus();
    });
  });

  // ─── Query Submission ─────────────────────────────────────────────────────
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    if (welcomeCard) welcomeCard.remove();

    appendMessage('user', query);
    userInput.value = '';
    showTyping(true);

    const payload = { question: query, top_k: parseInt(topKSlider.value) };

    try {
      const res = await fetch('/api/rag/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      showTyping(false);

      if (!res.ok) {
        appendMessage('assistant', 'Error: Failed to retrieve answer.');
        return;
      }

      const data = await res.json();
      appendMessage('assistant', data.answer, data.sources, data.retrieved_chunks);
    } catch (err) {
      showTyping(false);
      appendMessage('assistant', 'Network Error: Could not connect to API server.');
      console.error(err);
    }
  });

  // ─── Message Rendering ────────────────────────────────────────────────────
  function appendMessage(sender, text, sources = [], chunks = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;

    const avatarSvg = sender === 'user' ? userSvg : assistantSvg;
    const avatarClass = sender === 'user' ? 'user-avatar' : 'assistant-avatar';
    const senderTitle = sender === 'user' ? 'You' : 'Campus Assistant';

    msgDiv.innerHTML = `
      <div class="avatar ${avatarClass}">${avatarSvg}</div>
      <div class="message-content">
        <div class="sender-name">${senderTitle}</div>
        <p class="reply-text">${escapeHtml(text)}</p>
      </div>
    `;

    const contentContainer = msgDiv.querySelector('.message-content');
    
    if (sender === 'assistant' && sources.length > 0) {
      appendCitationsAndInspector(contentContainer, sources, chunks);
    }

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendCitationsAndInspector(container, sources, chunks) {
    // Citation pills
    const citationBox = document.createElement('div');
    citationBox.className = 'citations-box';
    sources.forEach(src => {
      const pill = document.createElement('span');
      pill.className = 'citation-badge';
      pill.innerHTML = `${docIconSvg}<span>${escapeHtml(src)}</span>`;
      citationBox.appendChild(pill);
    });
    container.appendChild(citationBox);

    // Collapsible chunk inspector
    if (chunks && chunks.length > 0) {
      const inspector = document.createElement('div');
      inspector.className = 'context-inspector';
      inspector.innerHTML = `
        <div class="inspector-toggle">
          <span>View Retrieved Policy Chunks</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </div>
        <div class="inspector-content"></div>
      `;

      const contentBox = inspector.querySelector('.inspector-content');
      chunks.forEach((chunk, index) => {
        const item = document.createElement('div');
        item.className = 'context-chunk';
        const scoreText = chunk.score !== null ? ` | Relevance Distance: ${chunk.score.toFixed(4)}` : '';
        item.innerHTML = `
          <div class="context-chunk-source">Chunk #${index + 1} from ${escapeHtml(chunk.source)}${scoreText}</div>
          <div>${escapeHtml(chunk.text)}</div>
        `;
        contentBox.appendChild(item);
      });

      inspector.querySelector('.inspector-toggle').addEventListener('click', () => {
        inspector.classList.toggle('open');
      });

      container.appendChild(inspector);
    }
  }

  function showTyping(visible) {
    typingIndicator.classList.toggle('hidden', !visible);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;")
      .replace(/\n/g, "<br>");
  }

  // Boot
  updateSystemStatus();
  loadSourceDocuments();
});
