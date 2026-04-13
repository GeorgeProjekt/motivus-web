/**
 * Canvas Background — Physics-based graph visualization
 * Adapted from motivus-1 by Ing. Robert Šamárek (data4sci)
 */
class CanvasBackground {
  constructor() {
    this.canvas1 = null;
    this.canvas2 = null;
    this.ctx1 = null;
    this.ctx2 = null;
    this.graphs = [];
    this.mouse = { x: 0, y: 0, active: false };
    this.animationId = null;
    this.lastTime = 0;
    this.attractRadius = 300;
    this.highlightRadius = 200;
    this.breakpoints = { small: { max: 768, count: 4 }, medium: { min: 768, max: 1440, count: 8 }, large: { min: 1440, count: 12 } };
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) this.init();
  }

  init() {
    this.canvas1 = document.getElementById('canvas-layer-1');
    this.canvas2 = document.getElementById('canvas-layer-2');
    if (!this.canvas1 || !this.canvas2) return;
    this.resize();
    this.generate();
    this.listen();
    this.loop(performance.now());
  }

  setupCtx(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const r = canvas.getBoundingClientRect();
    canvas.width = r.width * dpr;
    canvas.height = r.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    canvas.style.width = r.width + 'px';
    canvas.style.height = r.height + 'px';
    ctx.imageSmoothingEnabled = true;
    return ctx;
  }

  resize() {
    if (!this.canvas1 || !this.canvas2) return;
    this.ctx1 = this.setupCtx(this.canvas1);
    this.ctx2 = this.setupCtx(this.canvas2);
  }

  getCount() {
    const w = window.innerWidth;
    if (w < 768) return this.breakpoints.small.count;
    if (w < 1440) return this.breakpoints.medium.count;
    return this.breakpoints.large.count;
  }

  generate() {
    this.graphs = [];
    const count = this.getCount();
    const l1 = Math.round(count * 0.6);
    for (let i = 0; i < l1; i++) this.graphs.push(this.createGraph(1));
    for (let i = 0; i < count - l1; i++) this.graphs.push(this.createGraph(2));
  }

  createGraph(layer) {
    const nc = 2 + Math.floor(Math.random() * 3);
    const w = this.canvas1.getBoundingClientRect().width;
    const h = this.canvas1.getBoundingClientRect().height;
    const nodes = [];
    for (let i = 0; i < nc; i++) {
      nodes.push({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.5,
        r: 3, br: 3, pp: Math.random() * Math.PI * 2, ps: 0.003 + Math.random() * 0.002
      });
    }
    const edges = [];
    const possible = [];
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) possible.push([i, j]);
    for (let i = possible.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [possible[i], possible[j]] = [possible[j], possible[i]]; }
    const target = Math.floor(possible.length * (0.4 + Math.random() * 0.3));
    const connected = new Set();
    for (let i = 0; i < Math.min(target, possible.length); i++) {
      const [a, b] = possible[i];
      const dist = Math.sqrt((nodes[a].x - nodes[b].x) ** 2 + (nodes[a].y - nodes[b].y) ** 2);
      edges.push({ a: nodes[a], b: nodes[b], rl: dist, k: 0.002 + Math.random() * 0.004 });
      connected.add(a); connected.add(b);
    }
    nodes.forEach((n, i) => {
      if (!connected.has(i) && nodes.length > 1) {
        const o = (i + 1 + Math.floor(Math.random() * (nodes.length - 1))) % nodes.length;
        const dist = Math.sqrt((n.x - nodes[o].x) ** 2 + (n.y - nodes[o].y) ** 2);
        edges.push({ a: n, b: nodes[o], rl: dist, k: 0.003 });
      }
    });
    return { nodes, edges, layer };
  }

  physics(dt) {
    const w = this.canvas1.getBoundingClientRect().width;
    const h = this.canvas1.getBoundingClientRect().height;
    this.graphs.forEach(g => {
      g.nodes.forEach(n => {
        let fx = (Math.random() - 0.5) * 0.04;
        let fy = (Math.random() - 0.5) * 0.04;
        g.edges.forEach(e => {
          if (e.a === n || e.b === n) {
            const o = e.a === n ? e.b : e.a;
            const dx = o.x - n.x, dy = o.y - n.y;
            const d = Math.sqrt(dx * dx + dy * dy);
            if (d > 0) {
              e.rl += (d - e.rl) * 0.01;
              const f = (d - e.rl) * e.k;
              fx += (dx / d) * f;
              fy += (dy / d) * f;
            }
          }
        });
        if (this.mouse.active) {
          const dx = this.mouse.x - n.x, dy = this.mouse.y - n.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < this.attractRadius && d > 0) {
            const s = Math.pow(1 - d / this.attractRadius, 2) * 0.03;
            fx += (dx / d) * s;
            fy += (dy / d) * s;
          }
        }
        n.vx = (n.vx + fx) * 0.99;
        n.vy = (n.vy + fy) * 0.99;
        n.x += n.vx * dt; n.y += n.vy * dt;
        if (n.x < 0) n.x += w; if (n.x > w) n.x -= w;
        if (n.y < 0) n.y += h; if (n.y > h) n.y -= h;
        n.pp += n.ps * dt;
        n.r = n.br + Math.sin(n.pp) * 1.0;
      });
    });
  }

  render() {
    if (!this.ctx1 || !this.ctx2) return;
    const w = this.canvas1.getBoundingClientRect().width;
    const h = this.canvas1.getBoundingClientRect().height;
    this.ctx1.clearRect(0, 0, w, h);
    this.ctx2.clearRect(0, 0, w, h);
    const tc = getComputedStyle(document.documentElement).getPropertyValue('--color-text').trim() || '#2D2A26';

    this.graphs.forEach(g => {
      const ctx = g.layer === 1 ? this.ctx1 : this.ctx2;
      const bo = g.layer === 1 ? 0.04 : 0.08;
      const hl = new Set();
      if (this.mouse.active) g.nodes.forEach(n => { if (Math.sqrt((n.x - this.mouse.x) ** 2 + (n.y - this.mouse.y) ** 2) < this.highlightRadius) hl.add(n); });

      g.edges.forEach(e => {
        ctx.beginPath();
        ctx.moveTo(e.a.x, e.a.y);
        ctx.lineTo(e.b.x, e.b.y);
        ctx.strokeStyle = this.rgba(tc, bo);
        ctx.lineWidth = 1;
        ctx.lineCap = 'round';
        ctx.stroke();
      });

      g.nodes.forEach(n => {
        const isHl = hl.has(n);
        const op = isHl ? Math.min(bo + 0.2, 0.35) : bo;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = this.rgba(tc, op);
        if (isHl) { ctx.shadowBlur = 6; ctx.shadowColor = this.rgba(tc, 0.3); }
        ctx.fill();
        if (isHl) ctx.shadowBlur = 0;
      });
    });
  }

  rgba(hex, a) {
    if (hex.startsWith('#')) {
      const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r},${g},${b},${a})`;
    }
    return `rgba(45,42,38,${a})`;
  }

  loop(ts) {
    this.animationId = requestAnimationFrame(this.loop.bind(this));
    const dt = this.lastTime ? (ts - this.lastTime) / 16.67 : 1;
    this.lastTime = ts;
    this.physics(dt);
    this.render();
  }

  listen() {
    let throttle;
    window.addEventListener('mousemove', (e) => {
      if (throttle) return;
      throttle = setTimeout(() => { throttle = null; }, 16);
      this.mouse.x = e.clientX;
      this.mouse.y = e.clientY + window.scrollY;
      this.mouse.active = true;
    }, { passive: true });
    window.addEventListener('mouseleave', () => { this.mouse.active = false; });
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => { this.resize(); this.generate(); }, 200);
    });
  }
}

window.addEventListener('DOMContentLoaded', () => { window.canvasBg = new CanvasBackground(); });
