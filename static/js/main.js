// AviaGreene — main.js

(function () {
  'use strict';

  /* ── Icon helpers (declared FIRST so they're always available) ──────── */
  function iconHamburger() {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
  }
  function iconClose() {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  }

  /* ── Sticky / transparent header ───────────────────────────────────── */
  var header = document.querySelector('.site-header');
  if (header) {
    var isTransparent = header.classList.contains('header-transparent');
    function onScroll() {
      if (!isTransparent) return;
      if (window.scrollY > 24) {
        header.classList.add('scrolled');
        header.classList.remove('transparent');
      } else {
        header.classList.remove('scrolled');
        header.classList.add('transparent');
      }
    }
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ── Mobile menu — 100% inline-style, zero CSS-class dependency ─────
   *
   *  How it works:
   *  • applyMenuStyles() writes every visual property directly onto the
   *    element's .style object, which has higher priority than any
   *    stylesheet rule.  Nothing the CSS says can override it.
   *  • The toggle button calls e.stopPropagation() so the document-level
   *    "tap outside" listener never fires on the very same click that
   *    opens the menu (which would immediately close it again).
   *  • Clicks inside the menu panel are also stopped so they don't
   *    bubble to the document and accidentally close it.
   * ------------------------------------------------------------------ */
  var menuToggle = document.querySelector('.menu-toggle');
  var mobileMenu = document.getElementById('mobile-menu');
  var closeBtn   = document.getElementById('mobile-menu-close');
  var menuOpen   = false;

  function applyMenuStyles(open) {
    if (!mobileMenu) return;
    mobileMenu.style.display       = 'flex';
    mobileMenu.style.flexDirection = 'column';
    mobileMenu.style.position      = 'fixed';
    mobileMenu.style.top           = '0';
    mobileMenu.style.left          = '0';
    mobileMenu.style.right         = '0';
    mobileMenu.style.bottom        = '0';
    mobileMenu.style.width         = '100%';
    mobileMenu.style.height        = '100%';
    mobileMenu.style.background    = 'var(--navy, #0b1a2e)';
    mobileMenu.style.zIndex        = '9990';
    mobileMenu.style.padding       = '1.5rem 1.5rem 3rem';
    mobileMenu.style.gap           = '0';
    mobileMenu.style.overflowY     = 'auto';
    mobileMenu.style.transition    = 'transform 0.35s cubic-bezier(0.22,1,0.36,1), visibility 0.35s';
    // Only these two change between open and closed:
    mobileMenu.style.transform     = open ? 'translateX(0)'  : 'translateX(100%)';
    mobileMenu.style.visibility    = open ? 'visible'        : 'hidden';
  }

  // Initialise as CLOSED the moment the script runs
  applyMenuStyles(false);

  function openMenu() {
    menuOpen = true;
    applyMenuStyles(true);
    document.body.style.overflow = 'hidden';
    if (menuToggle) {
      menuToggle.setAttribute('aria-expanded', 'true');
      menuToggle.innerHTML = iconClose();
    }
  }

  function closeMenu() {
    menuOpen = false;
    applyMenuStyles(false);
    document.body.style.overflow = '';
    if (menuToggle) {
      menuToggle.setAttribute('aria-expanded', 'false');
      menuToggle.innerHTML = iconHamburger();
    }
  }

  // Hamburger button — stopPropagation prevents the document handler
  // from seeing this same click and immediately closing the menu
  if (menuToggle) {
    menuToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (menuOpen) { closeMenu(); } else { openMenu(); }
    });
  }

  // X button inside the menu
  if (closeBtn) {
    closeBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      closeMenu();
    });
  }

  // Clicks inside the panel stay inside — don't bubble to document
  if (mobileMenu) {
    mobileMenu.addEventListener('click', function (e) {
      e.stopPropagation();
    });
    // Nav links still navigate (and close the menu first)
    mobileMenu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { closeMenu(); });
    });
  }

  // Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menuOpen) closeMenu();
  });

  // Tap anywhere outside the open menu closes it
  document.addEventListener('click', function () {
    if (menuOpen) closeMenu();
  });

  /* ── Active nav link highlight ─────────────────────────────────────── */
  var path = window.location.pathname;
  document.querySelectorAll('.site-nav a, .mobile-menu a').forEach(function (a) {
    var href = a.getAttribute('href');
    if (href && (href === path || (href !== '/' && path.startsWith(href)))) {
      a.classList.add('active');
    }
  });

  /* ── Scroll-triggered fade-in ──────────────────────────────────────── */
  if ('IntersectionObserver' in window) {
    var fadeObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          fadeObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll('.fade-up, .fade-right').forEach(function (el) {
      fadeObs.observe(el);
    });
  } else {
    document.querySelectorAll('.fade-up, .fade-right').forEach(function (el) {
      el.classList.add('visible');
    });
  }

})();

/* ── Animation classes injected at runtime ─────────────────────────────── */
(function () {
  var s = document.createElement('style');
  s.textContent = [
    '.fade-up{opacity:0;transform:translateY(24px);transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .7s cubic-bezier(.22,1,.36,1)}',
    '.fade-up.visible{opacity:1;transform:translateY(0)}',
    '.fade-right{opacity:0;transform:translateX(24px);transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .7s cubic-bezier(.22,1,.36,1)}',
    '.fade-right.visible{opacity:1;transform:translateX(0)}',
    '@media(prefers-reduced-motion:reduce){.fade-up,.fade-right{transition:opacity .3s ease;transform:none}}'
  ].join('\n');
  document.head.appendChild(s);
})();

/* ── Hero background video — autoplay + reduced-motion handling ─────────── */
(function () {
  var video = document.querySelector('.hero-video');
  if (!video) return;

  // Respect prefers-reduced-motion: pause and show poster instead
  var mq = window.matchMedia('(prefers-reduced-motion: reduce)');
  function handleMotion(e) {
    if (e.matches) {
      video.pause();
      video.style.display = 'none'; // poster on <section> background shows through
    } else {
      video.style.display = '';
      video.play().catch(function () {});
    }
  }
  handleMotion(mq);
  if (mq.addEventListener) { mq.addEventListener('change', handleMotion); }
  else if (mq.addListener)  { mq.addListener(handleMotion); } // Safari < 14

  // Autoplay may be blocked (e.g. low-power mode on iOS) — fail silently,
  // poster image is always shown as the video element background
  var playPromise = video.play();
  if (playPromise !== undefined) {
    playPromise.catch(function () {
      // Autoplay blocked — poster is already visible, nothing to do
    });
  }
})();