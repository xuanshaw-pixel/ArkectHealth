/* ========================================
   Arkect Health - 圣链健康
   Interactive JavaScript
   ======================================== */

document.addEventListener('DOMContentLoaded', function() {

  // ---------- Page Loader ----------
  const loader = document.querySelector('.page-loader');
  if (loader) {
    window.addEventListener('load', function() {
      setTimeout(function() {
        loader.classList.add('fade-out');
        setTimeout(function() {
          loader.style.display = 'none';
        }, 500);
      }, 600);
    });
  }

  // ---------- Navbar Scroll Effect ----------
  const navbar = document.querySelector('.navbar');
  function handleNavScroll() {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
      navbar.classList.remove('transparent');
    } else {
      navbar.classList.remove('scrolled');
      if (navbar.classList.contains('transparent') || navbar.dataset.transparent !== undefined) {
        navbar.classList.add('transparent');
      }
    }
  }
  window.addEventListener('scroll', handleNavScroll);
  handleNavScroll();

  // ---------- Mobile Navigation ----------
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', function() {
      navLinks.classList.toggle('active');
      // Animate hamburger
      const spans = navToggle.querySelectorAll('span');
      if (navLinks.classList.contains('active')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
      } else {
        spans[0].style.transform = '';
        spans[1].style.opacity = '';
        spans[2].style.transform = '';
      }
    });

    // Close mobile nav on link click
    navLinks.querySelectorAll('a:not(.nav-dropdown > a)').forEach(function(link) {
      link.addEventListener('click', function() {
        navLinks.classList.remove('active');
        const spans = navToggle.querySelectorAll('span');
        spans[0].style.transform = '';
        spans[1].style.opacity = '';
        spans[2].style.transform = '';
      });
    });

    // Mobile dropdown toggle
    document.querySelectorAll('.nav-dropdown > a').forEach(function(dropdownLink) {
      dropdownLink.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
          e.preventDefault();
          this.parentElement.classList.toggle('open');
        }
      });
    });
  }

  // ---------- Scroll Animations ----------
  const animateElements = document.querySelectorAll('.animate-on-scroll, .animate-from-left, .animate-from-right, .animate-scale');

  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('animated');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  animateElements.forEach(function(el) {
    observer.observe(el);
  });

  // ---------- Counter Animation ----------
  const counters = document.querySelectorAll('.counter');

  function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    const suffix = el.dataset.suffix || '';
    const duration = 2000;
    const start = 0;
    const startTime = performance.now();

    function updateCounter(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + (target - start) * eased);
      el.textContent = current.toLocaleString() + suffix;
      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      }
    }

    requestAnimationFrame(updateCounter);
  }

  const counterObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(function(counter) {
    counterObserver.observe(counter);
  });

  // ---------- Back to Top Button ----------
  const backToTop = document.querySelector('.floating-btn.top');

  if (backToTop) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 500) {
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
      }
    });

    backToTop.addEventListener('click', function() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // ---------- WeChat QR Popup ----------
  const wechatBtn = document.querySelector('.floating-btn.wechat');
  const wechatPopup = document.querySelector('.wechat-popup');

  if (wechatBtn && wechatPopup) {
    wechatBtn.addEventListener('click', function() {
      wechatPopup.classList.toggle('show');
    });

    // Close popup when clicking outside
    document.addEventListener('click', function(e) {
      if (!wechatBtn.contains(e.target) && !wechatPopup.contains(e.target)) {
        wechatPopup.classList.remove('show');
      }
    });
  }

  // ---------- Smooth Scroll for Anchor Links ----------
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        const navHeight = navbar.offsetHeight;
        const targetPosition = targetEl.getBoundingClientRect().top + window.pageYOffset - navHeight;
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // ---------- Specialty Tag Filter ----------
  document.querySelectorAll('.specialty-tag').forEach(function(tag) {
    tag.addEventListener('click', function() {
      // Toggle active state
      document.querySelectorAll('.specialty-tag').forEach(function(t) {
        t.classList.remove('active');
      });
      this.classList.add('active');

      // Filter doctors if on doctors page
      const specialty = this.dataset.specialty;
      const doctorCards = document.querySelectorAll('.doctor-card');
      
      if (doctorCards.length > 0) {
        doctorCards.forEach(function(card) {
          if (specialty === 'all' || card.dataset.specialty === specialty) {
            card.style.display = '';
            card.style.animation = 'fadeInUp 0.4s ease forwards';
          } else {
            card.style.display = 'none';
          }
        });
      }
    });
  });

  // ---------- Case Study Filter ----------
  document.querySelectorAll('.case-filter-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.case-filter-btn').forEach(function(b) {
        b.classList.remove('active');
      });
      this.classList.add('active');

      const filter = this.dataset.filter;
      const caseCards = document.querySelectorAll('.case-card');

      if (caseCards.length > 0) {
        caseCards.forEach(function(card) {
          if (filter === 'all' || card.dataset.category === filter) {
            card.style.display = '';
            card.style.animation = 'fadeInUp 0.4s ease forwards';
          } else {
            card.style.display = 'none';
          }
        });
      }
    });
  });

  // ---------- Contact Form Validation ----------
  const contactForm = document.querySelector('#contact-form');
  
  if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      let isValid = true;
      const requiredFields = contactForm.querySelectorAll('[required]');
      
      requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
          isValid = false;
          field.style.borderColor = '#e74c3c';
          field.addEventListener('input', function() {
            this.style.borderColor = '';
          }, { once: true });
        }
      });

      // Email validation
      const emailField = contactForm.querySelector('input[type="email"]');
      if (emailField && emailField.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailField.value)) {
          isValid = false;
          emailField.style.borderColor = '#e74c3c';
        }
      }

      if (isValid) {
        // Submit form to Formspree via fetch
        const submitBtn = contactForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = '提交中...';
        submitBtn.disabled = true;

        const formData = new FormData(contactForm);

        fetch(contactForm.action, {
          method: 'POST',
          body: formData,
          headers: { 'Accept': 'application/json' }
        })
        .then(function(response) {
          if (response.ok) {
            submitBtn.textContent = '✓ 提交成功！';
            submitBtn.style.background = '#27ae60';
            submitBtn.style.borderColor = '#27ae60';
            contactForm.reset();
            setTimeout(function() {
              submitBtn.textContent = originalText;
              submitBtn.style.background = '';
              submitBtn.style.borderColor = '';
              submitBtn.disabled = false;
            }, 4000);
          } else {
            return response.json().then(function(data) {
              throw new Error(data.errors ? data.errors.map(function(e) { return e.message; }).join(', ') : '提交失败');
            });
          }
        })
        .catch(function(error) {
          submitBtn.textContent = '提交失败，请重试';
          submitBtn.style.background = '#e74c3c';
          submitBtn.style.borderColor = '#e74c3c';
          setTimeout(function() {
            submitBtn.textContent = originalText;
            submitBtn.style.background = '';
            submitBtn.style.borderColor = '';
            submitBtn.disabled = false;
          }, 3000);
        });
      }
    });
  }

  // ---------- Parallax effect on hero decoration ----------
  const heroDecoration = document.querySelector('.hero-decoration');
  
  if (heroDecoration) {
    window.addEventListener('scroll', function() {
      const scrolled = window.scrollY;
      if (scrolled < window.innerHeight) {
        heroDecoration.style.transform = 'translateY(-50%) translateX(' + (scrolled * 0.05) + 'px)';
      }
    });
  }

  // ---------- Active Navigation Highlight ----------
  function setActiveNav() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach(function(link) {
      const href = link.getAttribute('href');
      if (href === currentPage || (currentPage === '' && href === 'index.html')) {
        link.classList.add('active');
      }
    });
  }
  setActiveNav();

  // ---------- Process Step Interactive ----------
  document.querySelectorAll('.process-horizontal .step-item').forEach(function(step) {
    step.addEventListener('click', function() {
      document.querySelectorAll('.process-horizontal .step-item').forEach(function(s) {
        s.querySelector('.step-num').style.background = '';
        s.querySelector('.step-num').style.color = '';
      });
      this.querySelector('.step-num').style.background = 'var(--gold)';
      this.querySelector('.step-num').style.color = 'var(--navy)';
    });
  });

  // ---------- Insights Tab Switching ----------
  document.querySelectorAll('.insights-tab-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      // Update active tab button
      document.querySelectorAll('.insights-tab-btn').forEach(function(b) {
        b.classList.remove('active');
      });
      this.classList.add('active');

      // Show corresponding tab content
      var tabId = 'tab-' + this.dataset.tab;
      document.querySelectorAll('.insights-tab-content').forEach(function(content) {
        content.classList.remove('active');
      });
      var targetTab = document.getElementById(tabId);
      if (targetTab) {
        targetTab.classList.add('active');
        // Re-observe animations for newly visible elements
        targetTab.querySelectorAll('.animate-on-scroll, .animate-from-left, .animate-from-right, .animate-scale').forEach(function(el) {
          el.classList.remove('animated');
          observer.observe(el);
        });
      }
    });
  });

  // ---------- FAQ Accordion ----------
  document.querySelectorAll('.faq-question').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const item = this.closest('.faq-item');
      const answer = item.querySelector('.faq-answer');
      const isActive = item.classList.contains('active');

      // Close all other items
      document.querySelectorAll('.faq-item').forEach(function(otherItem) {
        if (otherItem !== item) {
          otherItem.classList.remove('active');
          var otherAnswer = otherItem.querySelector('.faq-answer');
          if (otherAnswer) otherAnswer.style.maxHeight = null;
        }
      });

      // Toggle current item
      if (isActive) {
        item.classList.remove('active');
        answer.style.maxHeight = null;
      } else {
        item.classList.add('active');
        answer.style.maxHeight = answer.scrollHeight + 'px';
      }
    });
  });

});

// ---------- Fade In Up Animation Keyframes (for JS-triggered animations) ----------
const style = document.createElement('style');
style.textContent = '@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }';
document.head.appendChild(style);