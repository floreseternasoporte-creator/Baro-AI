/* ==========================================================================
   orb.js — El orbe de partículas de Baro.
   Elemento de firma: una nube de puntos que respira en reposo, se contrae
   y vibra al escuchar, y ondula en oleadas concéntricas al hablar — igual
   que pediste, "como un cerebro" que se mueve mientras habla.
   ========================================================================== */

class BaroOrb {
  /**
   * @param {HTMLCanvasElement} canvas
   * @param {Object} options
   */
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.state = 'idle'; // idle | listening | thinking | speaking
    this.amplitude = 0; // nivel de audio en vivo (0..1), usado al hablar
    this.targetAmplitude = 0;
    this.time = 0;
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.colorMode = options.colorMode || 'light'; // 'light' | 'dark'
    this.particles = [];
    this.numParticles = options.numParticles || 220;
    this.baseRadius = options.baseRadius || 0.62; // fracción del tamaño del canvas

    this._resize();
    this._buildParticles();

    this._onResize = () => this._resize();
    window.addEventListener('resize', this._onResize);

    this._raf = null;
    this._start();
  }

  /* ------------------------------------------------------------------ */

  _resize() {
    const rect = this.canvas.getBoundingClientRect();
    const size = Math.round(Math.min(rect.width, rect.height)) || 300;
    this.size = size;
    this.canvas.width = size * this.dpr;
    this.canvas.height = size * this.dpr;
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(this.dpr, this.dpr);
    this.center = size / 2;
  }

  _buildParticles() {
    this.particles = [];
    for (let i = 0; i < this.numParticles; i++) {
      // Distribución esférica proyectada (efecto 3D sutil tipo "cerebro de puntos")
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = 2 * Math.PI * Math.random();
      this.particles.push({
        phi,
        theta,
        speed: 0.15 + Math.random() * 0.35,
        wobble: Math.random() * Math.PI * 2,
        wobbleSpeed: 0.4 + Math.random() * 0.8,
        sizeBase: 1.1 + Math.random() * 1.8,
        depthOffset: Math.random(),
      });
    }
  }

  /* ------------------------------------------------------------------ */

  setState(state) {
    this.state = state;
    if (state !== 'speaking') {
      this.targetAmplitude = state === 'listening' ? 0.35 : 0.15;
    }
  }

  /** Empuja un nivel de amplitud de audio en vivo (0..1) mientras Baro habla. */
  pushAmplitude(level) {
    this.targetAmplitude = Math.min(1, Math.max(0, level));
  }

  /* ------------------------------------------------------------------ */

  _start() {
    const loop = () => {
      this.time += 0.016;
      this.amplitude += (this.targetAmplitude - this.amplitude) * 0.12;
      this._draw();
      this._raf = requestAnimationFrame(loop);
    };
    loop();
  }

  destroy() {
    if (this._raf) cancelAnimationFrame(this._raf);
    window.removeEventListener('resize', this._onResize);
  }

  /* ------------------------------------------------------------------ */

  _palette() {
    if (this.colorMode === 'dark') {
      return {
        bg: null,
        particle: '#F0C9B8',
        particleCore: '#CC785C',
        glow: 'rgba(204, 120, 92, 0.35)',
        core: 'rgba(244, 241, 234, 0.9)',
      };
    }
    return {
      bg: null,
      particle: '#CC785C',
      particleCore: '#B35E42',
      glow: 'rgba(204, 120, 92, 0.22)',
      core: 'rgba(61, 57, 41, 0.85)',
    };
  }

  _draw() {
    const { ctx, size, center } = this;
    ctx.clearRect(0, 0, size, size);

    const pal = this._palette();
    const breathing = Math.sin(this.time * 0.9) * 0.025;
    const pulse =
      this.state === 'thinking'
        ? Math.sin(this.time * 5) * 0.06
        : 0;

    const radius = center * this.baseRadius * (1 + breathing + pulse);

    // --- Glow de fondo ---
    const glowRadius = radius * (1.5 + this.amplitude * 0.6);
    const grad = ctx.createRadialGradient(center, center, radius * 0.2, center, center, glowRadius);
    grad.addColorStop(0, pal.glow);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(center, center, glowRadius, 0, Math.PI * 2);
    ctx.fill();

    // --- Núcleo sutil (degradado, no un círculo duro) ---
    const coreRadius = radius * 0.22;
    const coreGrad = ctx.createRadialGradient(center, center, 0, center, center, coreRadius);
    coreGrad.addColorStop(0, pal.core);
    coreGrad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.beginPath();
    ctx.arc(center, center, coreRadius, 0, Math.PI * 2);
    ctx.fillStyle = coreGrad;
    ctx.globalAlpha = 0.55 + this.amplitude * 0.35;
    ctx.fill();
    ctx.globalAlpha = 1;

    // --- Partículas ---
    const rotationSpeed = this.state === 'listening' ? 0.25 : 0.12;
    const agitation =
      this.state === 'speaking'
        ? 0.18 + this.amplitude * 0.55
        : this.state === 'listening'
        ? 0.12
        : this.state === 'thinking'
        ? 0.16
        : 0.05;

    // Ordenar por profundidad (z) para dar sensación 3D al dibujar
    const projected = this.particles.map((p, idx) => {
      const theta = p.theta + this.time * rotationSpeed * p.speed;
      const wob = Math.sin(this.time * p.wobbleSpeed + p.wobble) * agitation;
      const r = radius * (1 + wob * 0.5);

      const x = Math.sin(p.phi) * Math.cos(theta);
      const y = Math.sin(p.phi) * Math.sin(theta) * 0.92; // esfera casi sin achatar
      const z = Math.cos(p.phi);

      return {
        sx: center + x * r,
        sy: center + y * r,
        z,
        sizeBase: p.sizeBase,
        depthOffset: p.depthOffset,
      };
    });

    projected.sort((a, b) => a.z - b.z);

    for (const pt of projected) {
      const depthScale = 0.4 + (pt.z + 1) / 2 * 0.95;
      const alpha = 0.16 + (pt.z + 1) / 2 * 0.78;
      const size_ = pt.sizeBase * depthScale * (1 + this.amplitude * 0.6);

      ctx.beginPath();
      ctx.arc(pt.sx, pt.sy, Math.max(0.6, size_), 0, Math.PI * 2);
      ctx.fillStyle = pt.z > 0.25 ? pal.particleCore : pal.particle;
      ctx.globalAlpha = alpha;
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
}

window.BaroOrb = BaroOrb;
