"use strict";

/* ValVuln AI — Lightweight WebGL Wireframe & Voxel Isolation Scene
 * Architectural flow: [01 Scope Gate] -> [02 Worker Sandbox] -> [03 Target Lab]
 * Zero external dependencies, CSP 'self' compatible, adaptive 3-tier fallback.
 */
(function (root) {
  function probeWebGLSupport() {
    try {
      const c = document.createElement("canvas");
      const opts = { antialias: true, alpha: false, powerPreference: "high-performance" };
      return Boolean(c.getContext("webgl2", opts) || c.getContext("webgl", opts));
    } catch {
      return false;
    }
  }

  function detectTier() {
    const reduced = Boolean(root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches);
    const saveData = Boolean(navigator.connection && navigator.connection.saveData);
    if (reduced || saveData) {
      return { tier: "css3d-fallback", reason: reduced ? "reduced-motion" : "save-data", dpr: 1 };
    }
    if (!probeWebGLSupport()) {
      return { tier: "css3d-fallback", reason: "no-webgl", dpr: 1 };
    }
    const cores = navigator.hardwareConcurrency || 8;
    const mem = navigator.deviceMemory || 8;
    const compact = root.innerWidth <= 760;
    if (cores <= 4 || mem <= 4 || compact) {
      return { tier: "webgl-lite", reason: compact ? "compact-viewport" : "constrained-device", dpr: 1 };
    }
    return { tier: "webgl-full", reason: "capable-device", dpr: Math.min(root.devicePixelRatio || 1, 2) };
  }

  const PALETTES = {
    dark: {
      clear: [10 / 255, 10 / 255, 12 / 255],
      surface: [20 / 255, 20 / 255, 24 / 255],
      raised: [31 / 255, 32 / 255, 38 / 255],
      wire: [74 / 255, 76 / 255, 86 / 255],
      wireDim: [42 / 255, 43 / 255, 50 / 255],
      accent: [34 / 255, 211 / 255, 238 / 255],
      accentSoft: [20 / 255, 118 / 255, 134 / 255],
      aiNeutral: [120 / 255, 124 / 255, 136 / 255]
    },
    light: {
      clear: [244 / 255, 244 / 255, 245 / 255],
      surface: [255 / 255, 255 / 255, 255 / 255],
      raised: [228 / 255, 228 / 255, 231 / 255],
      wire: [113 / 255, 113 / 255, 122 / 255],
      wireDim: [200 / 255, 200 / 255, 208 / 255],
      accent: [14 / 255, 116 / 255, 144 / 255],
      accentSoft: [74 / 255, 152 / 255, 174 / 255],
      aiNeutral: [102 / 255, 104 / 255, 114 / 255]
    }
  };

  function compileShader(gl, type, src) {
    const sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      gl.deleteShader(sh);
      return null;
    }
    return sh;
  }

  function createProgram(gl, vsSrc, fsSrc) {
    const vs = compileShader(gl, gl.VERTEX_SHADER, vsSrc);
    const fs = compileShader(gl, gl.FRAGMENT_SHADER, fsSrc);
    if (!vs || !fs) return null;
    const prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.bindAttribLocation(prog, 0, "aPos");
    gl.linkProgram(prog);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      gl.deleteProgram(prog);
      return null;
    }
    return prog;
  }

  function norm3(v) {
    const len = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / len, v[1] / len, v[2] / len];
  }

  function cross3(a, b) {
    return [
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0]
    ];
  }

  function dot3(a, b) {
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  }

  function mat4Perspective(out, fov, aspect, near, far) {
    const f = 1.0 / Math.tan(fov * 0.5);
    const nf = 1.0 / (near - far);
    out.fill(0);
    out[0] = f / aspect;
    out[5] = f;
    out[10] = (far + near) * nf;
    out[11] = -1;
    out[14] = 2 * far * near * nf;
    return out;
  }

  function mat4LookAt(out, eye, target, up) {
    const z = norm3([eye[0] - target[0], eye[1] - target[1], eye[2] - target[2]]);
    const x = norm3(cross3(up, z));
    const y = cross3(z, x);
    out[0] = x[0]; out[1] = y[0]; out[2] = z[0]; out[3] = 0;
    out[4] = x[1]; out[5] = y[1]; out[6] = z[1]; out[7] = 0;
    out[8] = x[2]; out[9] = y[2]; out[10] = z[2]; out[11] = 0;
    out[12] = -dot3(x, eye);
    out[13] = -dot3(y, eye);
    out[14] = -dot3(z, eye);
    out[15] = 1;
    return out;
  }

  function mat4Mul(out, a, b) {
    for (let col = 0; col < 4; col++) {
      const b0 = b[col * 4];
      const b1 = b[col * 4 + 1];
      const b2 = b[col * 4 + 2];
      const b3 = b[col * 4 + 3];
      for (let row = 0; row < 4; row++) {
        out[col * 4 + row] =
          a[row] * b0 +
          a[4 + row] * b1 +
          a[8 + row] * b2 +
          a[12 + row] * b3;
      }
    }
    return out;
  }

  function mat4Box(out, tx, ty, tz, sx, sy, sz) {
    out.fill(0);
    out[0] = sx;
    out[5] = sy;
    out[10] = sz;
    out[12] = tx;
    out[13] = ty;
    out[14] = tz;
    out[15] = 1;
    return out;
  }

  function buildUnitCubeTriangles() {
    // 6 faces * 2 triangles * 3 vertices, each vertex: x, y, z, nx, ny, nz
    const faces = [
      [[0, 0, 1], [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]],
      [[0, 0, -1], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5]],
      [[1, 0, 0], [0.5, -0.5, 0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5]],
      [[-1, 0, 0], [-0.5, -0.5, -0.5], [-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], [-0.5, 0.5, -0.5]],
      [[0, 1, 0], [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5]],
      [[0, -1, 0], [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5]]
    ];
    const data = [];
    faces.forEach(([n, a, b, c, d]) => {
      [a, b, c, a, c, d].forEach(p => {
        data.push(p[0], p[1], p[2], n[0], n[1], n[2]);
      });
    });
    return new Float32Array(data);
  }

  function buildUnitCubeEdges() {
    const p = [
      [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5],
      [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]
    ];
    const idx = [0, 1, 1, 2, 2, 3, 3, 0, 4, 5, 5, 6, 6, 7, 7, 4, 0, 4, 1, 5, 2, 6, 3, 7];
    const out = [];
    idx.forEach(i => out.push(p[i][0], p[i][1], p[i][2]));
    return new Float32Array(out);
  }

  function pushSeg(arr, x1, y1, z1, x2, y2, z2) {
    arr.push(x1, y1, z1, x2, y2, z2);
  }

  function buildDatumLines(isLite) {
    const arr = [];
    const y = -0.92;
    // Outer architectural perimeter
    pushSeg(arr, -3.55, y, -1.25, 3.55, y, -1.25);
    pushSeg(arr, 3.55, y, -1.25, 3.55, y, 1.25);
    pushSeg(arr, 3.55, y, 1.25, -3.55, y, 1.25);
    pushSeg(arr, -3.55, y, 1.25, -3.55, y, -1.25);
    // Isolation bay dividers
    pushSeg(arr, -1.16, y, -1.25, -1.16, y, 1.25);
    pushSeg(arr, 1.16, y, -1.25, 1.16, y, 1.25);
    if (!isLite) {
      // Hairline blueprint grid rails
      for (let gx = -3.0; gx <= 3.01; gx += 0.6) {
        pushSeg(arr, gx, y, -1.25, gx, y, 1.25);
      }
      for (let gz = -0.75; gz <= 0.76; gz += 0.5) {
        pushSeg(arr, -3.55, y, gz, 3.55, y, gz);
      }
    }
    // Primary execution conduit rail (Scope Gate -> Worker -> Lab)
    pushSeg(arr, -1.68, -0.04, 0, -1.16, -0.04, 0);
    pushSeg(arr, -1.16, -0.04, 0, -0.72, -0.04, 0);
    pushSeg(arr, 0.72, -0.04, 0, 1.16, -0.04, 0);
    pushSeg(arr, 1.16, -0.04, 0, 1.68, -0.04, 0);
    // Return verification telemetry rail along datum level
    pushSeg(arr, 2.35, -0.58, 0.55, 2.35, -0.78, 0.55);
    pushSeg(arr, 2.35, -0.78, 0.55, -2.35, -0.78, 0.55);
    pushSeg(arr, -2.35, -0.78, 0.55, -2.35, -0.58, 0.55);
    // Isolated dashed vertical channel from floating Triage AI (text-only) to Scope Gate
    for (let dy = 0.24; dy < 0.72; dy += 0.14) {
      pushSeg(arr, -2.35, dy, 0, -2.35, dy + 0.07, 0);
    }
    return new Float32Array(arr);
  }

  function buildGateLines() {
    const arr = [];
    [-1.16, 1.16].forEach(gx => {
      pushSeg(arr, gx, -0.84, -0.94, gx, 0.76, -0.94);
      pushSeg(arr, gx, 0.76, -0.94, gx, 0.76, 0.94);
      pushSeg(arr, gx, 0.76, 0.94, gx, -0.84, 0.94);
      pushSeg(arr, gx, -0.84, 0.94, gx, -0.84, -0.94);
      // Crossed policy gate notch around conduit portal
      pushSeg(arr, gx, -0.26, -0.22, gx, 0.18, -0.22);
      pushSeg(arr, gx, 0.18, -0.22, gx, 0.18, 0.22);
      pushSeg(arr, gx, 0.18, 0.22, gx, -0.26, 0.22);
      pushSeg(arr, gx, -0.26, 0.22, gx, -0.26, -0.22);
    });
    return new Float32Array(arr);
  }

  const SOLID_VS =
    "attribute vec3 aPos; attribute vec3 aNorm;" +
    "uniform mat4 uMvp; varying vec3 vNorm;" +
    "void main(){ vNorm = aNorm; gl_Position = uMvp * vec4(aPos, 1.0); }";

  const SOLID_FS =
    "precision mediump float;" +
    "varying vec3 vNorm; uniform vec3 uColor;" +
    "void main(){" +
    "  vec3 lightDir = normalize(vec3(0.45, 0.85, 0.55));" +
    "  float diff = 0.82 + 0.18 * max(dot(normalize(vNorm), lightDir), 0.0);" +
    "  gl_FragColor = vec4(uColor * diff, 1.0);" +
    "}";

  const LINE_VS =
    "attribute vec3 aPos; uniform mat4 uMvp;" +
    "void main(){ gl_Position = uMvp * vec4(aPos, 1.0); }";

  const LINE_FS =
    "precision mediump float; uniform vec3 uColor;" +
    "void main(){ gl_FragColor = vec4(uColor, 1.0); }";

  function mount(canvas, options = {}) {
    if (!canvas) return null;
    const tierInfo = options.tierInfo || detectTier();
    if (tierInfo.tier === "css3d-fallback") return null;

    const ctxOpts = { antialias: true, alpha: false, depth: true, powerPreference: "high-performance" };
    let gl = canvas.getContext("webgl2", ctxOpts);
    let contextType = "webgl2";
    if (!gl) {
      gl = canvas.getContext("webgl", ctxOpts);
      contextType = "webgl";
    }
    if (!gl) return null;

    const solidProg = createProgram(gl, SOLID_VS, SOLID_FS);
    const lineProg = createProgram(gl, LINE_VS, LINE_FS);
    if (!solidProg || !lineProg) return null;

    const isLite = tierInfo.tier === "webgl-lite";
    const cubeVerts = buildUnitCubeTriangles();
    const edgeVerts = buildUnitCubeEdges();
    const datumVerts = buildDatumLines(isLite);
    const gateVerts = buildGateLines();

    const makeBuf = data => {
      const b = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      return b;
    };

    const cubeBuf = makeBuf(cubeVerts);
    const edgeBuf = makeBuf(edgeVerts);
    const datumBuf = makeBuf(datumVerts);
    const gateBuf = makeBuf(gateVerts);

    const sLoc = {
      pos: gl.getAttribLocation(solidProg, "aPos"),
      norm: gl.getAttribLocation(solidProg, "aNorm"),
      mvp: gl.getUniformLocation(solidProg, "uMvp"),
      color: gl.getUniformLocation(solidProg, "uColor")
    };
    const lLoc = {
      pos: gl.getAttribLocation(lineProg, "aPos"),
      mvp: gl.getUniformLocation(lineProg, "uMvp"),
      color: gl.getUniformLocation(lineProg, "uColor")
    };

    const state = {
      theme: options.theme === "light" ? "light" : "dark",
      activeLayer: Number(options.activeLayer) || 0,
      paused: Boolean(options.paused),
      destroyed: false,
      rafId: 0,
      yaw: -0.46,
      pitch: 0.44,
      targetYaw: -0.46,
      targetPitch: 0.44,
      focusX: -2.35,
      targetFocusX: -2.35,
      dragging: false,
      dragX: 0,
      dragY: 0,
      simTime: 0,
      lastTs: 0,
      fpsCount: 0,
      fpsTimer: 0,
      fps: 60,
      width: 1,
      height: 1
    };

    const layerFocusX = [-2.35, 0.0, 2.35];
    const layerYaws = [-0.38, -0.48, -0.58];

    const proj = new Float32Array(16);
    const view = new Float32Array(16);
    const vp = new Float32Array(16);
    const model = new Float32Array(16);
    const mvp = new Float32Array(16);

    function resize() {
      if (state.destroyed) return;
      const rect = canvas.getBoundingClientRect();
      const dpr = tierInfo.dpr;
      const w = Math.max(1, Math.round(rect.width * dpr));
      const h = Math.max(1, Math.round(rect.height * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      state.width = w;
      state.height = h;
      gl.viewport(0, 0, w, h);
    }

    function drawBoxSolid(tx, ty, tz, sx, sy, sz, color) {
      mat4Box(model, tx, ty, tz, sx, sy, sz);
      mat4Mul(mvp, vp, model);
      gl.uniformMatrix4fv(sLoc.mvp, false, mvp);
      gl.uniform3fv(sLoc.color, color);
      gl.drawArrays(gl.TRIANGLES, 0, 36);
    }

    function drawBoxWire(tx, ty, tz, sx, sy, sz, color) {
      mat4Box(model, tx, ty, tz, sx, sy, sz);
      mat4Mul(mvp, vp, model);
      gl.uniformMatrix4fv(lLoc.mvp, false, mvp);
      gl.uniform3fv(lLoc.color, color);
      gl.drawArrays(gl.LINES, 0, 24);
    }

    function renderFrame(ts) {
      if (state.destroyed) return;
      const dt = state.lastTs ? Math.min(0.05, (ts - state.lastTs) / 1000) : 0.016;
      state.lastTs = ts;

      if (!state.paused) {
        state.simTime += dt;
        state.fpsCount++;
        state.fpsTimer += dt;
        if (state.fpsTimer >= 0.5) {
          state.fps = Math.round(state.fpsCount / state.fpsTimer);
          state.fpsCount = 0;
          state.fpsTimer = 0;
        }
      }

      const damp = 1 - Math.exp(-dt * 6.5);
      state.yaw += (state.targetYaw - state.yaw) * damp;
      state.pitch += (state.targetPitch - state.pitch) * damp;
      state.focusX += (state.targetFocusX - state.focusX) * damp;

      const aspect = Math.max(0.5, state.width / state.height);
      const dist = aspect < 1.05 ? 10.6 : 8.7;
      const eyeX = state.focusX * 0.24 + Math.sin(state.yaw) * Math.cos(state.pitch) * dist;
      const eyeY = 0.35 + Math.sin(state.pitch) * dist;
      const eyeZ = Math.cos(state.yaw) * Math.cos(state.pitch) * dist;

      mat4Perspective(proj, (34 * Math.PI) / 180, aspect, 0.1, 40.0);
      mat4LookAt(view, [eyeX, eyeY, eyeZ], [state.focusX * 0.24, -0.08, 0], [0, 1, 0]);
      mat4Mul(vp, proj, view);

      const pal = PALETTES[state.theme];
      gl.clearColor(pal.clear[0], pal.clear[1], pal.clear[2], 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);
      gl.depthFunc(gl.LEQUAL);
      gl.enable(gl.CULL_FACE);

      // 1. Solid voxel prisms with subtle polygon offset to eliminate edge z-fighting
      gl.useProgram(solidProg);
      gl.bindBuffer(gl.ARRAY_BUFFER, cubeBuf);
      gl.enableVertexAttribArray(sLoc.pos);
      gl.vertexAttribPointer(sLoc.pos, 3, gl.FLOAT, false, 24, 0);
      gl.enableVertexAttribArray(sLoc.norm);
      gl.vertexAttribPointer(sLoc.norm, 3, gl.FLOAT, false, 24, 12);
      gl.enable(gl.POLYGON_OFFSET_FILL);
      gl.polygonOffset(1.0, 1.0);

      const active = state.activeLayer;
      const pulsePhase = (state.simTime * 0.42) % 1.0;

      // Chamber 01: Scope Gate core + isolated Triage AI upper text block
      drawBoxSolid(-2.35, -0.22, 0, 0.92, 0.98, 0.92, active === 0 ? pal.raised : pal.surface);
      drawBoxSolid(-2.35, 0.94, 0, 0.46, 0.24, 0.46, pal.surface);

      // Chamber 02: Worker Sandbox twin session monoliths (Account A & Account B)
      const hoverA = isLite ? 0 : Math.sin(state.simTime * 1.4) * 0.03;
      const hoverB = isLite ? 0 : Math.sin(state.simTime * 1.4 + 2.2) * 0.03;
      drawBoxSolid(-0.34, -0.18 + hoverA, 0, 0.46, 0.92, 0.72, active === 1 ? pal.raised : pal.surface);
      drawBoxSolid(0.34, -0.18 + hoverB, 0, 0.46, 0.92, 0.72, active === 1 ? pal.raised : pal.surface);

      // Chamber 03: Target Lab stepped 3 paths (BAC-08, XSS-08, UP-04) + Negative Control node
      drawBoxSolid(2.05, -0.52, -0.22, 0.44, 0.62, 0.44, active === 2 ? pal.raised : pal.surface);
      drawBoxSolid(2.42, -0.34, 0.14, 0.44, 0.96, 0.44, active === 2 ? pal.raised : pal.surface);
      drawBoxSolid(2.74, -0.45, -0.12, 0.34, 0.74, 0.34, pal.surface);

      // Deterministic verification packet moving forward Scope -> Worker -> Target
      const forwardX = -1.68 + pulsePhase * 3.36;
      drawBoxSolid(forwardX, -0.04, 0, 0.11, 0.11, 0.11, pal.accent);

      // Verdict telemetry packet returning Target -> Scope along lower datum channel
      const returnX = 2.35 - ((pulsePhase + 0.5) % 1.0) * 4.7;
      drawBoxSolid(returnX, -0.78, 0.55, 0.09, 0.09, 0.09, pal.accentSoft);

      gl.disable(gl.POLYGON_OFFSET_FILL);
      if (sLoc.norm >= 0) gl.disableVertexAttribArray(sLoc.norm);

      // 2. Crisp orthogonal wireframe lines
      gl.useProgram(lineProg);
      gl.disable(gl.CULL_FACE);

      // Static datum rails
      gl.bindBuffer(gl.ARRAY_BUFFER, datumBuf);
      gl.enableVertexAttribArray(lLoc.pos);
      gl.vertexAttribPointer(lLoc.pos, 3, gl.FLOAT, false, 12, 0);
      gl.uniformMatrix4fv(lLoc.mvp, false, vp);
      gl.uniform3fv(lLoc.color, pal.wireDim);
      gl.drawArrays(gl.LINES, 0, datumVerts.length / 3);

      // Isolation Firewall Boundaries
      gl.bindBuffer(gl.ARRAY_BUFFER, gateBuf);
      gl.vertexAttribPointer(lLoc.pos, 3, gl.FLOAT, false, 12, 0);
      gl.uniform3fv(lLoc.color, active === 1 ? pal.accent : pal.wire);
      gl.drawArrays(gl.LINES, 0, gateVerts.length / 3);

      // Outer Chamber Cages + Solid Block Edges
      gl.bindBuffer(gl.ARRAY_BUFFER, edgeBuf);
      gl.vertexAttribPointer(lLoc.pos, 3, gl.FLOAT, false, 12, 0);

      // Chamber 01 Cage + Core Wire + Floating Triage AI Cage
      drawBoxWire(-2.35, -0.14, 0, 1.38, 1.54, 1.38, active === 0 ? pal.accent : pal.wire);
      drawBoxWire(-2.35, -0.22, 0, 0.92, 0.98, 0.92, active === 0 ? pal.accentSoft : pal.wire);
      drawBoxWire(-2.35, 0.94, 0, 0.46, 0.24, 0.46, pal.aiNeutral);

      // Chamber 02 Twin Worker Cage + Sub-session Wireframes
      drawBoxWire(0.0, -0.12, 0, 1.54, 1.58, 1.46, active === 1 ? pal.accent : pal.wire);
      drawBoxWire(-0.34, -0.18 + hoverA, 0, 0.46, 0.92, 0.72, active === 1 ? pal.accent : pal.wire);
      drawBoxWire(0.34, -0.18 + hoverB, 0, 0.46, 0.92, 0.72, active === 1 ? pal.accent : pal.wire);

      // Chamber 03 Target Lab Cage + 3 Vulnerability Voxel Steps
      drawBoxWire(2.38, -0.16, 0, 1.44, 1.48, 1.36, active === 2 ? pal.accent : pal.wire);
      drawBoxWire(2.05, -0.52, -0.22, 0.44, 0.62, 0.44, active === 2 ? pal.accent : pal.wire);
      drawBoxWire(2.42, -0.34, 0.14, 0.44, 0.96, 0.44, active === 2 ? pal.accent : pal.wire);
      drawBoxWire(2.74, -0.45, -0.12, 0.34, 0.74, 0.34, pal.wire);

      if (!state.paused) {
        state.rafId = root.requestAnimationFrame(renderFrame);
      }
    }

    function scheduleLoop() {
      if (state.destroyed || state.paused || state.rafId) return;
      state.lastTs = 0;
      state.rafId = root.requestAnimationFrame(renderFrame);
    }

    const onPointerDown = e => {
      state.dragging = true;
      state.dragX = e.clientX;
      state.dragY = e.clientY;
    };
    const onPointerMove = e => {
      if (!state.dragging) return;
      const dx = e.clientX - state.dragX;
      const dy = e.clientY - state.dragY;
      state.dragX = e.clientX;
      state.dragY = e.clientY;
      state.targetYaw = Math.max(-1.15, Math.min(0.45, state.targetYaw + dx * 0.0055));
      state.targetPitch = Math.max(0.18, Math.min(0.85, state.targetPitch + dy * 0.0045));
    };
    const onPointerUp = () => {
      state.dragging = false;
    };
    const onContextLost = e => {
      e.preventDefault();
      state.paused = true;
      if (state.rafId) {
        root.cancelAnimationFrame(state.rafId);
        state.rafId = 0;
      }
      if (typeof options.onContextLost === "function") options.onContextLost();
    };

    canvas.addEventListener("pointerdown", onPointerDown);
    root.addEventListener("pointermove", onPointerMove, { passive: true });
    root.addEventListener("pointerup", onPointerUp, { passive: true });
    canvas.addEventListener("webglcontextlost", onContextLost);

    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(() => {
      resize();
      if (state.paused && !state.destroyed) renderFrame(performance.now());
    }) : null;
    if (ro) ro.observe(canvas);

    resize();
    renderFrame(performance.now());
    if (!state.paused) scheduleLoop();

    return {
      setActiveLayer(idx) {
        const safe = Math.max(0, Math.min(2, Number(idx) || 0));
        state.activeLayer = safe;
        state.targetFocusX = layerFocusX[safe];
        if (!state.dragging) state.targetYaw = layerYaws[safe];
        if (state.paused && !state.destroyed) renderFrame(performance.now());
      },
      resetCamera() {
        state.targetFocusX = layerFocusX[state.activeLayer];
        state.targetYaw = layerYaws[state.activeLayer];
        state.targetPitch = 0.44;
        if (state.paused && !state.destroyed) renderFrame(performance.now());
      },
      setTheme(theme) {
        state.theme = theme === "light" ? "light" : "dark";
        if (state.paused && !state.destroyed) renderFrame(performance.now());
      },
      setPaused(paused) {
        const next = Boolean(paused);
        if (state.paused === next) return;
        state.paused = next;
        if (next) {
          if (state.rafId) {
            root.cancelAnimationFrame(state.rafId);
            state.rafId = 0;
          }
        } else {
          scheduleLoop();
        }
      },
      resize,
      getStats() {
        return {
          tier: tierInfo.tier,
          reason: tierInfo.reason,
          dpr: tierInfo.dpr,
          contextType,
          paused: state.paused,
          fps: state.fps,
          activeLayer: state.activeLayer
        };
      },
      destroy() {
        if (state.destroyed) return;
        state.destroyed = true;
        if (state.rafId) root.cancelAnimationFrame(state.rafId);
        if (ro) ro.disconnect();
        canvas.removeEventListener("pointerdown", onPointerDown);
        root.removeEventListener("pointermove", onPointerMove);
        root.removeEventListener("pointerup", onPointerUp);
        canvas.removeEventListener("webglcontextlost", onContextLost);
        gl.deleteBuffer(cubeBuf);
        gl.deleteBuffer(edgeBuf);
        gl.deleteBuffer(datumBuf);
        gl.deleteBuffer(gateBuf);
        gl.deleteProgram(solidProg);
        gl.deleteProgram(lineProg);
      }
    };
  }

  root.ValVulnMonolithScene = { detectTier, mount };
})(window);
