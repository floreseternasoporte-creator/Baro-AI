/* ==========================================================================
   app.js — Lógica de la aplicación Baro.
   Conecta: WebSocket con el backend, Web Speech API (reconocimiento nativo
   del navegador, gratis), reproducción de audio TTS (Edge-TTS desde el
   backend), y toda la interacción de la interfaz.
   ========================================================================== */

(() => {
  'use strict';

  // ------------------------------------------------------------------ //
  // Config / estado global
  // ------------------------------------------------------------------ //

  const WS_PATH = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';

  const state = {
    ws: null,
    wsReady: false,
    recognizing: false,
    recognition: null,
    selectedVoice: 'es-US-PalomaNeural',
    audioCtx: null,
    currentAudio: null,
    voiceModeOpen: false,
    pendingAutoListen: false,
  };

  // ------------------------------------------------------------------ //
  // Referencias DOM
  // ------------------------------------------------------------------ //

  const $ = (id) => document.getElementById(id);

  const welcomeScreen = $('welcome-screen');
  const mainScreen = $('main-screen');
  const voiceOverlay = $('voice-overlay');

  const startVoiceBtn = $('start-voice-btn');
  const startChatBtn = $('start-chat-btn');
  const newChatBtn = $('new-chat-btn');

  const messagesScroll = $('messages-scroll');
  const messagesInner = $('messages-inner');
  const emptyState = $('empty-state');

  const textInput = $('text-input');
  const sendBtn = $('send-btn');
  const micBtn = $('mic-btn');

  const connDot = $('conn-dot');
  const connLabel = $('conn-label');
  const voiceSelect = $('voice-select');

  const openVoiceModeBtn = $('open-voice-mode-btn');
  const voiceMicBtn = $('voice-mic-btn');
  const voiceCloseBtn = $('voice-close-btn');
  const voiceCaption = $('voice-caption');
  const voiceStateLabel = $('voice-state-label');

  // ------------------------------------------------------------------ //
  // Orbes (instancias del orbe de partículas)
  // ------------------------------------------------------------------ //

  let welcomeOrb = null;
  let emptyOrb = null;
  let voiceOrb = null;

  function initOrbs() {
    welcomeOrb = new BaroOrb($('welcome-orb-canvas'), { colorMode: 'light', numParticles: 260, baseRadius: 0.66 });
    emptyOrb = new BaroOrb($('empty-orb-canvas'), { colorMode: 'light', numParticles: 140, baseRadius: 0.7 });
    voiceOrb = new BaroOrb($('voice-orb-canvas'), { colorMode: 'dark', numParticles: 320, baseRadius: 0.6 });
    welcomeOrb.setState('idle');
    emptyOrb.setState('idle');
    voiceOrb.setState('idle');
  }

  // ------------------------------------------------------------------ //
  // WebSocket
  // ------------------------------------------------------------------ //

  function connectWebSocket() {
    try {
      state.ws = new WebSocket(WS_PATH);
    } catch (err) {
      setConnectionStatus(false);
      return;
    }

    state.ws.onopen = () => {
      state.wsReady = true;
      setConnectionStatus(true);
    };

    state.ws.onclose = () => {
      state.wsReady = false;
      setConnectionStatus(false);
      // Reintentar conexión cada 3s
      setTimeout(connectWebSocket, 3000);
    };

    state.ws.onerror = () => {
      setConnectionStatus(false);
    };

    state.ws.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }
      handleServerMessage(payload);
    };
  }

  function setConnectionStatus(online) {
    connDot.classList.toggle('offline', !online);
    connLabel.textContent = online ? 'Baro está activa' : 'Reconectando…';
  }

  function sendToServer(message) {
    if (!state.wsReady) {
      // Fallback REST si el socket no está disponible
      fallbackRestChat(message);
      return;
    }
    state.ws.send(JSON.stringify({ message, voice: state.selectedVoice }));
  }

  async function fallbackRestChat(message) {
    showThinking(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, voice: state.selectedVoice }),
      });
      const data = await res.json();
      showThinking(false);
      handleServerMessage({ type: 'response', ...data });
    } catch (err) {
      showThinking(false);
      addAssistantBubble('No pude conectarme con el servidor. Intenta de nuevo en un momento.', null, null);
    }
  }

  function handleServerMessage(payload) {
    if (payload.type === 'ready') {
      return;
    }
    if (payload.type === 'thinking') {
      showThinking(true);
      setOrbState('thinking');
      return;
    }
    if (payload.type === 'response') {
      showThinking(false);
      addAssistantBubble(payload.text, payload.action, payload.data);
      updateVoiceCaption(payload.text);
      if (payload.audio_base64) {
        playAudioBase64(payload.audio_base64);
      } else {
        setOrbState('idle');
      }
    }
  }

  // ------------------------------------------------------------------ //
  // Navegación entre pantallas
  // ------------------------------------------------------------------ //

  function showScreen(screenEl) {
    [welcomeScreen, mainScreen].forEach((s) => (s.hidden = s !== screenEl));
  }

  startChatBtn.addEventListener('click', () => {
    showScreen(mainScreen);
    textInput.focus();
  });

  startVoiceBtn.addEventListener('click', () => {
    showScreen(mainScreen);
    openVoiceMode();
  });

  newChatBtn.addEventListener('click', () => {
    messagesInner.innerHTML = '';
    messagesInner.appendChild(emptyState);
    emptyState.style.display = 'flex';
  });

  document.querySelectorAll('.suggestion-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const prompt = chip.dataset.prompt;
      textInput.value = prompt;
      handleSendMessage();
    });
  });

  // ------------------------------------------------------------------ //
  // Selección de voz
  // ------------------------------------------------------------------ //

  voiceSelect.addEventListener('change', () => {
    state.selectedVoice = voiceSelect.value;
  });

  // ------------------------------------------------------------------ //
  // Mensajería de texto (modo chat)
  // ------------------------------------------------------------------ //

  textInput.addEventListener('input', () => {
    sendBtn.disabled = textInput.value.trim().length === 0;
    textInput.style.height = 'auto';
    textInput.style.height = Math.min(textInput.scrollHeight, 140) + 'px';
  });

  textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  sendBtn.addEventListener('click', handleSendMessage);

  function handleSendMessage() {
    const text = textInput.value.trim();
    if (!text) return;
    addUserBubble(text);
    textInput.value = '';
    textInput.style.height = 'auto';
    sendBtn.disabled = true;
    sendToServer(text);
  }

  // ------------------------------------------------------------------ //
  // Renderizado de mensajes
  // ------------------------------------------------------------------ //

  function hideEmptyState() {
    if (emptyState.parentNode) emptyState.style.display = 'none';
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      messagesScroll.scrollTop = messagesScroll.scrollHeight;
    });
  }

  function addUserBubble(text) {
    hideEmptyState();
    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `
      <div class="avatar user">Tú</div>
      <div class="bubble-col">
        <div class="bubble">${escapeHtml(text)}</div>
      </div>`;
    messagesInner.appendChild(row);
    scrollToBottom();
  }

  function addAssistantBubble(text, action, data) {
    hideEmptyState();
    const row = document.createElement('div');
    row.className = 'message-row assistant';

    let cardHtml = '';
    if (action === 'show_weather_card' && data) {
      cardHtml = renderWeatherCard(data);
    } else if (action === 'show_calc_card' && data) {
      cardHtml = renderCalcCard(data);
    }

    row.innerHTML = `
      <div class="avatar baro"><span style="width:7px;height:7px;border-radius:50%;background:#CC785C;display:block;"></span></div>
      <div class="bubble-col">
        <div class="bubble">${escapeHtml(text)}</div>
        ${cardHtml}
      </div>`;
    messagesInner.appendChild(row);
    scrollToBottom();
  }

  function renderWeatherCard(data) {
    return `
      <div class="result-card">
        <div class="icon-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h.79a4.5 4.5 0 1 1 0 9Z"/></svg>
        </div>
        <div>
          <div class="result-title">Clima en ${escapeHtml(data.city || '')}</div>
          <div class="result-main">${data.temperature}°C</div>
          <div class="result-sub">${escapeHtml(data.description || '')} · sensación ${data.feels_like}°C</div>
        </div>
      </div>`;
  }

  function renderCalcCard(data) {
    return `
      <div class="result-card">
        <div class="icon-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 10h2M8 14h2M8 18h2M14 10h2M14 14h2M14 18h2"/></svg>
        </div>
        <div>
          <div class="result-title">Cálculo</div>
          <div class="result-main">${escapeHtml(String(data.result))}</div>
          <div class="result-sub">${escapeHtml(data.expression || '')}</div>
        </div>
      </div>`;
  }

  function showThinking(show) {
    let el = document.getElementById('thinking-indicator');
    if (show) {
      if (el) return;
      hideEmptyState();
      const row = document.createElement('div');
      row.className = 'thinking-row';
      row.id = 'thinking-indicator';
      row.innerHTML = `
        <div class="avatar baro"><span style="width:7px;height:7px;border-radius:50%;background:#CC785C;display:block;"></span></div>
        <div class="thinking-dots"><span></span><span></span><span></span></div>`;
      messagesInner.appendChild(row);
      scrollToBottom();
    } else if (el) {
      el.remove();
    }
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ------------------------------------------------------------------ //
  // Orbes: estado compartido entre el de mini-chat y el de modo voz
  // ------------------------------------------------------------------ //

  function setOrbState(s) {
    if (emptyOrb) emptyOrb.setState(s);
    if (voiceOrb) voiceOrb.setState(s);
  }

  // ------------------------------------------------------------------ //
  // Reconocimiento de voz — Web Speech API (nativo del navegador)
  // ------------------------------------------------------------------ //

  function getSpeechRecognition() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }

  function initRecognition() {
    const SpeechRecognitionCtor = getSpeechRecognition();
    if (!SpeechRecognitionCtor) return null;

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = 'es-ES';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      state.recognizing = true;
      micBtn.classList.add('listening');
      voiceMicBtn.classList.add('listening');
      setOrbState('listening');
      voiceStateLabel.textContent = 'ESCUCHANDO';
      voiceCaption.textContent = 'Te escucho…';
    };

    recognition.onerror = (e) => {
      state.recognizing = false;
      micBtn.classList.remove('listening');
      voiceMicBtn.classList.remove('listening');
      setOrbState('idle');
      voiceStateLabel.textContent = 'EN ESPERA';
      if (e.error === 'not-allowed' || e.error === 'permission-denied') {
        voiceCaption.textContent = 'Necesito permiso para usar el micrófono.';
      } else if (e.error !== 'no-speech' && e.error !== 'aborted') {
        voiceCaption.textContent = 'No pude escucharte bien. Intenta de nuevo.';
      }
    };

    recognition.onend = () => {
      state.recognizing = false;
      micBtn.classList.remove('listening');
      voiceMicBtn.classList.remove('listening');
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interim += transcript;
        }
      }

      if (interim && state.voiceModeOpen) {
        voiceCaption.textContent = interim;
      }

      if (finalTranscript.trim()) {
        if (state.voiceModeOpen) {
          voiceCaption.textContent = finalTranscript.trim();
        } else {
          textInput.value = finalTranscript.trim();
        }
        addUserBubble(finalTranscript.trim());
        setOrbState('thinking');
        voiceStateLabel.textContent = 'PENSANDO';
        sendToServer(finalTranscript.trim());
      }
    };

    return recognition;
  }

  function toggleListening() {
    if (!state.recognition) {
      state.recognition = initRecognition();
    }
    if (!state.recognition) {
      addAssistantBubble(
        'Tu navegador no soporta reconocimiento de voz nativo. Probemos por texto, o usa Google Chrome para hablar conmigo.',
        null, null
      );
      return;
    }

    if (state.recognizing) {
      state.recognition.stop();
    } else {
      try {
        state.recognition.start();
      } catch (err) {
        // ya está corriendo o navegador bloqueó: lo ignoramos
      }
    }
  }

  micBtn.addEventListener('click', toggleListening);
  voiceMicBtn.addEventListener('click', toggleListening);

  // ------------------------------------------------------------------ //
  // Modo voz inmersivo (overlay tipo Alexa)
  // ------------------------------------------------------------------ //

  function openVoiceMode() {
    state.voiceModeOpen = true;
    voiceOverlay.hidden = false;
    voiceCaption.textContent = 'Toca el micrófono y habla con Baro.';
    voiceStateLabel.textContent = 'EN ESPERA';
    setOrbState('idle');
  }

  function closeVoiceMode() {
    state.voiceModeOpen = false;
    voiceOverlay.hidden = true;
    if (state.recognizing && state.recognition) {
      state.recognition.stop();
    }
    stopCurrentAudio();
    setOrbState('idle');
  }

  openVoiceModeBtn.addEventListener('click', openVoiceMode);
  voiceCloseBtn.addEventListener('click', closeVoiceMode);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && state.voiceModeOpen) closeVoiceMode();
  });

  function updateVoiceCaption(text) {
    if (state.voiceModeOpen) {
      voiceCaption.textContent = text;
      voiceStateLabel.textContent = 'HABLANDO';
    }
  }

  // ------------------------------------------------------------------ //
  // Reproducción de audio TTS + análisis de amplitud en vivo
  // para animar el orbe mientras Baro "habla"
  // ------------------------------------------------------------------ //

  function getAudioContext() {
    if (!state.audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      state.audioCtx = new Ctx();
    }
    return state.audioCtx;
  }

  function stopCurrentAudio() {
    if (state.currentAudio) {
      try { state.currentAudio.pause(); } catch {}
      state.currentAudio = null;
    }
  }

  function playAudioBase64(base64) {
    stopCurrentAudio();

    const audio = new Audio('data:audio/mp3;base64,' + base64);
    state.currentAudio = audio;

    setOrbState('speaking');
    voiceStateLabel.textContent = 'HABLANDO';

    try {
      const ctx = getAudioContext();
      const source = ctx.createMediaElementSource(audio);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyser.connect(ctx.destination);

      const data = new Uint8Array(analyser.frequencyBinCount);

      function tick() {
        if (audio.paused || audio.ended) return;
        analyser.getByteFrequencyData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i];
        const avg = sum / data.length / 255; // 0..1
        if (emptyOrb) emptyOrb.pushAmplitude(avg);
        if (voiceOrb) voiceOrb.pushAmplitude(avg);
        requestAnimationFrame(tick);
      }
      tick();
    } catch (err) {
      // Si el análisis de frecuencia falla (por CORS u otra razón),
      // igual reproducimos el audio con una animación simulada.
      simulateSpeakingAmplitude(audio);
    }

    audio.addEventListener('ended', () => {
      setOrbState('idle');
      voiceStateLabel.textContent = state.voiceModeOpen ? 'EN ESPERA' : 'INACTIVA';
      if (state.voiceModeOpen) {
        voiceCaption.textContent = 'Toca el micrófono para hablar de nuevo.';
      }
    });

    audio.play().catch(() => {
      setOrbState('idle');
    });
  }

  function simulateSpeakingAmplitude(audio) {
    function tick() {
      if (audio.paused || audio.ended) return;
      const fake = 0.3 + Math.random() * 0.4;
      if (emptyOrb) emptyOrb.pushAmplitude(fake);
      if (voiceOrb) voiceOrb.pushAmplitude(fake);
      requestAnimationFrame(tick);
    }
    tick();
  }

  // ------------------------------------------------------------------ //
  // Arranque
  // ------------------------------------------------------------------ //

  document.addEventListener('DOMContentLoaded', () => {
    initOrbs();
    connectWebSocket();
  });
})();
