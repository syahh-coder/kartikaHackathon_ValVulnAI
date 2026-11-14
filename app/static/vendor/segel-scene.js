// Three.js minimal scene for "SEGEL" — Smooth Specimen Capsule with Horizontal Neon Lime "valvuln" Branding
import * as THREE from './three.module.min.js';

let renderer, scene, camera, capsuleMesh, canvas;
let frontTextMesh, backTextMesh, haloMesh;
let textTexture, haloTexture, matcapTexture;
let rafId = 0;
let startTime = 0;
let lastFrameTime = 0;
let isPaused = false;
let scrollProgress = 0;

// Stabilized Target Coordinates: Anchored gracefully without erratic jumping
let targetX = 2.2;
let targetY = 0.25;
let targetRotX = 0.08;
let targetRotZ = 0.02;

const FRAME_INTERVAL_MS = 33; // ~30fps cap to keep GPU and UI buttery smooth
const reducedMotionQuery = typeof window !== 'undefined' && window.matchMedia
  ? window.matchMedia('(prefers-reduced-motion: reduce)')
  : null;

function isReducedMotion() {
  return Boolean(reducedMotionQuery?.matches);
}

function createChromeMatcap() {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 256;
  const ctx = c.getContext('2d');

  // Radial metallic sphere gradient with high-contrast specular reflections and subtle lime-lemon rim accent
  const grad = ctx.createRadialGradient(92, 72, 8, 128, 128, 122);
  grad.addColorStop(0, '#FFFFFF');
  grad.addColorStop(0.20, '#F4FFF0');
  grad.addColorStop(0.40, '#4E6278');
  grad.addColorStop(0.68, '#141E2C');
  grad.addColorStop(0.86, '#98AEC4');
  grad.addColorStop(0.96, '#BFFF00'); // Ambient lemon-lime rim accent
  grad.addColorStop(1, '#080E18');

  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(128, 128, 124, 0, Math.PI * 2);
  ctx.fill();

  const tex = new THREE.CanvasTexture(c);
  tex.minFilter = THREE.LinearFilter;
  return tex;
}

function createTextTexture(text) {
  const c = document.createElement('canvas');
  c.width = 1024;
  c.height = 256;
  const ctx = c.getContext('2d');

  ctx.clearRect(0, 0, c.width, c.height);

  // Modern tech-focused font styling
  ctx.font = '900 108px "Schibsted Grotesk", system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  // Horizontal gradient: Neon Lime to Electric Emerald
  const grad = ctx.createLinearGradient(120, 0, 904, 0);
  grad.addColorStop(0, '#D4FF00');    // Electric lemon
  grad.addColorStop(0.45, '#76FF03');  // Vibrant neon lime
  grad.addColorStop(0.85, '#00E676');  // Electric emerald
  grad.addColorStop(1, '#69F0AE');    // Bright lime-cyan

  // Ambient outer neon glow
  ctx.shadowColor = 'rgba(118, 255, 3, 0.85)';
  ctx.shadowBlur = 24;

  ctx.letterSpacing = '8px';
  ctx.fillStyle = grad;
  ctx.fillText(text, 512, 128);

  // Crisp inner white accent stroke
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
  ctx.lineWidth = 2.5;
  ctx.shadowBlur = 0;
  ctx.strokeText(text, 512, 128);

  const tex = new THREE.CanvasTexture(c);
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;
  return tex;
}

function createHaloTexture() {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext('2d');

  // Ambient lemon-lime radial aura
  const g = ctx.createRadialGradient(256, 256, 60, 256, 256, 256);
  g.addColorStop(0, 'rgba(191, 255, 0, 0.32)');
  g.addColorStop(0.35, 'rgba(118, 255, 3, 0.16)');
  g.addColorStop(0.70, 'rgba(0, 230, 118, 0.05)');
  g.addColorStop(1, 'rgba(0, 0, 0, 0)');

  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(256, 256, 256, 0, Math.PI * 2);
  ctx.fill();

  const tex = new THREE.CanvasTexture(c);
  tex.minFilter = THREE.LinearFilter;
  return tex;
}

function updateTargets(elapsedSec) {
  const isMobile = window.innerWidth < 960;
  const reduced = isReducedMotion();

  // Gentle, calm harmonic float without erratic displacement
  const floatOffset = reduced ? 0 : Math.sin(elapsedSec * 0.75) * 0.06;

  // Stably anchored coordinates: never jumping across the screen or colliding with text
  if (isMobile) {
    targetX = 0;
    targetY = -0.7 + floatOffset;
  } else {
    // Desktop: Anchored comfortably in the stage area, completely clear of the left text "m."
    targetX = 2.3;
    targetY = 0.25 + floatOffset;
  }

  targetRotX = 0.08;
  targetRotZ = 0.02;
}

function snapCapsuleToTargets() {
  if (!capsuleMesh) return;
  updateTargets(0);
  capsuleMesh.position.set(targetX, targetY, 0.5);
  capsuleMesh.rotation.set(targetRotX, 0, targetRotZ);
}

function renderOnce() {
  if (!renderer || !scene || !camera || !capsuleMesh) return;
  renderer.render(scene, camera);
}

function onResize() {
  if (!renderer || !camera) return;
  const w = window.innerWidth;
  const h = window.innerHeight;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h, false);
  if (isReducedMotion()) {
    snapCapsuleToTargets();
    renderOnce();
  }
}

function onScroll() {
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  if (maxScroll > 0) {
    scrollProgress = Math.min(Math.max(window.scrollY / maxScroll, 0), 1);
  } else {
    scrollProgress = 0;
  }
  if (isReducedMotion()) {
    snapCapsuleToTargets();
    renderOnce();
  }
}

function canAnimate() {
  if (isPaused || document.hidden) return false;
  if (!canvas || !capsuleMesh || !renderer) return false;
  if (canvas.closest('[hidden]')) return false;
  return true;
}

function scheduleNextFrame() {
  if (rafId || isReducedMotion() || !canAnimate()) return;
  rafId = requestAnimationFrame(animate);
}

function stopLoop() {
  if (rafId) {
    cancelAnimationFrame(rafId);
    rafId = 0;
  }
}

function animate(now) {
  rafId = 0;
  if (!canAnimate()) return;

  if (now - lastFrameTime >= FRAME_INTERVAL_MS) {
    lastFrameTime = now;
    const elapsedSec = (now - startTime) * 0.001;
    updateTargets(elapsedSec);

    // Smooth, silky-smooth damping for position
    capsuleMesh.position.x += (targetX - capsuleMesh.position.x) * 0.06;
    capsuleMesh.position.y += (targetY - capsuleMesh.position.y) * 0.06;
    capsuleMesh.rotation.x += (targetRotX - capsuleMesh.rotation.x) * 0.06;
    capsuleMesh.rotation.z += (targetRotZ - capsuleMesh.rotation.z) * 0.06;

    // Putaran teratur, jelas kemana: Steady, continuous, clockwise/counter-clockwise carousel yaw
    // Memutar kapsul dengan konstan sehingga tulisan "valvuln" depan & belakang terlihat bergantian secara teratur
    capsuleMesh.rotation.y = elapsedSec * 0.45;

    renderOnce();
  }

  if (!isReducedMotion()) {
    scheduleNextFrame();
  }
}

function setPaused(paused) {
  isPaused = Boolean(paused);
  if (isPaused) {
    stopLoop();
  } else if (isReducedMotion()) {
    snapCapsuleToTargets();
    renderOnce();
  } else {
    lastFrameTime = 0;
    scheduleNextFrame();
  }
}

export function initSegelScene(containerId) {
  canvas = document.getElementById(containerId);
  if (!canvas) return null;

  const w = window.innerWidth;
  const h = window.innerHeight;

  renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    alpha: true,
    antialias: true,
    preserveDrawingBuffer: true,
    powerPreference: 'default'
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setSize(w, h, false);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 50);
  camera.position.set(0, 0, 12);

  matcapTexture = createChromeMatcap();
  const chromeMat = new THREE.MeshMatcapMaterial({ matcap: matcapTexture });

  // 1. Kapsul Laporan Chrome (Objek Utama Segel)
  const capGeo = new THREE.CapsuleGeometry(1.2, 2.7, 16, 32);
  capsuleMesh = new THREE.Mesh(capGeo, chromeMat);

  // 2. Tulisan Horizontal "valvuln" Depan & Belakang dengan Gradasi Hijau Lime Neon
  textTexture = createTextTexture('valvuln');
  const textGeo = new THREE.PlaneGeometry(2.2, 0.55);
  const textMat = new THREE.MeshBasicMaterial({
    map: textTexture,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide
  });

  // Tulisan Depan
  frontTextMesh = new THREE.Mesh(textGeo, textMat);
  frontTextMesh.position.set(0, 0, 1.22);
  capsuleMesh.add(frontTextMesh);

  // Tulisan Belakang (Diputar 180° agar terbaca horizontal dan normal dari sisi belakang)
  backTextMesh = new THREE.Mesh(textGeo, textMat);
  backTextMesh.position.set(0, 0, -1.22);
  backTextMesh.rotation.set(0, Math.PI, 0);
  capsuleMesh.add(backTextMesh);

  // 3. Ambient Hijau Lemon Tipis di Sekitar Kapsul
  haloTexture = createHaloTexture();
  const haloGeo = new THREE.PlaneGeometry(7.2, 7.2);
  const haloMat = new THREE.MeshBasicMaterial({
    map: haloTexture,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    opacity: 0.48
  });
  haloMesh = new THREE.Mesh(haloGeo, haloMat);
  haloMesh.position.set(0, 0, -0.15);
  capsuleMesh.add(haloMesh);

  scene.add(capsuleMesh);

  startTime = performance.now();
  lastFrameTime = 0;
  onScroll();
  snapCapsuleToTargets();
  renderOnce();

  window.addEventListener('resize', onResize);
  window.addEventListener('scroll', onScroll, { passive: true });
  reducedMotionQuery?.addEventListener?.('change', () => {
    if (isReducedMotion()) {
      stopLoop();
      snapCapsuleToTargets();
      renderOnce();
    } else if (!isPaused) {
      scheduleNextFrame();
    }
  });

  if (!isReducedMotion() && !isPaused) {
    scheduleNextFrame();
  }

  return {
    setPaused,
    setTheme() {},
    destroy() {
      stopLoop();
      window.removeEventListener('resize', onResize);
      window.removeEventListener('scroll', onScroll);
      capGeo.dispose();
      textGeo.dispose();
      haloGeo.dispose();
      chromeMat.dispose();
      textMat.dispose();
      haloMat.dispose();
      matcapTexture.dispose();
      textTexture.dispose();
      haloTexture.dispose();
      renderer?.dispose();
    }
  };
}

export function rotateCapsuleToTrack(index) {
  if (!capsuleMesh) return;
  // Subtle interactive nod when hovering track cards
  targetRotX = 0.14;
  setTimeout(() => {
    targetRotX = 0.08;
  }, 400);
}
