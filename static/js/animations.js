/* ============================================================
   AVIAGREENE — ANIMATIONS ENGINE
   ============================================================ */
(function () {
  'use strict';

  /* ── Page Loader ── */
  function initLoader() {
    var loader = document.getElementById('page-loader');
    if (!loader) return;
    function hide() { loader.classList.add('done'); }
    if (document.readyState === 'complete') {
      setTimeout(hide, 150);
    } else {
      window.addEventListener('load', function () { setTimeout(hide, 150); });
      setTimeout(hide, 2800);
    }
  }

  /* ── Scroll reveal ── */
  function initScrollReveal() {
    var els = document.querySelectorAll('.fade-up,.fade-left,.fade-right,.fade-in-el,.fade-scale');
    if (!els.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ── Stagger parent observer ── */
  function initStagger() {
    var parents = document.querySelectorAll('.stagger-children');
    if (!parents.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.08 });
    parents.forEach(function (p) { io.observe(p); });
  }

  /* ── Animated counter ── */
  function countUp(el, target, suffix, duration) {
    var start = performance.now();
    function tick(now) {
      var p = Math.min((now - start) / duration, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.floor(target * ease) + suffix;
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = target + suffix;
    }
    requestAnimationFrame(tick);
  }

  function initCounters() {
    var items = document.querySelectorAll('.stat-item');
    if (!items.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('visible');
        var kEl = e.target.querySelector('.stat-k');
        if (!kEl || kEl.dataset.done) return;
        kEl.dataset.done = '1';
        var raw = kEl.textContent.trim();
        var m = raw.match(/^(\d+\.?\d*)([^0-9.]*)$/);
        if (m) { kEl.textContent = '0' + m[2]; countUp(kEl, parseFloat(m[1]), m[2], 1600); }
        io.unobserve(e.target);
      });
    }, { threshold: 0.35 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ── Animated lines ── */
  function initLines() {
    var lines = document.querySelectorAll('.animated-line');
    if (!lines.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.5 });
    lines.forEach(function (el) { io.observe(el); });
  }

  /* ── Scrolled header ── */
  function initHeader() {
    var h = document.getElementById('site-header');
    if (!h) return;
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(function () {
          if (window.scrollY > 50) h.classList.add('scrolled');
          else h.classList.remove('scrolled');
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  /* ── Parallax ── */
  function initParallax() {
    var imgs = document.querySelectorAll('.parallax-img');
    if (!imgs.length || window.matchMedia('(prefers-reduced-motion:reduce)').matches) return;
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(function () {
          imgs.forEach(function (img) {
            var rect = img.getBoundingClientRect();
            var offset = (window.innerHeight / 2 - (rect.top + rect.height / 2)) * 0.07;
            img.style.transform = 'translateY(' + offset + 'px)';
          });
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  /* ── Magnetic buttons (subtle) ── */
  function initMagnetic() {
    document.querySelectorAll('.btn-green, .btn-navy').forEach(function (btn) {
      btn.addEventListener('mousemove', function (e) {
        var r = btn.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width  / 2) * 0.15;
        var y = (e.clientY - r.top  - r.height / 2) * 0.15;
        btn.style.transform = 'translate(' + x + 'px,' + (y - 2) + 'px)';
      });
      btn.addEventListener('mouseleave', function () {
        btn.style.transform = '';
      });
    });
  }

  /* ── Mobile menu toggle ── */
  function initMobileMenu() {
    var toggle = document.querySelector('.menu-toggle');
    var menu   = document.getElementById('mobile-menu');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', function () {
      var open = menu.style.display === 'flex';
      menu.style.display = open ? 'none' : 'flex';
      toggle.setAttribute('aria-expanded', String(!open));
    });
  }

  /* ── Carousel engine ── */
  var carousels = {};

  window.scrollCarousel = function (id, dir) {
    var c = carousels[id];
    if (!c) return;
    c.index = Math.max(0, Math.min(c.index + dir, c.total - c.perView));
    updateCarousel(id);
  };

  function updateCarousel(id) {
    var c = carousels[id];
    var track = document.getElementById(id + '-track');
    if (!track || !track.children.length) return;
    var w = track.children[0].offsetWidth + 1;
    track.style.transform = 'translateX(-' + (c.index * w) + 'px)';
    renderDots(id);
  }

  function renderDots(id) {
    var c = carousels[id];
    var box = document.getElementById(id + '-dots');
    if (!box) return;
    var n = Math.max(1, c.total - c.perView + 1);
    box.innerHTML = '';
    for (var i = 0; i < n; i++) {
      (function (idx) {
        var d = document.createElement('button');
        d.setAttribute('aria-label', 'Slide ' + (idx + 1));
        d.style.cssText = 'width:8px;height:8px;border-radius:50%;border:none;padding:0;cursor:pointer;transition:all 0.25s;background:'
          + (idx === c.index ? 'var(--green)' : 'rgba(255,255,255,0.25)')
          + ';transform:' + (idx === c.index ? 'scale(1.4)' : 'scale(1)');
        d.onclick = function () { carousels[id].index = idx; updateCarousel(id); };
        box.appendChild(d);
      })(i);
    }
  }

  function initCarouselById(id, perView) {
    var track = document.getElementById(id + '-track');
    if (!track || !track.children.length) return;
    Array.from(track.children).forEach(function (el) {
      el.style.minWidth = 'calc(' + (100 / perView) + '% - 1px)';
    });
    carousels[id] = { index: 0, total: track.children.length, perView: perView };
    renderDots(id);
    updateCarousel(id);
  }

  function getServicesPerView() {
    return window.innerWidth < 640 ? 1 : window.innerWidth < 1024 ? 2 : 3;
  }

  function initCarousels() {
    initCarouselById('services', getServicesPerView());
    initCarouselById('testimonials', 1);

    // Auto-advance testimonials
    var tTrack = document.getElementById('testimonials-track');
    if (tTrack) {
      setInterval(function () {
        var c = carousels['testimonials'];
        if (!c) return;
        c.index = c.index >= c.total - c.perView ? 0 : c.index + 1;
        updateCarousel('testimonials');
      }, 6000);
    }

    // Resize
    window.addEventListener('resize', function () {
      var st = document.getElementById('services-track');
      if (st) {
        var pv = getServicesPerView();
        Array.from(st.children).forEach(function (el) {
          el.style.minWidth = 'calc(' + (100 / pv) + '% - 1px)';
        });
        var c = carousels['services'];
        if (c) { c.perView = pv; c.index = 0; updateCarousel('services'); }
      }
    });
  }

  /* ── Testimonial card hover tilt ── */
  function initCardTilt() {
    var cards = document.querySelectorAll(
      'section div[style*="hsl(215 50% 18%)"], .testimonials-grid-item, .value-item'
    );
    cards.forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        if (window.matchMedia('(prefers-reduced-motion:reduce)').matches) return;
        var r = card.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width  - 0.5;
        var y = (e.clientY - r.top)  / r.height - 0.5;
        card.style.transform = 'translateY(-8px) rotateX(' + (-y * 4) + 'deg) rotateY(' + (x * 4) + 'deg)';
        card.style.transition = 'transform 0.1s ease';
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = '';
        card.style.transition = 'transform 0.35s cubic-bezier(0.22,1,0.36,1)';
      });
    });
  }

  /* ── Init all ── */
  document.addEventListener('DOMContentLoaded', function () {
    initLoader();
    initHeader();
    initScrollReveal();
    initStagger();
    initCounters();
    initLines();
    initParallax();
    initMagnetic();
    initMobileMenu();
    initCarousels();
    setTimeout(initCardTilt, 300);
  });

})();
