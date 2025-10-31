// Blog JavaScript - Modern, Interactive, and Feature-Rich

(function() {
  "use strict";

  // DOM Content Loaded
  document.addEventListener('DOMContentLoaded', function() {
    initBlog();
  });

  function initBlog() {
    // Initialize all blog features
    initParticleSystem();
    initThemeToggle();
    initBannerSlider();
    initTrendingSlider();
    initArticlesSlider();
    initSearchModal();
    initMenuModal();
    initScrollToTop();
    initNewsletterForm();
    initSmoothScrolling();
    initAnimations();
    initCardLinks();
  }

  // Particle System for Hero Section
  function initParticleSystem() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let particles = [];
    let animationId;

    function resizeCanvas() {
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    }

    function createParticle(x, y) {
      return {
        x: x || Math.random() * canvas.width,
        y: y || Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 4 + 2,
        life: Math.random() * 100 + 50,
        maxLife: Math.random() * 100 + 50,
        color: getCurrentThemeColor()
      };
    }

    function getCurrentThemeColor() {
      const isDark = document.documentElement.getAttribute('color-scheme') === 'dark';
      const colors = isDark ?
        ['rgba(206, 196, 239, 0.6)', 'rgba(228, 184, 191, 0.6)', 'rgba(104, 103, 105, 0.4)'] :
        ['rgba(13, 37, 85, 0.6)', 'rgba(228, 184, 191, 0.6)', 'rgba(7, 0, 17, 0.4)'];
      return colors[Math.floor(Math.random() * colors.length)];
    }

    function initParticles() {
      particles = [];
      const particleCount = Math.min(120, Math.floor((canvas.width * canvas.height) / 8000));

      for (let i = 0; i < particleCount; i++) {
        particles.push(createParticle());
      }
    }

    function updateParticles() {
      particles.forEach((particle, index) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.life--;

        // Wrap around edges
        if (particle.x < 0) particle.x = canvas.width;
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = canvas.height;
        if (particle.y > canvas.height) particle.y = 0;

        // Mouse interaction - stronger attraction
        const mouseX = window.mouseX || canvas.width / 2;
        const mouseY = window.mouseY || canvas.height / 2;
        const dx = mouseX - particle.x;
        const dy = mouseY - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 150) {
          const force = (150 - distance) / 150;
          particle.vx += (dx / distance) * force * 0.02;
          particle.vy += (dy / distance) * force * 0.02;
        }

        // Add some organic movement
        particle.vx += (Math.random() - 0.5) * 0.01;
        particle.vy += (Math.random() - 0.5) * 0.01;

        // Limit velocity
        const maxSpeed = 1;
        const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
        if (speed > maxSpeed) {
          particle.vx = (particle.vx / speed) * maxSpeed;
          particle.vy = (particle.vy / speed) * maxSpeed;
        }

        // Respawn dead particles
        if (particle.life <= 0) {
          particles[index] = createParticle();
        }
      });
    }

    function drawParticles() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach(particle => {
        const alpha = particle.life / particle.maxLife;
        ctx.globalAlpha = alpha;

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.fill();

        // Draw connections between nearby particles
        particles.forEach(otherParticle => {
          if (particle !== otherParticle) {
            const dx = particle.x - otherParticle.x;
            const dy = particle.y - otherParticle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 120) {
              ctx.globalAlpha = (120 - distance) / 120 * alpha * 0.5;
              ctx.beginPath();
              ctx.moveTo(particle.x, particle.y);
              ctx.lineTo(otherParticle.x, otherParticle.y);
              ctx.strokeStyle = particle.color;
              ctx.lineWidth = 1;
              ctx.stroke();
            }
          }
        });
      });

      ctx.globalAlpha = 1;
    }

    function animate() {
      updateParticles();
      drawParticles();
      animationId = requestAnimationFrame(animate);
    }

    // Track mouse position
    document.addEventListener('mousemove', (e) => {
      const rect = canvas.getBoundingClientRect();
      window.mouseX = e.clientX - rect.left;
      window.mouseY = e.clientY - rect.top;
    });

    // Initialize
    resizeCanvas();
    initParticles();
    animate();

    // Handle resize
    window.addEventListener('resize', () => {
      resizeCanvas();
      initParticles();
    });

    // Update colors when theme changes
    const observer = new MutationObserver(() => {
      particles.forEach(particle => {
        particle.color = getCurrentThemeColor();
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['color-scheme']
    });
  }

  // Theme Toggle Functionality
  function initThemeToggle() {
    const themeBtn = document.getElementById('themeToggle');
    const menuThemeBtn = document.getElementById('menuThemeToggle');

    if (!themeBtn) return;

    function getCurrentTheme() {
      let theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      localStorage.getItem('blog.theme') ? theme = localStorage.getItem('blog.theme') : null;
      return theme;
    }

    function loadTheme(theme) {
      const root = document.documentElement;
      if (theme === "light") {
        if (themeBtn) themeBtn.innerHTML = '<i class="ph-bold ph-sun"></i>';
        if (menuThemeBtn) menuThemeBtn.innerHTML = '<i class="ph-bold ph-sun"></i>';
        root.setAttribute('color-scheme', 'light');
      } else {
        if (themeBtn) themeBtn.innerHTML = '<i class="ph-bold ph-moon-stars"></i>';
        if (menuThemeBtn) menuThemeBtn.innerHTML = '<i class="ph-bold ph-moon-stars"></i>';
        root.setAttribute('color-scheme', 'dark');
      }
      root.setAttribute('data-theme', theme);
    }

    // Theme toggle click handlers
    [themeBtn, menuThemeBtn].forEach(btn => {
      if (btn) {
        btn.addEventListener('click', () => {
          let theme = getCurrentTheme();
          theme = theme === 'dark' ? 'light' : 'dark';
          localStorage.setItem('blog.theme', theme);
          loadTheme(theme);
        });
      }
    });

    // Load initial theme
    loadTheme(getCurrentTheme());
  }

  // Banner Slider Functionality
  function initBannerSlider() {
    const slider = document.getElementById('bannerSlider');
    const prevBtn = document.getElementById('bannerPrev');
    const nextBtn = document.getElementById('bannerNext');
    const dotsContainer = document.getElementById('bannerDots');

    if (!slider || !prevBtn || !nextBtn) return;

    const slides = slider.querySelectorAll('.banner-slide');
    let currentSlide = 0;
    let autoSlideInterval;

    // Create dots
    for (let i = 0; i < slides.length; i++) {
      const dot = document.createElement('div');
      dot.className = 'slider-dot';
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => goToSlide(i));
      dotsContainer.appendChild(dot);
    }

    const dots = dotsContainer.querySelectorAll('.slider-dot');

    function updateDots() {
      dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
      });
    }

    function updateSlides() {
      slides.forEach((slide, index) => {
        slide.classList.toggle('active', index === currentSlide);
      });
    }

    function goToSlide(index) {
      currentSlide = index;
      slider.style.transform = `translateX(-${currentSlide * 33.333}%)`;
      updateDots();
      updateSlides();
    }

    function nextSlide() {
      currentSlide = (currentSlide + 1) % slides.length;
      goToSlide(currentSlide);
    }

    function prevSlide() {
      currentSlide = (currentSlide - 1 + slides.length) % slides.length;
      goToSlide(currentSlide);
    }

    // Event listeners
    nextBtn.addEventListener('click', nextSlide);
    prevBtn.addEventListener('click', prevSlide);

    // Auto slide every 4 seconds
    function startAutoSlide() {
      autoSlideInterval = setInterval(nextSlide, 4000);
    }

    function stopAutoSlide() {
      clearInterval(autoSlideInterval);
    }

    // Pause on hover
    slider.parentElement.addEventListener('mouseenter', stopAutoSlide);
    slider.parentElement.addEventListener('mouseleave', startAutoSlide);

    // Initialize first slide
    updateSlides();

    // Start auto slide
    startAutoSlide();
  }

  // Trending Slider Functionality
  function initTrendingSlider() {
    const slider = document.getElementById('trendingSlider');
    const prevBtn = document.getElementById('trendingPrev');
    const nextBtn = document.getElementById('trendingNext');
    const dotsContainer = document.getElementById('trendingDots');

    if (!slider || !prevBtn || !nextBtn) return;

    const slides = slider.querySelectorAll('.slide');
    let currentSlide = 0;
    let autoSlideInterval;

    // Create dots
    for (let i = 0; i < slides.length; i++) {
      const dot = document.createElement('div');
      dot.className = 'slider-dot';
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => goToSlide(i));
      dotsContainer.appendChild(dot);
    }

    const dots = dotsContainer.querySelectorAll('.slider-dot');

    function updateDots() {
      dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
      });
    }

    function updateSlides() {
      slides.forEach((slide, index) => {
        slide.classList.toggle('active', index === currentSlide);
      });
    }

    function goToSlide(index) {
      currentSlide = index;
      slider.style.transform = `translateX(-${currentSlide * 33.333}%)`;
      updateDots();
      updateSlides();
    }

    function updateSlides() {
      slides.forEach((slide, index) => {
        slide.classList.remove('active');
        if (index === currentSlide) {
          slide.classList.add('active');
        }
      });
    }

    function nextSlide() {
      currentSlide = (currentSlide + 1) % slides.length;
      goToSlide(currentSlide);
    }

    function prevSlide() {
      currentSlide = (currentSlide - 1 + slides.length) % slides.length;
      goToSlide(currentSlide);
    }

    // Event listeners
    nextBtn.addEventListener('click', nextSlide);
    prevBtn.addEventListener('click', prevSlide);

    // Auto slide
    function startAutoSlide() {
      autoSlideInterval = setInterval(nextSlide, 4000);
    }

    function stopAutoSlide() {
      clearInterval(autoSlideInterval);
    }

    // Pause on hover
    slider.parentElement.addEventListener('mouseenter', stopAutoSlide);
    slider.parentElement.addEventListener('mouseleave', startAutoSlide);

    // Initialize first slide
    updateSlides();

    // Start auto slide
    startAutoSlide();
  }

  // Articles Slider Functionality
  function initArticlesSlider() {
    const track = document.getElementById('articlesTrack');
    const prevBtn = document.getElementById('articlesPrev');
    const nextBtn = document.getElementById('articlesNext');

    if (!track || !prevBtn || !nextBtn) return;

    const cards = Array.from(track.children);
    let currentIndex = 0;
    const cardWidth = 340; // 320px card + 20px gap
    const visibleCards = 3;
    const totalCards = 6; // Fixed to 6 cards as requested

    // Ensure we have exactly 6 cards
    while (cards.length < totalCards) {
      const clone = cards[0].cloneNode(true);
      cards.push(clone);
      track.appendChild(clone);
    }

    // Clone first 3 cards for seamless infinite scroll
    for (let i = 0; i < visibleCards; i++) {
      const clone = cards[i].cloneNode(true);
      track.appendChild(clone);
    }

    function updateSlider() {
      const translateX = -currentIndex * cardWidth;
      track.style.transform = `translateX(${translateX}px)`;
    }

    function nextSlide() {
      if (currentIndex >= totalCards - visibleCards) {
        // At the end, jump back to start seamlessly
        track.style.transition = 'none';
        currentIndex = 0;
        updateSlider();
        setTimeout(() => {
          track.style.transition = 'transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          currentIndex = 1;
          updateSlider();
        }, 50);
      } else {
        currentIndex++;
        updateSlider();
      }
    }

    function prevSlide() {
      if (currentIndex <= 0) {
        // At the beginning, jump to end seamlessly
        track.style.transition = 'none';
        currentIndex = totalCards - visibleCards;
        updateSlider();
        setTimeout(() => {
          track.style.transition = 'transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          currentIndex = totalCards - visibleCards - 1;
          updateSlider();
        }, 50);
      } else {
        currentIndex--;
        updateSlider();
      }
    }

    nextBtn.addEventListener('click', nextSlide);
    prevBtn.addEventListener('click', prevSlide);

    // Auto slide every 4 seconds
    setInterval(nextSlide, 4000);
  }

  // Search Modal Functionality
  function initSearchModal() {
    const searchBtn = document.getElementById('searchToggle');
    const menuSearchBtn = document.getElementById('menuSearchToggle');
    const searchOverlay = document.getElementById('searchOverlay');
    const searchClose = document.getElementById('searchClose');
    const searchInput = document.getElementById('searchInput');
    const searchSubmit = document.getElementById('searchBtn');
    const searchResults = document.getElementById('searchResults');

    if (!searchBtn || !searchOverlay) return;

    function openSearch() {
      searchOverlay.classList.add('active');
      if (searchInput) searchInput.focus();
    }

    function closeSearch() {
      searchOverlay.classList.remove('active');
      if (searchInput) searchInput.value = '';
      searchResults.innerHTML = '<div class="no-results"><i class="ph-bold ph-magnifying-glass"></i><p>Start typing to search articles...</p></div>';
    }

    [searchBtn, menuSearchBtn].forEach(btn => {
      if (btn) btn.addEventListener('click', openSearch);
    });

    if (searchClose) searchClose.addEventListener('click', closeSearch);
    searchOverlay.addEventListener('click', (e) => {
      if (e.target === searchOverlay) closeSearch();
    });

    // Search functionality
    function performSearch(query) {
      if (!query.trim()) {
        searchResults.innerHTML = '<div class="no-results"><i class="ph-bold ph-magnifying-glass"></i><p>Start typing to search articles...</p></div>';
        return;
      }

      // Mock search results - replace with real API call
      const mockResults = [
        { title: 'Latest AI Models: A Comprehensive Guide', excerpt: 'Explore the most advanced AI models...', category: 'AI' },
        { title: 'Building Billion-Dollar Ideas', excerpt: 'Lessons from successful startups...', category: 'Innovation' },
        { title: 'Modern Web Technologies', excerpt: 'What every developer should know...', category: 'Development' }
      ].filter(item =>
        item.title.toLowerCase().includes(query.toLowerCase()) ||
        item.excerpt.toLowerCase().includes(query.toLowerCase())
      );

      if (mockResults.length === 0) {
        searchResults.innerHTML = '<div class="no-results"><i class="ph-bold ph-magnifying-glass"></i><p>No articles found matching your search.</p></div>';
        return;
      }

      searchResults.innerHTML = mockResults.map(result => `
        <div class="search-result-item" style="padding: 1rem; border-bottom: 1px solid var(--stroke-elements); cursor: pointer;">
          <div style="font-weight: 600; color: var(--t-bright); margin-bottom: 0.5rem;">${result.title}</div>
          <div style="color: var(--t-medium); font-size: 0.9rem; margin-bottom: 0.5rem;">${result.excerpt}</div>
          <div style="color: var(--accent); font-size: 0.8rem; font-weight: 600;">${result.category}</div>
        </div>
      `).join('');
    }

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        performSearch(e.target.value);
      });
    }

    if (searchSubmit) {
      searchSubmit.addEventListener('click', () => {
        performSearch(searchInput.value);
      });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === '/' && !searchOverlay.classList.contains('active')) {
        e.preventDefault();
        openSearch();
      }
      if (e.key === 'Escape' && searchOverlay.classList.contains('active')) {
        closeSearch();
      }
    });
  }

  // Mobile Menu Modal Functionality
  function initMenuModal() {
    const menuBtn = document.getElementById('mobileMenuToggle');
    const menuOverlay = document.getElementById('menuOverlay');
    const menuClose = document.getElementById('menuClose');

    if (!menuBtn || !menuOverlay) return;

    function openMenu() {
      menuOverlay.classList.add('active');
    }

    function closeMenu() {
      menuOverlay.classList.remove('active');
    }

    menuBtn.addEventListener('click', openMenu);
    if (menuClose) menuClose.addEventListener('click', closeMenu);
    menuOverlay.addEventListener('click', (e) => {
      if (e.target === menuOverlay) closeMenu();
    });

    // Close menu when clicking nav links
    const navLinks = menuOverlay.querySelectorAll('.mobile-nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', closeMenu);
    });
  }

  // Scroll to Top Functionality
  function initScrollToTop() {
    const scrollBtn = document.getElementById('scrollToTop');
    const progressRing = document.getElementById('scrollProgress');

    if (!scrollBtn) return;

    function updateScrollProgress() {
      const scrollTop = window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = (scrollTop / docHeight) * 100;

      if (progressRing) {
        progressRing.style.background = `conic-gradient(var(--secondary) ${scrollPercent}%, transparent ${scrollPercent}%)`;
      }

      // Show/hide button
      if (scrollTop > 300) {
        scrollBtn.classList.add('visible');
      } else {
        scrollBtn.classList.remove('visible');
      }
    }

    function scrollToTop() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }

    window.addEventListener('scroll', updateScrollProgress);
    scrollBtn.addEventListener('click', scrollToTop);
  }

  // Newsletter Form Functionality
  function initNewsletterForm() {
    const form = document.getElementById('newsletterForm');
    const message = document.getElementById('newsletterMessage');
    const submitBtn = document.getElementById('subscribeBtn');
    const btnText = submitBtn.querySelector('.btn-text');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const name = document.getElementById('subscriberName').value;
      const email = document.getElementById('subscriberEmail').value;

      // Basic validation
      if (!name.trim() || !email.trim()) {
        showMessage('Please fill in all fields.', 'error');
        return;
      }

      if (!isValidEmail(email)) {
        showMessage('Please enter a valid email address.', 'error');
        return;
      }

      // Show loading state
      submitBtn.disabled = true;
      btnText.textContent = 'Subscribing...';

      try {
        // Mock API call - replace with real endpoint
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Success
        showMessage('Thank you for subscribing! Check your email for confirmation.', 'success');
        form.reset();

      } catch (error) {
        showMessage('Something went wrong. Please try again.', 'error');
      } finally {
        submitBtn.disabled = false;
        btnText.textContent = 'Subscribe';
      }
    });

    function showMessage(text, type) {
      message.textContent = text;
      message.className = `newsletter-message ${type}`;
      message.style.display = 'block';

      setTimeout(() => {
        message.style.display = 'none';
      }, 5000);
    }

    function isValidEmail(email) {
      const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return regex.test(email);
    }
  }

  // Smooth Scrolling
  function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
      link.addEventListener('click', (e) => {
        const targetId = link.getAttribute('href');
        const targetElement = document.querySelector(targetId);

        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  // Card Link Click Handler
  function initCardLinks() {
    document.querySelectorAll('.card-link, .post-link, .slide-link, .banner-link, .tag-item').forEach(card => {
      card.addEventListener('click', function(e) {
        const href = this.getAttribute('data-href');
        if (href) {
          window.location.href = href;
        }
      });
    });
  }

  // Animation Triggers
  function initAnimations() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
        }
      });
    }, observerOptions);

    // Observe elements for animation
    const animateElements = document.querySelectorAll('.article-card, .featured-post, .large-post, .sidebar-widget');
    animateElements.forEach(el => observer.observe(el));
  }

  // Utility Functions
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    }
  }

  // Performance optimizations
  window.addEventListener('load', () => {
    // Preload critical resources
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => {
      img.src = img.dataset.src;
    });
  });

  // Error handling
  window.addEventListener('error', (e) => {
    console.error('Blog JavaScript Error:', e.error);
  });

  // Service worker registration (for PWA features)
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      // Register service worker when ready
      // navigator.serviceWorker.register('/sw.js');
    });
  }

})();