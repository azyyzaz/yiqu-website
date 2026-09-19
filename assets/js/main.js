/* ==========================================================================
   福州易趣网络科技有限公司 — 官网交互
   无依赖。所有功能都有无 JS 时的降级表现。
   ========================================================================== */
(function () {
  'use strict';

  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. 页脚年份 ---------- */
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* ---------- 2. 移动端导航抽屉 ---------- */
  var nav       = document.getElementById('primaryNav');
  var toggle    = document.getElementById('navToggle');
  var backdrop  = document.getElementById('navBackdrop');

  function setNav(open) {
    if (!nav || !toggle) return;
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '关闭导航菜单' : '打开导航菜单');
    document.body.style.overflow = open ? 'hidden' : '';
    if (backdrop) backdrop.hidden = !open;
  }

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      setNav(!nav.classList.contains('is-open'));
    });
  }
  if (backdrop) backdrop.addEventListener('click', function () { setNav(false); });

  // 点击导航项后收起
  if (nav) {
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setNav(false);
    });
  }

  // Esc 关闭
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setNav(false);
  });

  // 视口变宽时复位
  var wideQuery = window.matchMedia('(min-width: 861px)');
  var onWide = function (e) { if (e.matches) setNav(false); };
  if (wideQuery.addEventListener) wideQuery.addEventListener('change', onWide);
  else if (wideQuery.addListener) wideQuery.addListener(onWide);

  /* ---------- 3. 顶部导航滚动态 ---------- */
  var header = document.getElementById('siteHeader');
  var ticking = false;

  function onScroll() {
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 8);
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(onScroll);
    }
  }, { passive: true });
  onScroll();

  /* ---------- 4. 滚动入场动画 ---------- */
  var revealEls = Array.prototype.slice.call(document.querySelectorAll('.reveal'));

  function showAll() {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  function showInViewport() {
    revealEls.forEach(function (el) {
      if (el.classList.contains('is-visible')) return;
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) el.classList.add('is-visible');
    });
  }

  if (prefersReduced || !('IntersectionObserver' in window)) {
    // 降级：不支持观察器或用户偏好减弱动效时，直接显示全部内容
    showAll();
  } else {
    var observerFired = false;

    var revealObserver = new IntersectionObserver(function (entries) {
      observerFired = true;
      entries.forEach(function (entry, i) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        // 同批元素轻微错峰，读起来有节奏
        el.style.transitionDelay = Math.min(i * 60, 240) + 'ms';
        el.classList.add('is-visible');
        revealObserver.unobserve(el);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });

    revealEls.forEach(function (el) { revealObserver.observe(el); });

    // 首屏直接落在某区块（如 /#contact）时，先补显一次
    window.addEventListener('load', showInViewport);

    // 兜底：若观察器始终未回调，退化为滚动监听，避免内容永久不可见
    window.setTimeout(function () {
      if (observerFired) return;
      showInViewport();
      window.addEventListener('scroll', showInViewport, { passive: true });
      window.addEventListener('resize', showInViewport);
    }, 2000);
  }

  /* ---------- 5. 导航高亮当前区块 ---------- */
  var navLinks = nav ? Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]')) : [];

  if (navLinks.length && 'IntersectionObserver' in window) {
    var sections = navLinks
      .map(function (a) { return document.querySelector(a.getAttribute('href')); })
      .filter(Boolean);

    var setActive = function (id) {
      navLinks.forEach(function (a) {
        a.classList.toggle('is-active', a.getAttribute('href') === '#' + id);
      });
    };

    var sectionObserver = new IntersectionObserver(function (entries) {
      // 取当前可见度最高的区块
      var best = null;
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        if (!best || e.intersectionRatio > best.intersectionRatio) best = e;
      });
      if (best) setActive(best.target.id);
    }, {
      rootMargin: '-25% 0px -60% 0px',
      threshold: [0, 0.15, 0.4, 0.75, 1]
    });

    sections.forEach(function (s) { sectionObserver.observe(s); });
  }
})();
