// AviaGreene — main.js

(function () {
  'use strict';

  // ─── Sticky header ──────────────────────────────────────────────────────
  var header = document.querySelector('.site-header');
  if (header) {
    var isTransparent = header.classList.contains('header-transparent');
    function onScroll() {
      if (isTransparent) {
        if (window.scrollY > 24) {
          header.classList.add('scrolled');
          header.classList.remove('transparent');
        } else {
          header.classList.remove('scrolled');
          header.classList.add('transparent');
        }
      }
    }
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // ─── Mobile menu ────────────────────────────────────────────────────────
  var menuToggle  = document.querySelector('.menu-toggle');
  var mobileMenu  = document.getElementById('mobile-menu');
  var closeBtn    = document.getElementById('mobile-menu-close');
  var body        = document.body;

  function openMenu() {
    if (!mobileMenu) return;
    mobileMenu.classList.add('open');
    body.style.overflow = 'hidden';          // prevent background scroll
    if (menuToggle) menuToggle.setAttribute('aria-expanded', 'true');
    if (menuToggle) menuToggle.innerHTML = svgX();
  }

  function closeMenu() {
    if (!mobileMenu) return;
    mobileMenu.classList.remove('open');
    body.style.overflow = '';
    if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
    if (menuToggle) menuToggle.innerHTML = svgMenu();
  }

  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener('click', function () {
      if (mobileMenu.classList.contains('open')) {
        closeMenu();
      } else {
        openMenu();
      }
    });
  }

  // Wire up close button inside mobile menu
  if (closeBtn) {
    closeBtn.addEventListener('click', closeMenu);
  }

  // Close when any link inside menu is clicked
  if (mobileMenu) {
    mobileMenu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });
  }

  // Close on backdrop click (clicking outside the nav)
  if (mobileMenu) {
    mobileMenu.addEventListener('click', function (e) {
      if (e.target === mobileMenu) closeMenu();
    });
  }

  // Close on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && mobileMenu && mobileMenu.classList.contains('open')) {
      closeMenu();
    }
  });

  // ─── Active nav link ────────────────────────────────────────────────────
  var currentPath = window.location.pathname;
  document.querySelectorAll('.site-nav a, .mobile-menu a').forEach(function (a) {
    var href = a.getAttribute('href');
    if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
      a.classList.add('active');
    }
  });

  // ─── Scroll-triggered fade in ────────────────────────────────────────────
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });   // slightly lower threshold for small screens

    document.querySelectorAll('.fade-up').forEach(function (el) {
      observer.observe(el);
    });
  } else {
    document.querySelectorAll('.fade-up').forEach(function (el) {
      el.classList.add('visible');
    });
  }

  // ─── SVG icons for menu toggle ──────────────────────────────────────────
  function svgMenu() {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
  }

  function svgX() {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  }


})();

// Additional CSS for fade-up
(function () {
  var style = document.createElement('style');
  style.textContent = [
    '.fade-up {',
    '  opacity: 0;',
    '  transform: translateY(24px);',
    '  transition: opacity 0.7s cubic-bezier(0.22,1,0.36,1), transform 0.7s cubic-bezier(0.22,1,0.36,1);',
    '}',
    '.fade-up.visible {',
    '  opacity: 1;',
    '  transform: translateY(0);',
    '}',
    '.fade-right {',
    '  opacity: 0;',
    '  transform: translateX(24px);',
    '  transition: opacity 0.7s cubic-bezier(0.22,1,0.36,1), transform 0.7s cubic-bezier(0.22,1,0.36,1);',
    '}',
    '.fade-right.visible {',
    '  opacity: 1;',
    '  transform: translateX(0);',
    '}',
    /* On small screens, reduce motion for better performance */
    '@media (prefers-reduced-motion: reduce) {',
    '  .fade-up, .fade-right {',
    '    transition: opacity 0.3s ease;',
    '    transform: none;',
    '  }',
    '}'
  ].join('\n');
  document.head.appendChild(style);

  // Also observe fade-right elements
  if ('IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll('.fade-right').forEach(function (el) { obs.observe(el); });
  } else {
    document.querySelectorAll('.fade-right').forEach(function (el) { el.classList.add('visible'); });
  }
})();
