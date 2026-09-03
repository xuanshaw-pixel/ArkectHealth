/* ============================================
   圣链健康 — 资讯分享 筛选交互
   文件位置: js/cases-articles.js
   功能：为各 Tab 的筛选按钮绑定点击事件
   文章卡片已由 build-articles.py 静态注入 cases.html
   ============================================ */

(function () {
  'use strict';

  /* ---------- 每个 Tab 的筛选容器与对应 Grid ---------- */
  var tabConfig = [
    { filterId: 'articleFilters',     gridId: 'articlesGrid'     },
    { filterId: 'frontierFilters',    gridId: 'frontierGrid'      },
    { filterId: 'ukNewsFilters',      gridId: 'ukNewsGrid'        },
    { filterId: 'ukKnowledgeFilters', gridId: 'ukKnowledgeGrid'   }
  ];

  tabConfig.forEach(function (tab) {
    var filtersEl = document.getElementById(tab.filterId);
    var grid = document.getElementById(tab.gridId);
    if (!filtersEl || !grid) return;

    /* ---------- 筛选点击 ---------- */
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
    });
  });

  /* ---------- URL hash / sessionStorage 自动选中分类（仅康复纪实） ---------- */
  var mainFilters = document.getElementById('articleFilters');
  var hash = window.location.hash.replace('#', '');
  if (hash && mainFilters) {
    var targetBtn = mainFilters.querySelector('.case-filter-btn[data-filter="' + hash + '"]');
    if (targetBtn) targetBtn.click();
  } else {
    try {
      var saved = sessionStorage.getItem('arkect_article_category');
      if (saved && saved !== 'all' && mainFilters) {
        var savedBtn = mainFilters.querySelector('.case-filter-btn[data-filter="' + saved + '"]');
        if (savedBtn) savedBtn.click();
      }
    } catch (ex) {}
  }

})();
