// ── ARS ENGINE SHARED JS ─────────────────────────────────────────────────
// Injected into every page via <script src="../shared.js"> or <script src="shared.js">

// ── GOOGLE FONTS ─────────────────────────────────────────────────────────
(function injectFonts() {
  if (document.getElementById('ars-fonts')) return;
  const link = document.createElement('link');
  link.id = 'ars-fonts';
  link.rel = 'stylesheet';
  link.href = 'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap';
  document.head.appendChild(link);
  const preconnect = document.createElement('link');
  preconnect.rel = 'preconnect';
  preconnect.href = 'https://fonts.googleapis.com';
  document.head.insertBefore(preconnect, link);
})();

// ── HEADER HTML ──────────────────────────────────────────────────────────
// Resolves relative paths for pages in subdirectories (e.g. industries/)
function getBasePath() {
  const depth = window.location.pathname.split('/').filter(Boolean).length;
  const inSubdir = document.querySelector('meta[name="ars-subdir"]');
  return inSubdir ? '../' : '';
}

function buildHeader() {
  const base = getBasePath();
  return `
<div class="topbar">
  <div class="topbar-item">&#9670; <span>PE-Grade</span> Acquisition Intelligence</div>
  <div class="topbar-item">&#9670; <span>5-Dimension</span> ARS Scoring</div>
  <div class="topbar-item">&#9670; Claude AI <span>Powered</span></div>
  <div class="topbar-item">&#9670; <span>Zero</span> Setup Required</div>
</div>
<header class="hdr">
  <div class="hdr-left">
    <a href="${base}index.html" class="logo-mark" style="text-decoration:none"><div class="logo-mark-inner">ARS</div></a>
    <a href="${base}index.html" class="logo-text" style="text-decoration:none">
      <span class="logo-name">ARS Engine</span>
      <span class="logo-sub">Acquisition Intelligence Platform</span>
    </a>
    <nav class="hdr-nav">
      <a class="hdr-nav-item" href="${base}index.html">Home</a>
      <a class="hdr-nav-item" href="${base}sandbox.html">Sandbox</a>
      <a class="hdr-nav-item" href="${base}roi-calculator.html">ROI Calculator</a>
      <a class="hdr-nav-item" href="${base}vs-saasquatch.html">vs SaaSquatch</a>
      <a class="hdr-nav-item" href="${base}industries/hvac.html">Industries</a>
    </nav>
  </div>
  <div class="hdr-right">
    <div class="api-pill"><div class="api-dot" id="api-dot"></div><span id="api-status-label">Connecting...</span></div>
    <a href="${base}login.html" class="btn btn-ghost-dark btn-sm">Log In</a>
    <a href="${base}signup.html" class="btn btn-amber btn-sm">Start Free</a>
    <button class="mobile-menu-btn" onclick="ARS.toggleMobileMenu()">&#9776;</button>
  </div>
</header>
<div id="mobile-menu" style="display:none;background:var(--navy2);border-bottom:1px solid var(--wborder);padding:12px 16px;position:sticky;top:62px;z-index:150">
  <div style="display:flex;flex-direction:column;gap:2px">
    <a class="hdr-nav-item" href="${base}index.html">Home</a>
    <a class="hdr-nav-item" href="${base}sandbox.html">Sandbox</a>
    <a class="hdr-nav-item" href="${base}roi-calculator.html">ROI Calculator</a>
    <a class="hdr-nav-item" href="${base}vs-saasquatch.html">vs SaaSquatch</a>
    <a class="hdr-nav-item" href="${base}industries/hvac.html">Industries</a>
    <a class="hdr-nav-item" href="${base}login.html">Log In</a>
    <a class="hdr-nav-item" href="${base}signup.html" style="color:var(--amber)">Start Free &#8594;</a>
  </div>
</div>`;
}

// ── FOOTER HTML ──────────────────────────────────────────────────────────
function buildFooter() {
  const base = getBasePath();
  return `
<div class="footer-grid">
  <div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
      <div style="width:32px;height:32px;background:var(--amber);border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:'Barlow Condensed',sans-serif;font-size:14px;font-weight:800;color:var(--navy)">ARS</div>
      <span style="font-family:'Barlow Condensed',sans-serif;font-size:16px;font-weight:700;color:#fff">ARS Engine</span>
    </div>
    <p style="font-size:12px;color:rgba(255,255,255,0.35);line-height:1.7;margin-bottom:20px;font-weight:300">PE-grade acquisition intelligence. Score, rank, and enrich business targets using AI-powered signal analysis across 5 dimensions.</p>
    <div style="display:flex;gap:8px">
      <a href="#" class="social-btn">𝕏</a>
      <a href="#" class="social-btn">in</a>
    </div>
  </div>
  <div>
    <div class="footer-col-title">Platform</div>
    <ul class="footer-links">
      <li><a href="${base}index.html">Home</a></li>
      <li><a href="${base}sandbox.html">Live Sandbox</a></li>
      <li><a href="${base}roi-calculator.html">ROI Calculator</a></li>
      <li><a href="${base}vs-saasquatch.html">ARS vs SaaSquatch</a></li>
    </ul>
  </div>
  <div>
    <div class="footer-col-title">Industries</div>
    <ul class="footer-links">
      <li><a href="${base}industries/hvac.html">HVAC Acquisitions</a></li>
      <li><a href="${base}industries/plumbing.html">Plumbing Acquisitions</a></li>
      <li><a href="${base}industries/landscaping.html">Landscaping Acquisitions</a></li>
      <li><a href="${base}industries/roofing.html">Roofing Acquisitions</a></li>
    </ul>
  </div>
  <div>
    <div class="footer-col-title">Company</div>
    <ul class="footer-links">
      <li><a href="#">About</a></li>
      <li><a href="#">Blog</a></li>
      <li><a href="#">Careers</a></li>
      <li><a href="#">Contact</a></li>
    </ul>
  </div>
  <div>
    <div class="footer-col-title">Legal</div>
    <ul class="footer-links">
      <li><a href="#">Privacy Policy</a></li>
      <li><a href="#">Terms of Service</a></li>
      <li><a href="#">Security</a></li>
      <li><a href="#">GDPR</a></li>
    </ul>
  </div>
</div>
<div class="footer-bottom">
  <span>© 2025 ARS Engine. All rights reserved.</span>
  <div style="display:flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:1px;text-transform:uppercase">
    <div style="width:6px;height:6px;border-radius:50%;background:#22c55e"></div>
    All Systems Operational
  </div>
</div>`;
}

// ── ARS NAMESPACE ────────────────────────────────────────────────────────
window.ARS = {

  // Toast
  toast(msg, type = '') {
    let t = document.getElementById('ars-toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'ars-toast';
      t.className = 'toast';
      document.body.appendChild(t);
    }
    t.innerText = msg;
    t.className = 'toast show' + (type ? ' ' + type : '');
    clearTimeout(t._timer);
    t._timer = setTimeout(() => { t.className = 'toast'; }, 3000);
  },

  // FAQ
  toggleFaq(el) {
    el.parentElement.classList.toggle('open');
  },

  // Mobile menu
  toggleMobileMenu() {
    const m = document.getElementById('mobile-menu');
    if (m) m.style.display = m.style.display === 'none' ? 'block' : 'none';
  },
  closeMobileMenu() {
    const m = document.getElementById('mobile-menu');
    if (m) m.style.display = 'none';
  },

  // Active nav highlight
  setActiveNav() {
    const filename = window.location.pathname.split('/').pop() || 'index.html';
    const fullpath = window.location.pathname;
    document.querySelectorAll('.hdr-nav-item').forEach(a => {
      const href = a.getAttribute('href') || '';
      const hrefFile = href.split('/').pop();
      if (hrefFile === filename || (filename === '' && hrefFile === 'index.html')) {
        a.classList.add('active');
      }
      // highlight Industries for any industries/ page
      if (fullpath.includes('/industries/') && href.includes('/industries/')) {
        a.classList.add('active');
      }
    });
  },

  // API dot animation
  initApiDot() {
    setTimeout(() => {
      const dot = document.getElementById('api-dot');
      const label = document.getElementById('api-status-label');
      if (dot) dot.classList.add('ok');
      if (label) label.innerText = 'System Live';
    }, 900);
  },

  // Init — called on DOMContentLoaded
  init() {
    // Inject header
    const headerEl = document.getElementById('ars-header');
    if (headerEl) headerEl.innerHTML = buildHeader();

    // Inject footer
    document.querySelectorAll('.ars-footer').forEach(el => {
      el.innerHTML = buildFooter();
    });

    this.setActiveNav();
    this.initApiDot();
  }
};

// ── LEGACY COMPAT: top-level functions ───────────────────────────────────
function showToast(msg, type) { ARS.toast(msg, type); }
function toggleFaq(el) { ARS.toggleFaq(el); }
function toggleMobileMenu() { ARS.toggleMobileMenu(); }
function closeMobileMenu() { ARS.closeMobileMenu(); }

// ── AUTO INIT ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => ARS.init());
