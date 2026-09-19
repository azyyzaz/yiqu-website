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

  /* ---------- 3. 顶部导航滚动态 + 阅读进度 ---------- */
  var header = document.getElementById('siteHeader');
  var ticking = false;

  function onScroll() {
    var y = window.scrollY || window.pageYOffset || 0;
    if (header) {
      header.classList.toggle('is-scrolled', y > 8);

      // 阅读进度：0 → 1，交给 CSS 的 --progress 决定进度条宽度
      var max = document.documentElement.scrollHeight - window.innerHeight;
      var p = max > 0 ? Math.min(1, Math.max(0, y / max)) : 0;
      header.style.setProperty('--progress', p.toFixed(4));
    }
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(onScroll);
    }
  }, { passive: true });
  // 视口变化会改变总高度，进度条需要重算
  window.addEventListener('resize', onScroll);
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

  /* ---------- 6. 首屏细网浮起 ---------- */
  /*
    .hero::after 铺着一层 68px 的静态网线。这里在它上面再画一张十倍密的细网
    （6.8px，正好是 68 的十分之一，两张网严格嵌套）。指针扫过时细网被托起
    一个小穹顶：网格点离指针越近抬得越高，按 smoothstep 衰减，看到的是整张
    网被顶起来，而不是一块方形被抬走。

    十倍密之后一格只有 6.8px，整屏要两万多个格子，DOM 无论如何铺不下，所以
    改用 canvas：

    · 每帧只画指针周围 REACH 半径内的线，所有线并进一条 path、一次 stroke。
    · 柔边交给一道径向渐变的 destination-in 遮罩，而不是逐点调透明度——
      后者得把每段线拆成单独 stroke，慢一个数量级。遮罩顺带把上一帧画在
      别处的内容一并抹掉，不必整屏 clearRect。

    只在能真正"悬浮"的设备上做：触摸屏没有 hover，弱动效同理，都直接跳过；
    JS 不参与时这层根本不存在，页面退回纯静态网线。
    指针移出首屏后整层淡出并停掉动画循环，静止期间一帧都不算。
  */
  (function heroMesh() {
    if (prefersReduced) return;
    if (!window.matchMedia ||
        !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    var hero = document.querySelector('.hero');
    if (!hero) return;

    var canvas = document.createElement('canvas');
    if (!canvas.getContext) return;
    canvas.className = 'hero-mesh';
    canvas.setAttribute('aria-hidden', 'true');
    hero.insertBefore(canvas, hero.firstChild);

    var ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 步距的唯一来源是 CSS 里的 --mesh-size，避免两边写死后对不上
    var PITCH = parseFloat(getComputedStyle(hero).getPropertyValue('--mesh-size')) || 6.8;
    var REACH = 150;                       // 影响半径 px
    var LIFT  = 18;                        // 圆心处最大上浮 px
    var LINE  = 'rgba(44, 85, 240, .42)';  // 线色

    var W = 0, H = 0;
    var cx = 0, cy = 0;                    // 指针的视口坐标
    var mx = 0, my = 0;                    // 换算成首屏内坐标
    var fade = 0, target = 0;
    var running = false, last = 0;
    var dirty = null;                      // 上一帧画过的区域，换地方前先擦掉

    function resize() {
      var w = hero.clientWidth, h = hero.clientHeight;
      if (!w || !h) return;
      W = w; H = h;
      // 细线在小数倍率下会糊，超过 2 倍就没有肉眼收益了，直接封顶
      var dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width  = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      dirty = null;
    }

    // 离指针越近抬得越高；REACH 之外为 0
    function rise(x, y) {
      var dx = x - mx, dy = y - my;
      var d = Math.sqrt(dx * dx + dy * dy) / REACH;
      if (d >= 1) return 0;
      var t = 1 - d;
      t = t * t * (3 - 2 * t);             // smoothstep，边缘更柔
      return LIFT * t;
    }

    function draw(t) {
      if (dirty) ctx.clearRect(dirty[0], dirty[1], dirty[2], dirty[3]);

      var x0 = Math.max(0, mx - REACH), x1 = Math.min(W, mx + REACH);
      var y0 = Math.max(0, my - REACH), y1 = Math.min(H, my + REACH);
      dirty = [x0 - 1, y0 - 1, (x1 - x0) + 2, (y1 - y0) + 2];

      ctx.strokeStyle = LINE;
      ctx.lineWidth = 1;
      ctx.beginPath();

      var i, j, x, y;

      // 竖线：沿 y 逐点采样，抬升只作用在这一段里
      for (i = Math.ceil(x0 / PITCH); i * PITCH <= x1; i++) {
        x = i * PITCH;
        ctx.moveTo(x, y0);
        for (y = y0 + PITCH; y < y1; y += PITCH) ctx.lineTo(x, y - rise(x, y));
        ctx.lineTo(x, y1);
      }
      // 横线：同理，抬升方向始终朝上
      for (j = Math.ceil(y0 / PITCH); j * PITCH <= y1; j++) {
        y = j * PITCH;
        ctx.moveTo(x0, y - rise(x0, y));
        for (x = x0 + PITCH; x < x1; x += PITCH) ctx.lineTo(x, y - rise(x, y));
        ctx.lineTo(x1, y - rise(x1, y));
      }

      /*
        这里不画投影。网格尺寸是给 68px 的间距配的，落到 6.8px 之后
        16px 的模糊半径横跨两个多格子，相邻线的投影互相盖住，整片糊成
        一块蓝色底衬——看着像给浮起区域铺了背景色。这个密度下投影已经
        当不了"单根线的立体感"，索性去掉，只留线条本身。

        浮起靠的是线在弯、加上径向遮罩收边，这两样已经够了。
      */
      ctx.stroke();

      /*
        柔边。destination-in 只保留遮罩不透明的地方，矩形之外整片被抹掉——
        上一帧画在别处的残留也就跟着没了。fade 乘进渐变里，进出场自带淡入淡出。
      */
      ctx.globalCompositeOperation = 'destination-in';
      var g = ctx.createRadialGradient(mx, my, REACH * 0.2, mx, my, REACH);
      g.addColorStop(0, 'rgba(0, 0, 0, ' + t + ')');
      g.addColorStop(0.65, 'rgba(0, 0, 0, ' + (t * 0.5) + ')');
      g.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = g;
      ctx.fillRect(mx - REACH, my - REACH, REACH * 2, REACH * 2);
      ctx.globalCompositeOperation = 'source-over';
    }

    function frame(now) {
      if (now - last < 22) {               // 与其它动效一致，封在 45fps 上下
        window.requestAnimationFrame(frame);
        return;
      }
      last = now;

      // 每帧重算一次，滚动时位置也跟着走；顺带判断指针还在不在首屏
      var r = hero.getBoundingClientRect();
      mx = cx - r.left;
      my = cy - r.top;
      target = (cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom) ? 1 : 0;

      fade += (target - fade) * 0.2;
      if (Math.abs(target - fade) < 0.008) fade = target;

      if (fade <= 0.004) {                 // 收尾：擦干净后停机
        ctx.clearRect(0, 0, W, H);
        dirty = null;
        running = false;
        return;
      }

      draw(fade);
      window.requestAnimationFrame(frame);
    }

    function wake() {
      if (running) return;
      running = true;
      last = 0;
      window.requestAnimationFrame(frame);
    }

    /*
      监听挂在 window 而不是首屏上。挂在首屏上的话，指针一移出去事件就断了，
      cx/cy 会停在最后一个"还在里面"的位置，循环于是永远以为指针没走，
      网格再也淡不掉。"在不在首屏里"由 frame() 每帧重新判断——
      这样滚动把首屏移出视口、指针却没动的情况也能一并覆盖。
    */
    window.addEventListener('pointermove', function (e) {
      cx = e.clientX;
      cy = e.clientY;
      // 循环已经停着时，只有落在首屏内才值得把它叫起来
      if (!running) {
        var r = hero.getBoundingClientRect();
        if (cx < r.left || cx > r.right || cy < r.top || cy > r.bottom) return;
      }
      wake();
    }, { passive: true });

    var resizing = false;
    window.addEventListener('resize', function () {
      if (resizing) return;
      resizing = true;
      window.requestAnimationFrame(function () {
        resizing = false;
        resize();
        wake();
      });
    });

    resize();
    window.addEventListener('load', resize);
  })();

  /* ---------- 7. 关键数据滚动计数 ---------- */
  (function countUpStats() {
    var nums = Array.prototype.slice.call(document.querySelectorAll('.stat-num'));
    if (!nums.length) return;

    // HTML 里已经写死最终值：JS 不参与时页面依然正确
    if (prefersReduced || !('IntersectionObserver' in window)) return;

    var items = [];
    nums.forEach(function (el) {
      var raw = el.textContent.trim();
      if (!/^\d+$/.test(raw)) return;                 // 非纯数字（如"A"）保持原样
      var target = parseInt(raw, 10);
      items.push({
        el: el,
        target: target,
        // 年份从 30 年前爬起，比从 0 翻到 2015 更自然
        from: target >= 1000 ? target - 30 : 0
      });
    });
    if (!items.length) return;

    function run(item) {
      var start = 0;
      var dur = 1150;
      function tick(now) {
        if (!start) start = now;
        var t = Math.min(1, (now - start) / dur);
        var eased = 1 - Math.pow(1 - t, 3);           // easeOutCubic
        if (t < 1) {
          item.el.textContent = String(Math.round(item.from + (item.target - item.from) * eased));
          window.requestAnimationFrame(tick);
        } else {
          item.el.textContent = String(item.target);
        }
      }
      window.requestAnimationFrame(tick);
    }

    var itemByEl = new Map();
    items.forEach(function (item) { itemByEl.set(item.el, item); });

    var counterObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        counterObserver.unobserve(entry.target);
        var item = itemByEl.get(entry.target);
        if (item) run(item);
      });
    }, { threshold: 0.5 });

    items.forEach(function (item) { counterObserver.observe(item.el); });
  })();

  /* ---------- 8. 卡片指针光晕 ---------- */
  (function pointerGlow() {
    if (prefersReduced) return;
    if (!window.matchMedia ||
        !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    var SEL = '.card, .feature, .honor, .contact-card';
    var pending = null;
    var queued = false;

    function apply() {
      queued = false;
      if (!pending) return;
      var target = pending.el;
      var r = target.getBoundingClientRect();
      target.style.setProperty('--mx', (pending.x - r.left) + 'px');
      target.style.setProperty('--my', (pending.y - r.top) + 'px');
      pending = null;
    }

    document.addEventListener('pointermove', function (e) {
      var el = e.target && e.target.closest ? e.target.closest(SEL) : null;
      if (!el) return;
      pending = { el: el, x: e.clientX, y: e.clientY };
      if (!queued) {
        queued = true;
        window.requestAnimationFrame(apply);
      }
    }, { passive: true });
  })();

  /* ---------- 9. 复制联系方式 ---------- */
  (function copyContact() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.copy-btn[data-copy]'));
    if (!buttons.length) return;

    // clipboard API 需要安全上下文（https / localhost），否则退回 execCommand
    function legacyCopy(text) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
      document.body.removeChild(ta);
      return ok;
    }

    function feedback(btn, ok) {
      var label = btn.querySelector('.copy-label');
      var card = btn.parentNode;
      var status = card ? card.querySelector('.copy-status') : null;

      btn.classList.toggle('is-done', ok);
      if (label) label.textContent = ok ? '已复制' : '复制失败';
      if (status) status.textContent = ok ? '已复制到剪贴板' : '复制失败，请手动选择文本';

      window.clearTimeout(btn.copyTimer);
      btn.copyTimer = window.setTimeout(function () {
        btn.classList.remove('is-done');
        if (label) label.textContent = '复制';
        if (status) status.textContent = '';
      }, 1800);
    }

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var text = btn.getAttribute('data-copy') || '';
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(
            function () { feedback(btn, true); },
            function () { feedback(btn, legacyCopy(text)); }
          );
        } else {
          feedback(btn, legacyCopy(text));
        }
      });
    });
  })();
})();
