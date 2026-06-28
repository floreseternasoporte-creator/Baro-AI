/* ==========================================================================
   app.js — Baro v3.0 MEGA
   ✅ Escucha continua con palabra de activación "Oye Baro" (tipo Siri)
   ✅ Saludo automático con voz al abrir el modo voz
   ✅ El micrófono queda siempre abierto en modo voz
   ✅ Responde solo cuando detecta "Oye Baro" primero
   ✅ Animación del orbe mejorada
   ✅ UI mejorada con chips de sugerencias ampliadas
   ========================================================================== */

(() => {
  'use strict';

  // ─── Config ──────────────────────────────────────────────────────── //
  const WS_PATH = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';
  const WAKE_WORD = 'oye baro';
  const WAKE_WORD_ALT = ['hey baro', 'ey baro', 'oye varo', 'hola baro', 'baro'];

  const state = {
    ws: null,
    wsReady: false,
    recognizing: false,
    recognition: null,
    selectedVoice: 'es-US-PalomaNeural',
    audioCtx: null,
    currentAudio: null,
    voiceModeOpen: false,
    wakeWordMode: true,      // Modo siempre escuchando con palabra clave
    wakeWordDetected: false, // Si ya se dijo "Oye Baro" y estamos esperando el comando
    lastTranscript: '',
    isPlaying: false,
    autoRestart: false,
    greetingPlayed: false,
  };

  // ─── DOM refs ─────────────────────────────────────────────────────── //
  const $ = (id) => document.getElementById(id);

  const welcomeScreen  = $('welcome-screen');
  const mainScreen     = $('main-screen');
  const voiceOverlay   = $('voice-overlay');
  const startVoiceBtn  = $('start-voice-btn');
  const startChatBtn   = $('start-chat-btn');
  const newChatBtn     = $('new-chat-btn');
  const messagesScroll = $('messages-scroll');
  const messagesInner  = $('messages-inner');
  const emptyState     = $('empty-state');
  const textInput      = $('text-input');
  const sendBtn        = $('send-btn');
  const micBtn         = $('mic-btn');
  const connDot        = $('conn-dot');
  const connLabel      = $('conn-label');
  const voiceSelect    = $('voice-select');
  const openVoiceModeBtn = $('open-voice-mode-btn');
  const voiceMicBtn    = $('voice-mic-btn');
  const voiceCloseBtn  = $('voice-close-btn');
  const voiceCaption   = $('voice-caption');
  const voiceStateLabel = $('voice-state-label');
  const wakeWordBadge  = $('wake-word-badge');

  // ─── Orbes ────────────────────────────────────────────────────────── //
  let welcomeOrb = null, emptyOrb = null, voiceOrb = null;

  function initOrbs() {
    welcomeOrb = new BaroOrb($('welcome-orb-canvas'), { colorMode: 'light', numParticles: 280, baseRadius: 0.66 });
    emptyOrb   = new BaroOrb($('empty-orb-canvas'),   { colorMode: 'light', numParticles: 150, baseRadius: 0.7 });
    voiceOrb   = new BaroOrb($('voice-orb-canvas'),   { colorMode: 'dark',  numParticles: 360, baseRadius: 0.6 });
    welcomeOrb.setState('idle');
    emptyOrb.setState('idle');
    voiceOrb.setState('idle');
  }

  // ─── WebSocket ────────────────────────────────────────────────────── //
  function connectWebSocket() {
    try { state.ws = new WebSocket(WS_PATH); } catch { setConnectionStatus(false); return; }

    state.ws.onopen = () => { state.wsReady = true; setConnectionStatus(true); };
    state.ws.onclose = () => {
      state.wsReady = false;
      setConnectionStatus(false);
      setTimeout(connectWebSocket, 3000);
    };
    state.ws.onerror = () => setConnectionStatus(false);
    state.ws.onmessage = (event) => {
      let payload;
      try { payload = JSON.parse(event.data); } catch { return; }
      handleServerMessage(payload);
    };
  }

  function setConnectionStatus(online) {
    connDot.classList.toggle('offline', !online);
    connLabel.textContent = online ? 'Baro está activa' : 'Reconectando…';
  }

  function sendToServer(message) {
    if (!state.wsReady) { fallbackRestChat(message); return; }
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
    } catch {
      showThinking(false);
      addAssistantBubble('No pude conectarme con el servidor. Intenta de nuevo.', null, null);
    }
  }

  function handleServerMessage(payload) {
    if (payload.type === 'ready') return;
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
        if (state.voiceModeOpen) scheduleRestart();
      }
    }
  }

  // ─── Pantallas ────────────────────────────────────────────────────── //
  function showScreen(screenEl) {
    [welcomeScreen, mainScreen].forEach((s) => (s.hidden = s !== screenEl));
  }

  startChatBtn.addEventListener('click', () => { showScreen(mainScreen); textInput.focus(); });
  startVoiceBtn.addEventListener('click', () => { showScreen(mainScreen); openVoiceMode(); });
  newChatBtn.addEventListener('click', () => {
    messagesInner.innerHTML = '';
    messagesInner.appendChild(emptyState);
    emptyState.style.display = 'flex';
  });

  document.querySelectorAll('.suggestion-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      textInput.value = chip.dataset.prompt;
      handleSendMessage();
    });
  });

  voiceSelect.addEventListener('change', () => { state.selectedVoice = voiceSelect.value; });

  // ─── Chat de texto ────────────────────────────────────────────────── //
  textInput.addEventListener('input', () => {
    sendBtn.disabled = textInput.value.trim().length === 0;
    textInput.style.height = 'auto';
    textInput.style.height = Math.min(textInput.scrollHeight, 140) + 'px';
  });
  textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }
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

  // ─── Render mensajes ─────────────────────────────────────────────── //
  function hideEmptyState() {
    if (emptyState.parentNode) emptyState.style.display = 'none';
  }
  function scrollToBottom() {
    requestAnimationFrame(() => { messagesScroll.scrollTop = messagesScroll.scrollHeight; });
  }

  function addUserBubble(text) {
    hideEmptyState();
    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `
      <div class="avatar user">Tú</div>
      <div class="bubble-col"><div class="bubble">${escapeHtml(text)}</div></div>`;
    messagesInner.appendChild(row);
    scrollToBottom();
  }

  function addAssistantBubble(text, action, data) {
    hideEmptyState();
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    let cardHtml = '';
    if (action === 'show_weather_card' && data) cardHtml = renderWeatherCard(data);
    else if (action === 'show_calc_card' && data) cardHtml = renderCalcCard(data);
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
    return `<div class="result-card">
      <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h.79a4.5 4.5 0 1 1 0 9Z"/></svg></div>
      <div>
        <div class="result-title">Clima en ${escapeHtml(data.city || '')}</div>
        <div class="result-main">${data.temperature}°C</div>
        <div class="result-sub">${escapeHtml(data.description || '')} · sensación ${data.feels_like}°C · humedad ${data.humidity}%</div>
      </div></div>`;
  }

  function renderCalcCard(data) {
    return `<div class="result-card">
      <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 10h2M8 14h2M8 18h2M14 10h2M14 14h2M14 18h2"/></svg></div>
      <div>
        <div class="result-title">Cálculo</div>
        <div class="result-main">${escapeHtml(String(data.result))}</div>
        <div class="result-sub">${escapeHtml(data.expression || '')}</div>
      </div></div>`;
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
    } else if (el) el.remove();
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ─── Orbe ─────────────────────────────────────────────────────────── //
  function setOrbState(s) {
    if (emptyOrb) emptyOrb.setState(s);
    if (voiceOrb)  voiceOrb.setState(s);
  }

  // ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ───  //
  //  SISTEMA DE VOZ — ESCUCHA CONTINUA TIPO SIRI                        //
  // ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ───  //

  function getSpeechRecognition() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }

  function containsWakeWord(transcript) {
    const t = transcript.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    if (t.includes(WAKE_WORD)) return true;
    for (const alt of WAKE_WORD_ALT) {
      if (t.includes(alt)) return true;
    }
    return false;
  }

  function stripWakeWord(transcript) {
    let t = transcript.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    for (const alt of [WAKE_WORD, ...WAKE_WORD_ALT]) {
      t = t.replace(alt, '').trim();
    }
    return t;
  }

  function initRecognition() {
    const SpeechRecognitionCtor = getSpeechRecognition();
    if (!SpeechRecognitionCtor) return null;

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = 'es-ES';
    recognition.continuous = false;   // En Chrome continuo falla; reiniciamos manualmente
    recognition.interimResults = true;
    recognition.maxAlternatives = 3;

    recognition.onstart = () => {
      state.recognizing = true;
      if (state.wakeWordDetected) {
        // Ya activado: mostramos "escuchando"
        micBtn.classList.add('listening');
        voiceMicBtn.classList.add('listening');
        setOrbState('listening');
        voiceStateLabel.textContent = 'ESCUCHANDO';
        voiceCaption.textContent = 'Te escucho…';
      } else {
        // Esperando "Oye Baro"
        setOrbState('idle');
        voiceStateLabel.textContent = 'DI "OYE BARO"';
        voiceCaption.textContent = 'Escuchando en segundo plano…';
        showWakeBadge(true);
      }
    };

    recognition.onerror = (e) => {
      state.recognizing = false;
      micBtn.classList.remove('listening');
      voiceMicBtn.classList.remove('listening');

      if (e.error === 'not-allowed' || e.error === 'permission-denied') {
        setOrbState('idle');
        voiceStateLabel.textContent = 'SIN PERMISO';
        voiceCaption.textContent = 'Necesito permiso para usar el micrófono.';
        showWakeBadge(false);
        return;
      }

      // Para no-speech, aborted: reiniciamos si estamos en modo voz
      if (state.voiceModeOpen && state.autoRestart && !state.isPlaying) {
        setTimeout(startListeningContinuous, 400);
      } else {
        voiceStateLabel.textContent = state.wakeWordDetected ? 'ESCUCHANDO' : 'DI "OYE BARO"';
      }
    };

    recognition.onend = () => {
      state.recognizing = false;
      micBtn.classList.remove('listening');
      voiceMicBtn.classList.remove('listening');

      // Auto-reinicio si estamos en modo voz y no estamos reproduciendo audio
      if (state.voiceModeOpen && state.autoRestart && !state.isPlaying) {
        setTimeout(startListeningContinuous, 300);
      }
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        // Tomamos la mejor alternativa
        const transcript = result[0].transcript;
        if (result.isFinal) {
          finalTranscript += transcript;
        } else {
          interim += transcript;
        }
      }

      if (interim && state.voiceModeOpen) {
        if (!state.wakeWordMode || state.wakeWordDetected) {
          voiceCaption.textContent = interim;
        }
      }

      if (finalTranscript.trim()) {
        processVoiceInput(finalTranscript.trim());
      }
    };

    return recognition;
  }

  function processVoiceInput(transcript) {
    const hasWake = containsWakeWord(transcript);

    if (state.wakeWordMode && state.voiceModeOpen) {
      if (!state.wakeWordDetected) {
        if (hasWake) {
          // Palabra de activación detectada
          const command = stripWakeWord(transcript).trim();
          if (command.length > 2) {
            // El usuario dijo "Oye Baro, <comando>" en un solo enunciado
            activateAndCommand(command);
          } else {
            // Solo dijo "Oye Baro" — mostrar que estamos listos
            activateWakeMode();
          }
        }
        // Si no hay wake word, ignoramos
        return;
      } else {
        // Ya activado: procesamos el comando
        const command = transcript.trim();
        if (command.length > 1) {
          executeCommand(command);
        }
        state.wakeWordDetected = false;
        return;
      }
    }

    // Modo sin wake word (botón manual)
    if (state.voiceModeOpen) {
      voiceCaption.textContent = transcript;
    } else {
      textInput.value = transcript;
    }
    addUserBubble(transcript);
    setOrbState('thinking');
    voiceStateLabel.textContent = 'PENSANDO';
    sendToServer(transcript);
  }

  function activateWakeMode() {
    state.wakeWordDetected = true;
    setOrbState('listening');
    voiceStateLabel.textContent = '¿EN QUÉ TE AYUDO?';
    voiceCaption.textContent = 'Dime, estoy lista…';
    voiceMicBtn.classList.add('listening');
    showWakeBadge(false);

    // Volver al modo espera después de 5s si no hay comando
    setTimeout(() => {
      if (state.wakeWordDetected) {
        state.wakeWordDetected = false;
        voiceStateLabel.textContent = 'DI "OYE BARO"';
        voiceCaption.textContent = 'Escuchando en segundo plano…';
        voiceMicBtn.classList.remove('listening');
        showWakeBadge(true);
      }
    }, 5000);
  }

  function activateAndCommand(command) {
    state.wakeWordDetected = false;
    addUserBubble(command);
    voiceCaption.textContent = command;
    setOrbState('thinking');
    voiceStateLabel.textContent = 'PENSANDO';
    showWakeBadge(false);
    sendToServer(command);
  }

  function executeCommand(command) {
    addUserBubble(command);
    voiceCaption.textContent = command;
    setOrbState('thinking');
    voiceStateLabel.textContent = 'PENSANDO';
    voiceMicBtn.classList.remove('listening');
    showWakeBadge(false);
    sendToServer(command);
  }

  function showWakeBadge(show) {
    if (wakeWordBadge) {
      wakeWordBadge.style.display = show ? 'flex' : 'none';
    }
  }

  function startListeningContinuous() {
    if (!state.recognition) {
      state.recognition = initRecognition();
    }
    if (!state.recognition) {
      voiceCaption.textContent = 'Tu navegador no soporta reconocimiento de voz. Usa Google Chrome.';
      return;
    }
    if (state.recognizing) return;
    try {
      state.recognition.start();
    } catch (err) {
      // ya está corriendo
    }
  }

  function stopListening() {
    state.autoRestart = false;
    if (state.recognizing && state.recognition) {
      try { state.recognition.stop(); } catch {}
    }
  }

  function scheduleRestart() {
    if (state.voiceModeOpen && state.autoRestart) {
      setTimeout(startListeningContinuous, 600);
    }
  }

  micBtn.addEventListener('click', () => {
    if (!state.recognition) state.recognition = initRecognition();
    if (!state.recognition) {
      addAssistantBubble('Tu navegador no soporta reconocimiento de voz nativo. Usa Google Chrome.', null, null);
      return;
    }
    if (state.recognizing) {
      state.autoRestart = false;
      state.recognition.stop();
    } else {
      state.wakeWordMode = false; // Modo manual en chat
      state.autoRestart = false;
      try { state.recognition.start(); } catch {}
    }
  });

  // El botón del mic en modo voz ahora es solo para pausar/reanudar
  voiceMicBtn.addEventListener('click', () => {
    if (state.recognizing) {
      stopListening();
      voiceStateLabel.textContent = 'PAUSADO';
      voiceCaption.textContent = 'Toca de nuevo para reanudar.';
      showWakeBadge(false);
    } else {
      state.autoRestart = true;
      state.wakeWordMode = true;
      state.wakeWordDetected = false;
      startListeningContinuous();
    }
  });

  // ─── Modo voz inmersivo ───────────────────────────────────────────── //
  function openVoiceMode() {
    state.voiceModeOpen = true;
    state.wakeWordMode = true;
    state.wakeWordDetected = false;
    state.autoRestart = true;
    voiceOverlay.hidden = false;
    voiceStateLabel.textContent = 'INICIANDO…';
    voiceCaption.textContent = 'Preparando a Baro…';
    setOrbState('idle');

    // Saludo automático con voz al abrir
    if (!state.greetingPlayed) {
      state.greetingPlayed = true;
      playWelcomeGreeting();
    } else {
      // Si ya saludó, empezar a escuchar directamente
      setTimeout(startListeningContinuous, 500);
    }
  }

  function playWelcomeGreeting() {
    const greetings = [
      '¡Hola! Soy Baro, tu asistente inteligente. Ya estoy escuchando. Solo di "Oye Baro" y luego tu pregunta.',
      '¡Hola! Baro lista y activada. Di "Oye Baro" seguido de tu pregunta y te respondo al instante.',
      '¡Hola! Aquí estoy. Soy Baro. Para hablar conmigo, di "Oye Baro" y luego lo que necesitas.',
    ];
    const greeting = greetings[Math.floor(Math.random() * greetings.length)];

    updateVoiceCaption(greeting);
    voiceStateLabel.textContent = 'SALUDANDO';
    setOrbState('speaking');

    // Pedir TTS del saludo al servidor
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'saludo_inicial_baro_v3', voice: state.selectedVoice }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.audio_base64) {
          playAudioBase64(data.audio_base64, () => {
            voiceStateLabel.textContent = 'DI "OYE BARO"';
            voiceCaption.textContent = 'Escuchando en segundo plano…';
            showWakeBadge(true);
            startListeningContinuous();
          });
        } else {
          startListeningContinuous();
        }
      })
      .catch(() => {
        startListeningContinuous();
      });
  }

  function closeVoiceMode() {
    state.voiceModeOpen = false;
    state.autoRestart = false;
    state.wakeWordDetected = false;
    voiceOverlay.hidden = true;
    stopListening();
    stopCurrentAudio();
    setOrbState('idle');
    showWakeBadge(false);
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

  // ─── Audio TTS ────────────────────────────────────────────────────── //
  function getAudioContext() {
    if (!state.audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      state.audioCtx = new Ctx();
    }
    return state.audioCtx;
  }

  function stopCurrentAudio() {
    state.isPlaying = false;
    if (state.currentAudio) {
      try { state.currentAudio.pause(); } catch {}
      state.currentAudio = null;
    }
  }

  function playAudioBase64(base64, onEndCallback) {
    stopCurrentAudio();
    state.isPlaying = true;

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
        const avg = sum / data.length / 255;
        if (emptyOrb) emptyOrb.pushAmplitude(avg);
        if (voiceOrb)  voiceOrb.pushAmplitude(avg);
        requestAnimationFrame(tick);
      }
      tick();
    } catch {
      simulateSpeakingAmplitude(audio);
    }

    audio.addEventListener('ended', () => {
      state.isPlaying = false;
      setOrbState('idle');
      if (state.voiceModeOpen) {
        voiceStateLabel.textContent = 'DI "OYE BARO"';
        voiceCaption.textContent = 'Escuchando en segundo plano…';
        showWakeBadge(true);
        scheduleRestart();
      } else {
        voiceStateLabel.textContent = 'INACTIVA';
      }
      if (onEndCallback) onEndCallback();
    });

    audio.play().catch(() => {
      state.isPlaying = false;
      setOrbState('idle');
      if (onEndCallback) onEndCallback();
    });
  }

  function simulateSpeakingAmplitude(audio) {
    function tick() {
      if (audio.paused || audio.ended) return;
      const fake = 0.3 + Math.random() * 0.4;
      if (emptyOrb) emptyOrb.pushAmplitude(fake);
      if (voiceOrb)  voiceOrb.pushAmplitude(fake);
      requestAnimationFrame(tick);
    }
    tick();
  }

  // ─── Arranque ─────────────────────────────────────────────────────── //
  document.addEventListener('DOMContentLoaded', () => {
    initOrbs();
    connectWebSocket();
  });
})();
