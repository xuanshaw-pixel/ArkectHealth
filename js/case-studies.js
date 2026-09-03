/* ============================================
   圣链健康 — 资讯分享页交互逻辑
   文件位置: js/case-studies.js
   功能：分类筛选、标签高亮、卡片跳转、交错动画
   ============================================ */

(function () {
  'use strict';

  var categoryTags = document.querySelectorAll('.category-tag');
  var articleCards = document.querySelectorAll('.article-card');
  var emptyState = document.getElementById('emptyState');
  var articlesGrid = document.getElementById('articlesGrid');

  /* ---------- 分类计数 ---------- */
  if (categoryTags.length > 0 && typeof ARTICLES !== 'undefined') {
    var counts = {};
    ARTICLES.forEach(function (a) {
      counts[a.category] = (counts[a.category] || 0) + 1;
    });
    categoryTags.forEach(function (tag) {
      var cat = tag.getAttribute('data-category');
      if (cat === '全部') {
        tag.textContent = '全部 (' + ARTICLES.length + ')';
      } else if (counts[cat]) {
        tag.textContent = cat + ' (' + counts[cat] + ')';
      }
    });
  }

  /* ---------- 分类筛选 ---------- */
  if (categoryTags.length > 0) {
    categoryTags.forEach(function (tag) {
      tag.addEventListener('click', function () {
        var selectedCategory = this.getAttribute('data-category');

        // 保存选中分类
        try { sessionStorage.setItem('hc_article_category', selectedCategory); } catch(e) {}

        // 高亮当前标签（带弹性动画）
        categoryTags.forEach(function (t) { t.classList.remove('active'); });
        this.classList.add('active');
        this.style.transform = 'scale(1.08)';
        var self = this;
        setTimeout(function () { self.style.transform = ''; }, 200);

        // 筛选卡片（交错淡入）
        var visibleCount = 0;
        articleCards.forEach(function (card) {
          var cardCategory = card.getAttribute('data-category');
          if (selectedCategory === '全部' || cardCategory === selectedCategory) {
            card.style.display = '';
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            (function(c, delay) {
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

        // 空状态
        if (emptyState) {
          emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
        }

        // 平滑滚动到列表区
        if (articlesGrid) {
          var rect = articlesGrid.getBoundingClientRect();
          if (rect.top < -100 || rect.top > window.innerHeight) {
            window.scrollTo({ top: articlesGrid.offsetTop - 100, behavior: 'smooth' });
          }
        }
      });
    });
  }

  /* ---------- 卡片点击跳转（非 <a> 标签时） ---------- */
  articleCards.forEach(function (card) {
    if (card.tagName === 'A') return;
    card.addEventListener('click', function () {
      var articleId = this.getAttribute('data-id');
      if (articleId) {
        window.location.href = '../consultation/' + encodeURIComponent(articleId) + '.html';
      }
    });
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'link');
    card.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this.click(); }
    });
  });

  /* ---------- URL hash / sessionStorage 自动选中分类 ---------- */
  var hash = window.location.hash.replace('#', '');
  if (hash) {
    var targetTag = document.querySelector('.category-tag[data-category="' + hash + '"]');
    if (targetTag) targetTag.click();
  } else {
    try {
      var saved = sessionStorage.getItem('hc_article_category');
      if (saved && saved !== '全部') {
        var savedTag = document.querySelector('.category-tag[data-category="' + saved + '"]');
        if (savedTag) savedTag.click();
      }
    } catch(e) {}
  }

})();
