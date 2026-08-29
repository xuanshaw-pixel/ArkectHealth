/* ============================================
   圣链健康官方网站 - 主脚本
   文件位置: js/main.js
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Navbar Scroll Effect ---------- */
  const navbar = document.querySelector('.navbar');
  const scrollTopBtn = document.querySelector('.scroll-top');

  function handleScroll() {
    const scrollY = window.scrollY;

    // Navbar background
    if (scrollY > 60) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }

    // Scroll to top button
    if (scrollTopBtn) {
      if (scrollY > 500) {
        scrollTopBtn.classList.add('visible');
      } else {
        scrollTopBtn.classList.remove('visible');
      }
    }
  }

  window.addEventListener('scroll', handleScroll);
  handleScroll(); // Run once on load

  /* ---------- Scroll to Top ---------- */
  if (scrollTopBtn) {
    scrollTopBtn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- Mobile Navigation ---------- */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', function () {
      navLinks.classList.toggle('active');
      // Animate hamburger
      navToggle.classList.toggle('active');
    });

    // Close menu when clicking a link
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('active');
        navToggle.classList.remove('active');
      });
    });
  }

  /* ---------- Scroll Animations (Intersection Observer) ---------- */
  const animatedElements = document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right');

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.15,
      rootMargin: '0px 0px -50px 0px'
    });

    animatedElements.forEach(function (el) {
      observer.observe(el);
    });
  } else {
    // Fallback: show all elements
    animatedElements.forEach(function (el) {
      el.classList.add('visible');
    });
  }

  /* ---------- Counter Animation ---------- */
  const counterElements = document.querySelectorAll('[data-count]');
  
  if (counterElements.length > 0 && 'IntersectionObserver' in window) {
    const counterObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    counterElements.forEach(function (el) {
      counterObserver.observe(el);
    });
  }

  function animateCounter(el) {
    const target = parseInt(el.getAttribute('data-count'), 10);
    const duration = 2000;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + (target - start) * eased);

      el.textContent = current;

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        el.textContent = target;
      }
    }

    requestAnimationFrame(update);
  }

  /* ---------- Smooth Scroll for Anchor Links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;

      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        const navHeight = navbar.offsetHeight;
        const targetPosition = targetEl.getBoundingClientRect().top + window.scrollY - navHeight - 20;
        window.scrollTo({ top: targetPosition, behavior: 'smooth' });
      }
    });
  });

  /* ---------- Form Handling ---------- */
  const consultationForm = document.getElementById('consultationForm');
  
  if (consultationForm) {
    consultationForm.addEventListener('submit', function (e) {
      e.preventDefault();

      // Basic validation
      const formData = new FormData(consultationForm);
      let isValid = true;

      formData.forEach(function (value, key) {
        if (!value || value.trim() === '') {
          const input = consultationForm.querySelector('[name="' + key + '"]');
          if (input && input.required) {
            isValid = false;
            input.style.borderColor = '#e74c3c';
          }
        }
      });

      if (isValid) {
        // Show success message
        const submitBtn = consultationForm.querySelector('.btn-primary');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = '提交成功！';
        submitBtn.style.background = '#27ae60';
        submitBtn.disabled = true;

        setTimeout(function () {
          submitBtn.textContent = originalText;
          submitBtn.style.background = '';
          submitBtn.disabled = false;
          consultationForm.reset();
        }, 3000);
      }
    });

    // Reset border color on input focus
    consultationForm.querySelectorAll('input, select, textarea').forEach(function (input) {
      input.addEventListener('focus', function () {
        this.style.borderColor = '';
      });
    });
  }

  /* ---------- Parallax Subtle Effect on Hero ---------- */
  const heroSection = document.querySelector('.hero');
  const heroBg = document.querySelector('.hero-bg');

  if (heroSection && heroBg) {
    window.addEventListener('scroll', function () {
      const scrollY = window.scrollY;
      const heroHeight = heroSection.offsetHeight;

      if (scrollY < heroHeight) {
        const translateY = scrollY * 0.3;
        heroBg.style.transform = 'translateY(' + translateY + 'px)';
      }
    });
  }

  /* ---------- Active Navigation Highlight ---------- */
  const sections = document.querySelectorAll('section[id]');

  function highlightNav() {
    const scrollY = window.scrollY + 100;

    sections.forEach(function (section) {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
      const sectionId = section.getAttribute('id');

      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        const navLink = document.querySelector('.nav-links a[href="#' + sectionId + '"]');
        if (navLink) {
          document.querySelectorAll('.nav-links a').forEach(function (a) {
            a.style.color = '';
          });
          navLink.style.color = '#C9A96E';
        }
      }
    });
  }

  if (sections.length > 0) {
    window.addEventListener('scroll', highlightNav);
  }

});