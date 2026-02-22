from flask import Flask, render_template_string, request, jsonify
import os, uuid, base64
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import io

app = Flask(__name__)


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>$israelify – Israelification Machine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Rubik:wght@300;400;500;700;900&display=swap" rel="stylesheet"/>
  <style>
    :root {
      --blue: #0038b8;
      --blue-mid: #1a5dcc;
      --blue-light: #4a90d9;
      --blue-pale: #d4e6f8;
      --white: #ffffff;
      --off-white: #f4f8ff;
      --gold: #ffd700;
      --text-dark: #0a1628;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Rubik', sans-serif;
      background: var(--off-white);
      color: var(--text-dark);
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* ── Animated flag background ── */
    .flag-bg {
      position: fixed;
      inset: 0;
      z-index: 0;
      background: var(--white);
      overflow: hidden;
    }
    .flag-bg::before,
    .flag-bg::after {
      content: '';
      position: absolute;
      left: 0; right: 0;
      height: 15%;
      background: var(--blue);
      animation: stripe-pulse 4s ease-in-out infinite;
    }
    .flag-bg::before { top: 0; }
    .flag-bg::after  { bottom: 0; }

    @keyframes stripe-pulse {
      0%, 100% { opacity: 0.12; }
      50%       { opacity: 0.22; }
    }

    /* floating stars */
    .stars-bg {
      position: fixed;
      inset: 0;
      z-index: 0;
      pointer-events: none;
    }
    .star {
      position: absolute;
      opacity: 0;
      animation: float-star 8s infinite;
      font-size: 20px;
      color: var(--blue);
    }
    @keyframes float-star {
      0%   { opacity: 0; transform: translateY(100vh) rotate(0deg); }
      10%  { opacity: 0.15; }
      90%  { opacity: 0.12; }
      100% { opacity: 0; transform: translateY(-10vh) rotate(360deg); }
    }

    /* ── Layout ── */
    .wrapper {
      position: relative;
      z-index: 1;
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 24px 80px;
    }

    /* ── Header ── */
    header {
      text-align: center;
      padding: 48px 20px 32px;
    }

    .logo-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      margin-bottom: 10px;
    }

    .logo-star {
      font-size: 48px;
      animation: spin-star 20s linear infinite;
      display: inline-block;
    }
    @keyframes spin-star {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }

    h1 {
      font-family: 'Black Han Sans', sans-serif;
      font-size: clamp(52px, 9vw, 96px);
      letter-spacing: -2px;
      background: linear-gradient(135deg, var(--blue) 0%, var(--blue-light) 50%, var(--blue) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      line-height: 0.95;
      filter: drop-shadow(0 4px 24px rgba(0,56,184,0.25));
    }

    h1 .dollar {
      -webkit-text-fill-color: var(--gold);
      filter: drop-shadow(0 0 12px rgba(255,215,0,0.6));
    }

    .tagline {
      font-size: clamp(13px, 2vw, 17px);
      color: var(--blue-mid);
      font-weight: 500;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      margin-top: 12px;
      opacity: 0.9;
    }

    /* ── CA Banner ── */
    .ca-banner {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      background: var(--blue);
      color: var(--white);
      border-radius: 50px;
      padding: 8px 20px;
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.05em;
      margin-top: 20px;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 4px 20px rgba(0,56,184,0.35);
      position: relative;
    }
    .ca-banner:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,56,184,0.45); }
    .ca-banner .ca-label { opacity: 0.7; font-size: 10px; letter-spacing: 0.1em; }
    .ca-banner .ca-value { font-family: monospace; font-size: 11px; }
    .ca-banner .copy-tip {
      position: absolute;
      top: -34px; left: 50%; transform: translateX(-50%);
      background: var(--text-dark);
      color: white;
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 6px;
      white-space: nowrap;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s;
    }
    .ca-banner.copied .copy-tip { opacity: 1; }

    /* ── Social Links ── */
    .social-row {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-top: 16px;
    }
    .social-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 18px;
      border-radius: 50px;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s;
      border: 2px solid var(--blue);
      color: var(--blue);
    }
    .social-link:hover { background: var(--blue); color: white; transform: translateY(-2px); }
    .social-link.filled { background: var(--blue); color: white; }
    .social-link.filled:hover { background: var(--blue-mid); }

    /* ── Main Card ── */
    .card {
      background: white;
      border-radius: 28px;
      box-shadow: 0 8px 60px rgba(0, 56, 184, 0.12), 0 2px 8px rgba(0,0,0,0.06);
      overflow: hidden;
      margin-top: 40px;
      border: 1px solid rgba(0, 56, 184, 0.1);
    }

    .card-header {
      background: linear-gradient(135deg, var(--blue) 0%, #1a5dcc 100%);
      padding: 28px 36px;
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .card-header h2 {
      font-family: 'Black Han Sans', sans-serif;
      color: white;
      font-size: 26px;
      letter-spacing: 0.02em;
    }
    .card-header .step-num {
      background: rgba(255,255,255,0.2);
      color: white;
      width: 36px; height: 36px;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-weight: 900;
      font-size: 16px;
      border: 2px solid rgba(255,255,255,0.4);
    }

    .card-body { padding: 36px; }

    /* ── Upload Zone ── */
    .upload-zone {
      border: 3px dashed rgba(0, 56, 184, 0.3);
      border-radius: 20px;
      padding: 60px 40px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s;
      background: var(--off-white);
      position: relative;
      overflow: hidden;
    }
    .upload-zone::before {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, rgba(0,56,184,0.03), rgba(74,144,217,0.06));
      opacity: 0;
      transition: opacity 0.3s;
    }
    .upload-zone:hover, .upload-zone.drag-over {
      border-color: var(--blue);
      transform: scale(1.01);
      box-shadow: 0 8px 40px rgba(0,56,184,0.15);
    }
    .upload-zone:hover::before, .upload-zone.drag-over::before { opacity: 1; }

    .upload-icon {
      font-size: 64px;
      display: block;
      margin-bottom: 16px;
      animation: bob 2.5s ease-in-out infinite;
    }
    @keyframes bob {
      0%, 100% { transform: translateY(0); }
      50%       { transform: translateY(-8px); }
    }
    .upload-title {
      font-size: 20px;
      font-weight: 700;
      color: var(--blue);
      margin-bottom: 8px;
    }
    .upload-sub {
      font-size: 14px;
      color: #888;
    }
    .upload-btn {
      display: inline-block;
      margin-top: 20px;
      padding: 12px 32px;
      background: var(--blue);
      color: white;
      border-radius: 50px;
      font-weight: 700;
      font-size: 15px;
      transition: all 0.2s;
      box-shadow: 0 4px 16px rgba(0,56,184,0.3);
    }
    .upload-zone:hover .upload-btn { background: var(--blue-mid); transform: scale(1.05); }
    #file-input { display: none; }

    /* ── Preview Grid ── */
    .preview-section { margin-top: 36px; display: none; }
    .preview-section.show { display: block; }
    .preview-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }
    @media (max-width: 600px) { .preview-grid { grid-template-columns: 1fr; } }

    .preview-pane {
      border-radius: 16px;
      overflow: hidden;
      border: 2px solid rgba(0,56,184,0.15);
      background: #f0f5ff;
      position: relative;
    }
    .preview-pane-label {
      position: absolute;
      top: 12px; left: 12px;
      background: rgba(0,0,0,0.6);
      color: white;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 4px 10px;
      border-radius: 20px;
      backdrop-filter: blur(4px);
    }
    .preview-pane img {
      width: 100%;
      display: block;
      object-fit: contain;
      max-height: 400px;
    }

    /* ── Transform Button ── */
    .transform-btn-wrap {
      text-align: center;
      margin-top: 28px;
    }
    .transform-btn {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 18px 52px;
      background: linear-gradient(135deg, var(--blue) 0%, var(--blue-mid) 100%);
      color: white;
      border: none;
      border-radius: 60px;
      font-size: 18px;
      font-family: 'Black Han Sans', sans-serif;
      letter-spacing: 0.05em;
      cursor: pointer;
      transition: all 0.3s;
      box-shadow: 0 6px 32px rgba(0,56,184,0.4);
      position: relative;
      overflow: hidden;
    }
    .transform-btn::before {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.2));
      opacity: 0;
      transition: opacity 0.3s;
    }
    .transform-btn:hover { transform: translateY(-3px); box-shadow: 0 12px 48px rgba(0,56,184,0.5); }
    .transform-btn:hover::before { opacity: 1; }
    .transform-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    .transform-btn .btn-star { font-size: 22px; }

    /* ── Loading ── */
    .loading-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(8px);
      z-index: 1000;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 24px;
    }
    .loading-overlay.show { display: flex; }
    .loading-star {
      font-size: 72px;
      animation: spin-star 1s linear infinite;
    }
    .loading-text {
      font-family: 'Black Han Sans', sans-serif;
      font-size: 28px;
      color: var(--blue);
      letter-spacing: 0.05em;
    }
    .loading-sub {
      font-size: 15px;
      color: #888;
      animation: pulse-text 1.5s ease-in-out infinite;
    }
    @keyframes pulse-text {
      0%, 100% { opacity: 0.6; }
      50%       { opacity: 1; }
    }
    .progress-bar {
      width: 280px;
      height: 6px;
      background: var(--blue-pale);
      border-radius: 10px;
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--blue), var(--blue-light));
      border-radius: 10px;
      animation: progress-anim 2s ease-in-out infinite;
    }
    @keyframes progress-anim {
      0%   { width: 0%; }
      50%  { width: 80%; }
      100% { width: 95%; }
    }

    /* ── Download ── */
    .download-section {
      display: none;
      margin-top: 28px;
      text-align: center;
    }
    .download-section.show { display: block; }
    .download-btn {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 16px 44px;
      background: linear-gradient(135deg, #059669, #10b981);
      color: white;
      border-radius: 50px;
      font-size: 17px;
      font-weight: 700;
      text-decoration: none;
      transition: all 0.2s;
      box-shadow: 0 6px 24px rgba(5,150,105,0.35);
    }
    .download-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 36px rgba(5,150,105,0.5); }
    .success-msg {
      margin-top: 12px;
      font-size: 14px;
      color: #059669;
      font-weight: 600;
    }

    /* ── Error ── */
    .error-msg {
      display: none;
      margin-top: 16px;
      padding: 14px 20px;
      background: #fff0f0;
      border: 1px solid #fca5a5;
      border-radius: 12px;
      color: #dc2626;
      font-size: 14px;
    }
    .error-msg.show { display: block; }

    /* ── Info Section ── */
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
      margin-top: 48px;
    }
    .info-card {
      background: white;
      border-radius: 20px;
      padding: 28px 24px;
      text-align: center;
      border: 1px solid rgba(0,56,184,0.1);
      box-shadow: 0 4px 20px rgba(0,56,184,0.06);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .info-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0,56,184,0.14); }
    .info-card-icon { font-size: 40px; margin-bottom: 12px; display: block; }
    .info-card-title { font-weight: 800; font-size: 16px; color: var(--blue); margin-bottom: 6px; }
    .info-card-text { font-size: 13px; color: #666; line-height: 1.5; }

    /* ── Footer ── */
    footer {
      text-align: center;
      padding: 40px 20px 20px;
      position: relative;
      z-index: 1;
      font-size: 13px;
      color: #aaa;
    }
    footer strong { color: var(--blue); }

    /* ── Divider ── */
    .divider {
      text-align: center;
      margin: 40px 0;
      position: relative;
    }
    .divider::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 0; right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(0,56,184,0.2), transparent);
    }
    .divider span {
      position: relative;
      background: var(--off-white);
      padding: 0 16px;
      font-size: 22px;
    }

    /* Reset button */
    .reset-btn {
      display: none;
      margin: 12px auto 0;
      padding: 8px 24px;
      border: 2px solid var(--blue);
      background: transparent;
      color: var(--blue);
      border-radius: 50px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .reset-btn.show { display: inline-block; }
    .reset-btn:hover { background: var(--blue); color: white; }

    /* Confetti canvas */
    #confetti-canvas {
      position: fixed;
      inset: 0;
      z-index: 999;
      pointer-events: none;
    }
  </style>
</head>
<body>

<canvas id="confetti-canvas"></canvas>

<div class="flag-bg"></div>
<div class="stars-bg" id="starsContainer"></div>

<div class="wrapper">

  <!-- Header -->
  <header>
    <div class="logo-row">
      <span class="logo-star">✡</span>
      <h1><span class="dollar">$</span>israelify</h1>
      <span class="logo-star">✡</span>
    </div>
    <p class="tagline">Israelification is the process of jewifying every meme</p>

    <!-- CA Badge -->
    <div class="ca-banner" id="caBanner" onclick="copyCa()">
      <span class="ca-label">CA</span>
      <span class="ca-value">HnWQXCVE84dGc2AQxNwK1DdR3NgYqLHQTnFkh6ddpump</span>
      <span>📋</span>
      <span class="copy-tip">Copied!</span>
    </div>

    <!-- Social Links -->
    <div class="social-row">
      <a href="https://x.com/i/communities/2025256544208617787" target="_blank" class="social-link filled">
        𝕏 Community
      </a>
      <a href="https://dexscreener.com/solana/5jyzm6eqtwusxydazmnl9rrughbda8xcpv8w6udkfaxb" class="social-link">
        🚀 Buy $israelify
      </a>
    </div>
  </header>

  <!-- Main Transform Card -->
  <div class="card">
    <div class="card-header">
      <div class="step-num">✡</div>
      <h2>ISRAELIFICATION MACHINE</h2>
    </div>
    <div class="card-body">

      <!-- Upload Zone -->
      <div class="upload-zone" id="uploadZone" onclick="document.getElementById('file-input').click()">
        <input type="file" id="file-input" accept="image/*"/>
        <span class="upload-icon">🖼️</span>
        <div class="upload-title">Drop your meme here</div>
        <div class="upload-sub">PNG, JPG, GIF, WEBP up to 16MB</div>
        <div class="upload-btn">Choose File</div>
      </div>

      <!-- Preview Section -->
      <div class="preview-section" id="previewSection">
        <div class="preview-grid">
          <div class="preview-pane">
            <span class="preview-pane-label">Original</span>
            <img id="originalPreview" src="" alt="Original"/>
          </div>
          <div class="preview-pane">
            <span class="preview-pane-label">✡ Israelified</span>
            <img id="resultPreview" src="/static/placeholder.png" alt="Result"/>
          </div>
        </div>

        <!-- Transform Button -->
        <div class="transform-btn-wrap">
          <button class="transform-btn" id="transformBtn" onclick="transformImage()">
            <span class="btn-star">✡</span>
            ISRAELIFY THIS MEME
            <span class="btn-star">✡</span>
          </button>
          <button class="reset-btn" id="resetBtn" onclick="resetAll()">↩ Start Over</button>
        </div>

        <!-- Download Section -->
        <div class="download-section" id="downloadSection">
          <a class="download-btn" id="downloadBtn" href="#" download>
            ⬇️ Download Israelified Meme
          </a>
          <p class="success-msg">🎉 Your meme has been successfully Israelified! Share it with the community.</p>
        </div>

        <!-- Error -->
        <div class="error-msg" id="errorMsg"></div>
      </div>

    </div>
  </div>

  <!-- Divider -->
  <div class="divider"><span>✡</span></div>

  <!-- Info Cards -->
  <div class="info-grid">
    <div class="info-card">
      <span class="info-card-icon">🇮🇱</span>
      <div class="info-card-title">Israeli Flag Colors</div>
      <div class="info-card-text">Every meme gets the sacred blue & white treatment. Star of David included.</div>
    </div>
    <div class="info-card">
      <span class="info-card-icon">✡</span>
      <div class="info-card-title">$israelify Token</div>
      <div class="info-card-text">The first memecoin dedicated to the Israelification of the entire internet.</div>
    </div>
    <div class="info-card">
      <span class="info-card-icon">🚀</span>
      <div class="info-card-title">Pump.fun</div>
      <div class="info-card-text">Buy $israelify on Pump.fun. CA: DaZrk...pump. Join the community today.</div>
    </div>
    <div class="info-card">
      <span class="info-card-icon">🤝</span>
      <div class="info-card-title">Join the Movement</div>
      <div class="info-card-text">Follow our X Community and share your Israelified memes with the world.</div>
    </div>
  </div>

</div>

<!-- Loading Overlay -->
<div class="loading-overlay" id="loadingOverlay">
  <span class="loading-star">✡</span>
  <div class="loading-text">ISRAELIFYING...</div>
  <div class="loading-sub">Applying blue & white transformation ✡</div>
  <div class="progress-bar"><div class="progress-fill"></div></div>
</div>

<!-- Footer -->
<footer>
  <p>✡ <strong>$israelify</strong> — Israelification is the process of jewifying every meme ✡</p>
  <p style="margin-top:6px">CA: HnWQXCVE84dGc2AQxNwK1DdR3NgYqLHQTnFkh6ddpump </p>
</footer>

<script>
  // ── Floating stars background ──
  const starsContainer = document.getElementById('starsContainer');
  for (let i = 0; i < 18; i++) {
    const s = document.createElement('span');
    s.className = 'star';
    s.textContent = '✡';
    s.style.left = Math.random() * 100 + '%';
    s.style.animationDelay = Math.random() * 8 + 's';
    s.style.animationDuration = (6 + Math.random() * 8) + 's';
    s.style.fontSize = (14 + Math.random() * 22) + 'px';
    starsContainer.appendChild(s);
  }

  // ── Copy CA ──
  function copyCa() {
    navigator.clipboard.writeText('HnWQXCVE84dGc2AQxNwK1DdR3NgYqLHQTnFkh6ddpump
9:');
    const el = document.getElementById('caBanner');
    el.classList.add('copied');
    setTimeout(() => el.classList.remove('copied'), 2000);
  }

  // ── Drag & Drop ──
  const zone = document.getElementById('uploadZone');
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  document.getElementById('file-input').addEventListener('change', e => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
  });

  let currentFile = null;

  function handleFile(file) {
    if (!file.type.startsWith('image/')) {
      showError('Please upload an image file.');
      return;
    }
    currentFile = file;
    const reader = new FileReader();
    reader.onload = e => {
      document.getElementById('originalPreview').src = e.target.result;
      document.getElementById('resultPreview').src = e.target.result;
      document.getElementById('resultPreview').style.opacity = '0.4';
      document.getElementById('previewSection').classList.add('show');
      document.getElementById('downloadSection').classList.remove('show');
      document.getElementById('errorMsg').classList.remove('show');
      document.getElementById('resetBtn').classList.remove('show');
      // Animate card in
      document.getElementById('previewSection').style.animation = 'none';
      document.getElementById('previewSection').offsetHeight;
    };
    reader.readAsDataURL(file);
  }

  async function transformImage() {
    if (!currentFile) return;
    
    const btn = document.getElementById('transformBtn');
    btn.disabled = true;
    document.getElementById('loadingOverlay').classList.add('show');
    // Cycle through messages while AI works
    const msgs = [
      'Sending to AI model... ✡',
      'Swapping costume to Israeli colors... 🇮🇱',
      'Adding Stars of David... ✡',
      'Almost done... ✡',
    ];
    let mi = 0;
    const msgInterval = setInterval(() => {
      const el = document.getElementById('loadingSub');
      if (el) el.textContent = msgs[mi++ % msgs.length];
    }, 3000);
    window._msgInterval = msgInterval;
    document.getElementById('errorMsg').classList.remove('show');

    const formData = new FormData();
    formData.append('image', currentFile);

    try {
      const resp = await fetch('/transform', { method: 'POST', body: formData });
      const data = await resp.json();

      document.getElementById('loadingOverlay').classList.remove('show');
      clearInterval(window._msgInterval);
      btn.disabled = false;

      if (data.success) {
        const resultImg = document.getElementById('resultPreview');
        resultImg.style.opacity = '1';
        resultImg.src = data.preview;

        // FIX: Client-side download — no server route needed.
        // Create a temporary <a> with the base64 data URL and trigger click.
        // Works perfectly on Vercel's stateless serverless environment.
        const dlBtn = document.getElementById('downloadBtn');
        dlBtn.onclick = (e) => {
          e.preventDefault();
          const a = document.createElement('a');
          a.href = data.preview;          // the data:image/png;base64,... string
          a.download = 'israelified.png';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        };
        document.getElementById('downloadSection').classList.add('show');
        document.getElementById('resetBtn').classList.add('show');
        launchConfetti();
      } else {
        showError(data.error || 'Transformation failed. Try another image.');
      }
    } catch (err) {
      document.getElementById('loadingOverlay').classList.remove('show');
      clearInterval(window._msgInterval);
      btn.disabled = false;
      showError('Server error. Please try again.');
    }
  }

  function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = '⚠️ ' + msg;
    el.classList.add('show');
  }

  function resetAll() {
    currentFile = null;
    document.getElementById('previewSection').classList.remove('show');
    document.getElementById('downloadSection').classList.remove('show');
    document.getElementById('errorMsg').classList.remove('show');
    document.getElementById('resetBtn').classList.remove('show');
    document.getElementById('file-input').value = '';
  }

  // ── Confetti ──
  function launchConfetti() {
    const canvas = document.getElementById('confetti-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = ['#0038b8','#4a90d9','#ffffff','#ffd700','#d4e6f8'];
    const particles = Array.from({length: 120}, () => ({
      x: Math.random() * canvas.width,
      y: -20,
      vx: (Math.random() - 0.5) * 4,
      vy: Math.random() * 4 + 2,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: Math.random() * 8 + 4,
      rot: Math.random() * 360,
      rotSpeed: (Math.random()-0.5)*6,
      shape: Math.random() > 0.5 ? 'rect' : 'star'
    }));

    let frame = 0;
    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.05;
        p.rot += p.rotSpeed;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot * Math.PI / 180);
        ctx.fillStyle = p.color;
        if (p.shape === 'rect') {
          ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size * 0.6);
        } else {
          ctx.font = p.size * 2 + 'px serif';
          ctx.fillText('✡', -p.size/2, p.size/2);
        }
        ctx.restore();
      });
      frame++;
      if (frame < 180) requestAnimationFrame(animate);
      else ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    animate();
  }
</script>
</body>
</html>
"""
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

import requests as http_requests

ISRAELIFY_PROMPT = (
    "Transform this image into an Israeli-themed version. "
    "Replace ALL clothing, costume, outfit, and fabric with Israeli flag design: "
    "pure white fabric with royal blue horizontal stripes and large Star of David (Magen David) symbols. "
    "The hat/headwear should become white with blue horizontal stripe and a blue Star of David on it. "
    "The body/shirt/suit should be white with blue Stars of David printed on it. "
    "Any sleeves or cuffs should have blue horizontal stripes. "
    "Keep the face, skin, hair, eyes, and background completely unchanged and identical. "
    "Preserve all facial features perfectly. "
    "The transformation is only on clothing and accessories. "
    "Style: clean, bright, high-quality, sharp details, professional lighting. "
    "Israeli flag colors only: white (#FFFFFF) and royal blue (#0038B8). "
    "No red. No other colors on the costume."
)


def ai_israelify(image_b64: str) -> str:
    """
    Call fal.ai Flux Kontext API for AI image-to-image transformation.
    Requires FAL_KEY environment variable.
    Returns base64-encoded result image.
    """
    fal_key = os.environ.get('FAL_KEY', '')
    if not fal_key:
        raise ValueError("FAL_KEY environment variable not set. Get your key at fal.ai")

    # Submit job
    response = http_requests.post(
        'https://queue.fal.run/fal-ai/flux-pro/kontext',
        headers={
            'Authorization': f'Key {fal_key}',
            'Content-Type': 'application/json',
        },
        json={
            'prompt': ISRAELIFY_PROMPT,
            'image_url': f'data:image/jpeg;base64,{image_b64}',
            'num_inference_steps': 30,
            'guidance_scale': 4.0,
            'num_images': 1,
            'output_format': 'jpeg',
        },
        timeout=10
    )

    if response.status_code not in (200, 201):
        raise Exception(f"fal.ai error {response.status_code}: {response.text[:200]}")

    data = response.json()

    # fal queue — poll for result
    request_id = data.get('request_id')
    status_url = data.get('status_url') or f'https://queue.fal.run/fal-ai/flux-pro/kontext/requests/{request_id}/status'
    result_url = data.get('response_url') or f'https://queue.fal.run/fal-ai/flux-pro/kontext/requests/{request_id}'

    # If synchronous result already returned
    if 'images' in data:
        image_url = data['images'][0]['url']
    else:
        # Poll status
        import time
        for _ in range(60):  # up to 60s
            time.sleep(1)
            st = http_requests.get(status_url, headers={'Authorization': f'Key {fal_key}'}, timeout=10)
            st_data = st.json()
            status = st_data.get('status', '')
            if status == 'COMPLETED':
                res = http_requests.get(result_url, headers={'Authorization': f'Key {fal_key}'}, timeout=10)
                res_data = res.json()
                image_url = res_data['images'][0]['url']
                break
            elif status in ('FAILED', 'CANCELLED'):
                raise Exception(f"fal.ai job failed: {st_data}")
        else:
            raise Exception("fal.ai timeout after 60s")

    # Download result image
    img_response = http_requests.get(image_url, timeout=30)
    img_bytes = img_response.content
    return base64.b64encode(img_bytes).decode()


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/transform', methods=['POST'])
def transform():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Read and resize image
        img = Image.open(file.stream).convert('RGB')
        max_dim = 1024
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.LANCZOS)

        # Encode to base64 JPEG for API
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=90)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()

        # AI transformation
        result_b64 = ai_israelify(img_b64)

        return jsonify({
            'success': True,
            'preview': f'data:image/jpeg;base64,{result_b64}',
        })
    except ValueError as e:
        # Missing API key — return friendly message
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
