/* ============================================
   圣链健康 — 资讯分享·康复纪实 动态文章渲染
   文件位置: js/cases-articles.js
   功能：从 ARTICLES 数据渲染卡片、分类筛选、跳转详情
   ============================================ */

(function () {
  'use strict';

  if (typeof ARTICLES === 'undefined' || !ARTICLES.length) {
    // 没有文章数据时显示占位提示
    var grid = document.getElementById('articlesGrid');
    if (grid) {
      grid.innerHTML = '<p style="text-align:center;color:var(--text-light);padding:60px 0;">暂无文章，敬请期待</p>';
    }
    return;
  }

  /* ---------- 分类提取与排序 ---------- */
  var categoryOrder = ['慢病管理', '远程问诊', '赴英就医', '留学生服务', '干货分享'];
  var counts = {};
  ARTICLES.forEach(function (a) {
    counts[a.category] = (counts[a.category] || 0) + 1;
  });

  // 按预定义顺序排列，未在列表中的追加到末尾
  var categories = categoryOrder.filter(function (c) { return counts[c]; });
  Object.keys(counts).forEach(function (c) {
    if (categories.indexOf(c) === -1) categories.push(c);
  });

  /* ---------- 渲染筛选按钮 ---------- */
  var filtersEl = document.getElementById('articleFilters');
  if (filtersEl) {
    var allBtn = document.createElement('button');
    allBtn.className = 'case-filter-btn active';
    allBtn.setAttribute('data-filter', 'all');
    allBtn.textContent = '全部 (' + ARTICLES.length + ')';
    filtersEl.appendChild(allBtn);

    categories.forEach(function (cat) {
      var btn = document.createElement('button');
      btn.className = 'case-filter-btn';
      btn.setAttribute('data-filter', cat);
      btn.textContent = cat + ' (' + counts[cat] + ')';
      filtersEl.appendChild(btn);
    });
  }

  /* ---------- 渲染文章卡片 ---------- */
  var grid = document.getElementById('articlesGrid');
  if (!grid) return;

  // 按日期倒序
  var sorted = ARTICLES.slice().sort(function (a, b) {
    return (b.date || '').localeCompare(a.date || '');
  });

  sorted.forEach(function (article, idx) {
    var catSlug = article.category;
    var card = document.createElement('a');
    card.href = 'consultation/' + article.id + '.html';
    card.className = 'case-card animate-on-scroll delay-' + ((idx % 3) + 1);
    card.setAttribute('data-category', catSlug);
    card.setAttribute('data-id', article.id);

    // 图片区域
    var imgHtml = '';
    if (article.image && article.image !== 'None') {
      imgHtml = '<div class="case-image"><img loading="lazy" src="' + article.image + '" alt="' + (article.title || '') + '" onerror="this.style.display=\'none\';this.parentElement.classList.add(\'no-image\');"><div class="case-image-fallback"><svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h2v5zm0 4h-2v-2h2v2z"/></svg></div></div>';
    } else {
      imgHtml = '<div class="case-image no-image"><div class="case-image-fallback"><svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h2v5zm0 4h-2v-2h2v2z"/></svg></div></div>';
    }

    // 日期格式化
    var dateStr = article.date || '';
    if (dateStr) {
      var parts = dateStr.split('-');
      if (parts.length >= 2) dateStr = parts[0] + '年' + parseInt(parts[1]) + '月';
    }

    card.innerHTML = imgHtml +
      '<div class="case-tag">' + (article.category || '') + '</div>' +
      '<h4>' + (article.title || '') + '</h4>' +
      (dateStr ? '<div class="case-meta"><span>' + dateStr + '</span></div>' : '') +
      '<p>' + (article.summary || '') + '</p>';

    grid.appendChild(card);
  });

  /* ---------- 分类筛选 ---------- */
  if (filtersEl) {
    filtersEl.addEventListener('click', function (e) {
      var btn = e.target.closest('.case-filter-btn');
      if (!btn) return;

      var filter = btn.getAttribute('data-filter');

      // 高亮按钮
      filtersEl.querySelectorAll('.case-filter-btn').forEach(function (b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');

      // 筛选卡片
      var cards = grid.querySelectorAll('.case-card');
      var visibleCount = 0;
      cards.forEach(function (card) {
        var cardCat = card.getAttribute('data-category');
        if (filter === 'all' || cardCat === filter) {
          card.style.display = '';
          card.style.opacity = '0';
          card.style.transform = 'translateY(20px)';
          (function (c, delay) {
            setTimeout(function () {
              c.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
              c.style.opacity = '1';
              c.style.transform = 'translateY(0)';
            }, delay);
          })(card, visibleCount * 80);
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });

      // 保存选中分类
      try { sessionStorage.setItem('arkect_article_category', filter); } catch (ex) {}

      // 滚动到列表区
      if (grid && visibleCount > 0) {
        var rect = grid.getBoundingClientRect();
        if (rect.top < -100 || rect.top > window.innerHeight) {
          window.scrollTo({ top: grid.offsetTop - 100, behavior: 'smooth' });
        }
      }
    });
  }

  /* ---------- URL hash / sessionStorage 自动选中分类 ---------- */
  var hash = window.location.hash.replace('#', '');
  if (hash) {
    var targetBtn = filtersEl && filtersEl.querySelector('.case-filter-btn[data-filter="' + hash + '"]');
    if (targetBtn) targetBtn.click();
  } else {
    try {
      var saved = sessionStorage.getItem('arkect_article_category');
      if (saved && saved !== 'all') {
        var savedBtn = filtersEl && filtersEl.querySelector('.case-filter-btn[data-filter="' + saved + '"]');
        if (savedBtn) savedBtn.click();
      }
    } catch (ex) {}
  }

})();
