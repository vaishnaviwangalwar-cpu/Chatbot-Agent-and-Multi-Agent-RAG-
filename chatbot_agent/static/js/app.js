document.addEventListener('DOMContentLoaded', () => {
  const newSessionBtn = document.getElementById('newSessionBtn');
  const recentSessionsList = document.getElementById('recentSessionsList');
  const promptStyleSelect = document.getElementById('promptStyleSelect');
  const streamingToggle = document.getElementById('streamingToggle');
  const clearMemoryBtn = document.getElementById('clearMemoryBtn');
  const messagesContainer = document.getElementById('messagesContainer');
  const typingIndicator = document.getElementById('typingIndicator');
  const chatForm = document.getElementById('chatForm');
  const userInput = document.getElementById('userInput');
  const activeSessionTitle = document.getElementById('activeSessionTitle');
  const turnCounter = document.getElementById('turnCounter');

  // SVG Icons
  const userSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 4-4H8a4 4 0 0 4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
  const assistantSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"></path></svg>`;
  const chatIconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;

  // Restore active session ID from localStorage or default to student_session_1
  let currentSessionId = localStorage.getItem('active_session_id') || 'student_session_1';

  // Set active session & update header/localStorage
  function setActiveSession(sessionId) {
    currentSessionId = sessionId;
    localStorage.setItem('active_session_id', sessionId);
    activeSessionTitle.textContent = `Session: ${sessionId}`;
    fetchRecentSessions();
    loadSessionHistory(sessionId);
  }

  // Fetch recent sessions list from backend
  async function fetchRecentSessions() {
    try {
      const res = await fetch('/api/sessions');
      if (res.ok) {
        let sessions = await res.json();
        
        // Guarantee currentSessionId is present in list for UI selection
        const exists = sessions.some(s => s.session_id === currentSessionId);
        if (!exists) {
          sessions.unshift({ session_id: currentSessionId, message_count: 0, max_turns: 10 });
        }

        renderRecentSessions(sessions);
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  }

  // Render recent sessions list in sidebar
  function renderRecentSessions(sessions) {
    recentSessionsList.innerHTML = '';
    sessions.forEach(s => {
      const item = document.createElement('div');
      item.className = `session-item ${s.session_id === currentSessionId ? 'active' : ''}`;
      
      const turnsText = s.message_count > 0 ? `${Math.floor(s.message_count / 2)} turns` : 'New';

      item.innerHTML = `
        <div class="session-title">
          ${chatIconSvg}
          <span>${escapeHtml(s.session_id)}</span>
        </div>
        <span class="session-count">${turnsText}</span>
      `;

      item.addEventListener('click', () => {
        if (currentSessionId !== s.session_id) {
          setActiveSession(s.session_id);
        }
      });

      recentSessionsList.appendChild(item);
    });
  }

  // Load session history from backend
  async function loadSessionHistory(sessionId) {
    try {
      const res = await fetch(`/api/chat/${encodeURIComponent(sessionId)}`);
      if (res.ok) {
        const data = await res.json();
        clearMessagesUI();
        if (data.turns && data.turns.length > 0) {
          data.turns.forEach(turn => {
            appendMessage(turn.role === 'user' ? 'user' : 'assistant', turn.text);
          });
          turnCounter.textContent = `Turns: ${Math.floor(data.turn_count / 2)} / 10`;
        } else {
          appendWelcomeMessage();
          turnCounter.textContent = 'Turns: 0 / 10';
        }
      }
    } catch (err) {
      console.error('Error loading session history:', err);
    }
  }

  // + New Chat button handler (ChatGPT / Gemini style)
  newSessionBtn.addEventListener('click', () => {
    const randomId = 'session_' + Math.floor(1000 + Math.random() * 9000);
    setActiveSession(randomId);
    appendSystemNotice(`Created new session: ${randomId}`);
  });

  // Suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      userInput.value = chip.getAttribute('data-msg');
      userInput.focus();
    });
  });

  // Clear session memory
  clearMemoryBtn.addEventListener('click', async () => {
    try {
      const res = await fetch(`/api/chat/${encodeURIComponent(currentSessionId)}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        clearMessagesUI();
        appendWelcomeMessage();
        appendSystemNotice(`Cleared memory for session '${currentSessionId}'`);
        turnCounter.textContent = 'Turns: 0 / 10';
        fetchRecentSessions();
      } else {
        appendSystemNotice(`Could not clear session memory`);
      }
    } catch (err) {
      console.error('Error clearing session:', err);
    }
  });

  // Send message
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    // Append user message to UI
    appendMessage('user', text);
    userInput.value = '';
    showTyping(true);

    const payload = {
      session_id: currentSessionId,
      message: text,
      prompt_style: promptStyleSelect.value
    };

    const isStreaming = streamingToggle ? streamingToggle.checked : true;

    if (isStreaming) {
      // 1. Real-Time Streaming Mode (/api/chat/stream)
      try {
        const response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        showTyping(false);

        if (!response.ok) {
          const errorData = await response.json();
          appendMessage('assistant', `Error: ${errorData.detail || 'An error occurred'}`);
          return;
        }

        const assistantBubble = createAssistantBubble();
        const textContainer = assistantBubble.querySelector('.reply-text');
        const toolContainer = assistantBubble.querySelector('.tool-container');

        let accumulatedText = '';
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split('\n\n');
          buffer = events.pop();

          for (const eventBlock of events) {
            if (!eventBlock.trim()) continue;
            
            let eventType = 'message';
            let dataStr = '';

            const lines = eventBlock.split('\n');
            for (const line of lines) {
              if (line.startsWith('event: ')) {
                eventType = line.substring(7).trim();
              } else if (line.startsWith('data: ')) {
                dataStr = line.substring(6).trim();
              }
            }

            if (dataStr) {
              const dataObj = JSON.parse(dataStr);

              if (eventType === 'token' && dataObj.text) {
                accumulatedText += dataObj.text;
                textContainer.innerHTML = escapeHtml(accumulatedText);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
              } else if (eventType === 'tool_call' && dataObj.tool_name) {
                const badge = document.createElement('div');
                badge.className = 'tool-badge';
                badge.innerHTML = `<span>Tool Executed:</span> <strong>${dataObj.tool_name}()</strong>`;
                toolContainer.appendChild(badge);
              } else if (eventType === 'done' && dataObj.turn_count) {
                turnCounter.textContent = `Turns: ${Math.floor(dataObj.turn_count / 2)} / 10`;
                fetchRecentSessions();
              }
            }
          }
        }

      } catch (err) {
        showTyping(false);
        appendMessage('assistant', `Network Error: Could not connect to API server.`);
        console.error(err);
      }
    } else {
      // 2. Standard Non-Streaming Mode (/api/chat)
      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        showTyping(false);

        if (!response.ok) {
          const errorData = await response.json();
          appendMessage('assistant', `Error: ${errorData.detail || 'An error occurred'}`);
          return;
        }

        const data = await response.json();
        appendMessage('assistant', data.reply, data.tools_used);
        turnCounter.textContent = `Turns: ${Math.floor(data.turn_count / 2)} / 10`;
        fetchRecentSessions();

      } catch (err) {
        showTyping(false);
        appendMessage('assistant', `Network Error: Could not connect to API server.`);
        console.error(err);
      }
    }
  });

  // Helper: Append Welcome Message
  function appendWelcomeMessage() {
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'message assistant';
    welcomeDiv.innerHTML = `
      <div class="avatar assistant-avatar">${assistantSvg}</div>
      <div class="message-content">
        <div class="sender-name">Campus Assistant</div>
        <p>Welcome! I am your DY Patil University AI Support Agent. You can ask about course schedules, library hours, hostel fees, campus shuttles, or student services.</p>
        <div class="capabilities-pills">
          <span class="pill">Session Memory</span>
          <span class="pill">Python Tool Execution</span>
          <span class="pill">Prompt Architecture</span>
        </div>
      </div>
    `;
    messagesContainer.appendChild(welcomeDiv);
  }

  // Helper: Create Assistant message bubble for streaming
  function createAssistantBubble() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';
    msgDiv.innerHTML = `
      <div class="avatar assistant-avatar">${assistantSvg}</div>
      <div class="message-content">
        <div class="sender-name">Campus Assistant</div>
        <p class="reply-text"></p>
        <div class="tool-container"></div>
      </div>
    `;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
  }

  // Helper: Append static message bubble
  function appendMessage(sender, text, toolsUsed = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;

    const avatarSvg = sender === 'user' ? userSvg : assistantSvg;
    const avatarClass = sender === 'user' ? 'user-avatar' : 'assistant-avatar';
    const senderTitle = sender === 'user' ? 'You' : 'Campus Assistant';

    let toolsHtml = '';
    if (toolsUsed && toolsUsed.length > 0) {
      toolsHtml = toolsUsed.map(t => `
        <div class="tool-badge">
          <span>Tool Executed:</span> <strong>${t.tool_name}()</strong>
        </div>
      `).join('');
    }

    msgDiv.innerHTML = `
      <div class="avatar ${avatarClass}">${avatarSvg}</div>
      <div class="message-content">
        <div class="sender-name">${senderTitle}</div>
        <p class="reply-text">${escapeHtml(text)}</p>
        <div class="tool-container">${toolsHtml}</div>
      </div>
    `;

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendSystemNotice(text) {
    const noticeDiv = document.createElement('div');
    noticeDiv.style.textAlign = 'center';
    noticeDiv.style.fontSize = '11px';
    noticeDiv.style.color = 'var(--text-subtle)';
    noticeDiv.style.margin = '8px 0';
    noticeDiv.textContent = `— ${text} —`;
    messagesContainer.appendChild(noticeDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function clearMessagesUI() {
    messagesContainer.innerHTML = '';
  }

  function showTyping(visible) {
    if (visible) {
      typingIndicator.classList.remove('hidden');
    } else {
      typingIndicator.classList.add('hidden');
    }
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

  // Initial setup: activate stored session
  setActiveSession(currentSessionId);
});
