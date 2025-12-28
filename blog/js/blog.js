// Blog JavaScript - Modern, Interactive, and Feature-Rich

(function () {
  "use strict";

  // Robust bootstrap: run once regardless of readyState timing
  (function bootstrap() {
    function start() {
      if (window.__blogInited) return;
      window.__blogInited = true;
      initBlog();
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', start, { once: true });
    } else {
      start();
    }
  })();

  function initBlog() {
    // Initialize all blog features (resilient to isolated failures)
    const safe = (fn, name) => {
      try { fn(); } catch (e) { console.error('Blog init error in', name || fn?.name, e); }
    };

    safe(initParticleSystem, 'initParticleSystem');
    safe(initThemeToggle, 'initThemeToggle');
    safe(initBannerSlider, 'initBannerSlider');
    safe(initTrendingSlider, 'initTrendingSlider');
    safe(initArticlesSlider, 'initArticlesSlider');
    safe(initSearchModal, 'initSearchModal');
    safe(initMenuModal, 'initMenuModal');
    safe(initScrollToTop, 'initScrollToTop');
    safe(initNewsletterForm, 'initNewsletterForm');
    safe(initSmoothScrolling, 'initSmoothScrolling');
    safe(initAnimations, 'initAnimations');
    safe(initCardLinks, 'initCardLinks');
    safe(initPostModal, 'initPostModal');
    safe(forceTextWrapping, 'forceTextWrapping');
  }

  // Force text wrapping for slide titles on mobile
  function forceTextWrapping() {
    const slideTitles = document.querySelectorAll('.slide-title-text');

    slideTitles.forEach(title => {
      // Force line breaks for long titles
      const text = title.textContent;
      if (text.length > 30) {
        // Insert line breaks at word boundaries
        const words = text.split(' ');
        let currentLine = '';
        let newText = '';

        words.forEach(word => {
          if ((currentLine + ' ' + word).length > 15) {
            newText += currentLine + '\n';
            currentLine = word;
          } else {
            currentLine += (currentLine ? ' ' : '') + word;
          }
        });
        newText += currentLine;

        title.innerHTML = newText.replace(/\n/g, '<br>');
      }
    });
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
    const themeBtn = document.getElementById('themeToggle') || document.getElementById('theme-toggle');
    const menuThemeBtn = document.getElementById('menuThemeToggle') || document.getElementById('menu-theme-toggle');

    // If neither exists, nothing to bind
    if (!themeBtn && !menuThemeBtn) return;

    function getCurrentTheme() {
      let theme =
        document.documentElement.getAttribute('color-scheme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      const saved = localStorage.getItem('blog.theme') || localStorage.getItem('color-scheme');
      if (saved) theme = saved;
      return theme;
    }

    function setIcons(theme) {
      const desired = theme === 'light' ? 'ph ph-sun' : 'ph ph-moon-stars';
      [themeBtn, menuThemeBtn].forEach(btn => {
        if (!btn) return;
        let iconEl = btn.querySelector('i');
        if (!iconEl) {
          iconEl = document.createElement('i');
          btn.innerHTML = '';
          btn.appendChild(iconEl);
        }
        iconEl.className = desired;
      });
      if (themeBtn) {
        themeBtn.setAttribute('aria-label', theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode');
      }
    }

    function loadTheme(theme) {
      const root = document.documentElement;
      // Persist to both keys for cross-script compatibility
      localStorage.setItem('blog.theme', theme);
      localStorage.setItem('color-scheme', theme);

      // Apply attribute + Tailwind dark class (some route pages rely on dark: variants)
      const isLight = theme === 'light';
      root.setAttribute('color-scheme', isLight ? 'light' : 'dark');
      root.setAttribute('data-theme', theme);
      if (isLight) {
        root.classList.remove('dark');
      } else {
        root.classList.add('dark');
      }
      // Inform the UA for form controls, etc.
      try { root.style.colorScheme = isLight ? 'light' : 'dark'; } catch (e) { /* no-op */ }

      setIcons(theme);
    }

    // Bind click handlers once per element (avoid duplicate bindings on SPA swaps)
    [themeBtn, menuThemeBtn].forEach(btn => {
      if (btn && !btn.dataset.bound) {
        btn.addEventListener('click', () => {
          if (typeof window.__toggleTheme === 'function') {
            window.__toggleTheme();
          } else {
            let theme = getCurrentTheme();
            theme = theme === 'dark' ? 'light' : 'dark';
            loadTheme(theme);
          }
        });
        btn.dataset.bound = 'true';
      }
    });

    // Additionally, delegate click so the toggle always works even if bindings are lost on SPA swaps
    // Avoid double-toggle if early bootstrap already installed a global handler
    if (!window.__themeBootstrap && !window.__themeDelegated) {
      document.addEventListener('click', (e) => {
        const tbtn = e.target.closest('#themeToggle, #theme-toggle, #menuThemeToggle, #menu-theme-toggle');
        if (tbtn) {
          if (typeof window.__toggleTheme === 'function') {
            window.__toggleTheme();
          } else {
            let theme = getCurrentTheme();
            theme = theme === 'dark' ? 'light' : 'dark';
            loadTheme(theme);
          }
        }
      }, true);
      window.__themeDelegated = true;
    }

    // Observe attribute changes (if any other script flips theme, keep icons in sync)
    const mo = new MutationObserver(() => setIcons(getCurrentTheme()));
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['color-scheme', 'class', 'data-theme'] });

    // Load initial theme
    loadTheme(getCurrentTheme());

    // Expose sync helper for SPA route swaps
    if (!window.ApplyThemeFromStorage) {
      window.ApplyThemeFromStorage = () => {
        try {
          const t = getCurrentTheme();
          if (typeof window.__applyTheme === 'function') {
            window.__applyTheme(t);
          } else {
            loadTheme(t);
          }
        } catch (e) { /* no-op */ }
      };
    }
  }

  // Banner Slider Functionality
  function initBannerSlider() {
    const slider = document.getElementById('bannerSlider');
    const prevBtn = document.getElementById('bannerPrev');
    const nextBtn = document.getElementById('bannerNext');
    const dotsContainer = document.getElementById('bannerDots');

    if (!slider || !prevBtn || !nextBtn) return;

    // Clean up existing state if re-initializing
    if (slider.autoSlideInterval) clearInterval(slider.autoSlideInterval);
    if (dotsContainer) dotsContainer.innerHTML = '';

    const slides = slider.querySelectorAll('.banner-slide');
    if (slides.length === 0) return;

    let currentSlide = 0;

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

    // Event listeners - use onclick to prevent duplicates on re-init
    nextBtn.onclick = nextSlide;
    prevBtn.onclick = prevSlide;

    // Auto slide every 4 seconds
    function startAutoSlide() {
      stopAutoSlide(); // Ensure we don't have multiple
      slider.autoSlideInterval = setInterval(nextSlide, 4000);
    }

    function stopAutoSlide() {
      if (slider.autoSlideInterval) {
        clearInterval(slider.autoSlideInterval);
        slider.autoSlideInterval = null;
      }
    }

    // Pause on hover
    slider.parentElement.onmouseenter = stopAutoSlide;
    slider.parentElement.onmouseleave = startAutoSlide;

    // Initialize first slide
    updateSlides();

    // Start auto slide
    startAutoSlide();
  }
  window.initBannerSlider = initBannerSlider;

  // Trending Slider Functionality
  function initTrendingSlider() {
    const slider = document.getElementById('trendingSlider');
    const prevBtn = document.getElementById('trendingPrev');
    const nextBtn = document.getElementById('trendingNext');
    const dotsContainer = document.getElementById('trendingDots');

    if (!slider || !prevBtn || !nextBtn) return;

    // Clean up
    if (slider.autoSlideInterval) clearInterval(slider.autoSlideInterval);
    if (dotsContainer) dotsContainer.innerHTML = '';

    const slides = slider.querySelectorAll('.slide');
    if (slides.length === 0) return;

    let currentSlide = 0;

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
        slide.classList.remove('active');
        if (index === currentSlide) {
          slide.classList.add('active');
        }
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

    // Make slides clickable
    slides.forEach((slide, index) => {
      slide.onclick = () => {
        const href = slide.getAttribute('data-href');
        if (href) {
          if (window.RouteManager && typeof window.RouteManager.navigate === 'function') {
            window.RouteManager.navigate(href.replace('/blog/', ''));
          } else {
            window.location.href = href;
          }
        }
      };
      slide.style.cursor = 'pointer';
    });

    // Event listeners
    nextBtn.onclick = nextSlide;
    prevBtn.onclick = prevSlide;

    // Auto slide
    function startAutoSlide() {
      stopAutoSlide();
      slider.autoSlideInterval = setInterval(nextSlide, 4000);
    }

    function stopAutoSlide() {
      if (slider.autoSlideInterval) {
        clearInterval(slider.autoSlideInterval);
        slider.autoSlideInterval = null;
      }
    }

    // Pause on hover
    slider.parentElement.onmouseenter = stopAutoSlide;
    slider.parentElement.onmouseleave = startAutoSlide;

    // Initialize first slide
    updateSlides();

    // Start auto slide
    startAutoSlide();
  }
  window.initTrendingSlider = initTrendingSlider;

  // Articles Slider Functionality
  function initArticlesSlider() {
    const track = document.getElementById('articlesTrack');
    const prevBtn = document.getElementById('articlesPrev');
    const nextBtn = document.getElementById('articlesNext');

    if (!track || !prevBtn || !nextBtn) return;

    // Clean up
    if (track.autoSlideInterval) clearInterval(track.autoSlideInterval);

    const cards = Array.from(track.children);
    if (cards.length === 0) return;

    let currentIndex = 0;
    const cardWidth = 340; // 320px card + 20px gap
    const visibleCards = 3;
    const totalCards = 6; // Fixed as requested

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

    nextBtn.onclick = nextSlide;
    prevBtn.onclick = prevSlide;

    // Auto slide every 4 seconds
    track.autoSlideInterval = setInterval(nextSlide, 4000);
  }
  window.initArticlesSlider = initArticlesSlider;

  // Advanced Search Modal Functionality
  function initSearchModal() {
    const searchBtn = document.getElementById('searchToggle') || document.getElementById('search-toggle');
    const searchOverlay = document.getElementById('searchOverlay');
    const searchClose = document.getElementById('searchClose');
    const searchInput = document.getElementById('searchInput');
    const searchSubmit = document.getElementById('searchBtn');

    // State management elements
    const searchSuggestions = document.getElementById('searchSuggestions');
    const typingState = document.getElementById('typingState');
    const initialFilters = document.querySelector('.search-filters');
    const searchResultsSection = document.querySelector('.search-results-section');
    const resultsCount = document.getElementById('resultsCount');
    const searchStats = document.getElementById('searchStats');
    const resultFilters = document.getElementById('resultsSort');
    const searchResults = document.getElementById('searchResults');
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    const loadMoreBtn = document.getElementById('loadMoreBtn');

    if (!searchBtn || !searchOverlay) return;

    // Search state
    let searchState = 'idle'; // 'idle' or 'active'
    let currentQuery = '';
    let currentFilters = {
      section: 'all',
      tags: [],
      sort: 'relevance'
    };
    let currentResults = [];
    let resultsOffset = 0;
    const resultsPerPage = 10;

    function openSearch() {
      searchOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      if (searchInput) {
        searchInput.focus();
        setState('idle'); // Set to idle state when opening
      }
    }

    function closeSearch() {
      searchOverlay.classList.remove('active');
      document.body.style.overflow = '';
      resetSearchState();
    }

    function setState(newState) {
      const currentState = searchState;
      if (currentState === newState) return; // No change needed

      searchState = newState;

      if (newState === 'idle') {
        // Fade out active state components
        if (searchResultsSection) {
          searchResultsSection.classList.remove('visible');
          setTimeout(() => {
            if (searchResultsSection) searchResultsSection.style.display = 'none';
          }, 300);
        }

        // Wait for fade out animation, then show idle state
        setTimeout(() => {
          if (searchSuggestions) {
            searchSuggestions.style.display = 'flex';
            searchSuggestions.classList.remove('hidden');
          }
          if (typingState) {
            typingState.style.display = 'block';
            typingState.classList.remove('hidden');
          }
          if (initialFilters) {
            initialFilters.style.display = 'block';
            initialFilters.classList.remove('hidden');
          }
        }, 350);
      } else if (newState === 'active') {
        // Fade out idle state components
        if (searchSuggestions) {
          searchSuggestions.classList.add('hidden');
          setTimeout(() => {
            if (searchSuggestions) searchSuggestions.style.display = 'none';
          }, 300);
        }
        if (typingState) {
          typingState.classList.add('hidden');
          setTimeout(() => {
            if (typingState) typingState.style.display = 'none';
          }, 300);
        }
        if (initialFilters) {
          initialFilters.classList.add('hidden');
          setTimeout(() => {
            if (initialFilters) initialFilters.style.display = 'none';
          }, 300);
        }

        // Wait for fade out animation, then show active state
        setTimeout(() => {
          if (searchResultsSection) {
            searchResultsSection.style.display = 'flex';
            searchResultsSection.classList.add('visible');
          }
        }, 350);
      }
    }

    function resetSearchState() {
      currentQuery = '';
      currentFilters = { section: 'all', tags: [], sort: 'relevance' };
      currentResults = [];
      resultsOffset = 0;
      searchState = 'idle';

      if (searchInput) searchInput.value = '';

      // Reset UI to idle state
      setState('idle');
      updateUI();
      showInitialState();
    }

    function showInitialState() {
      resultsCount.textContent = 'Start typing to search...';
      searchStats.innerHTML = '';
      loadMoreContainer.style.display = 'none';

      if (searchResults) {
        searchResults.innerHTML = `
          <div class="no-results">
            <div class="no-results-icon">
              <i class="ph-bold ph-magnifying-glass"></i>
            </div>
            <h3>Discover Amazing Content</h3>
            <p>Search through our collection of articles, tutorials, and insights</p>
          </div>
        `;
      }
    }

    // Event listeners
    searchBtn.addEventListener('click', openSearch);

    if (searchClose) searchClose.addEventListener('click', closeSearch);
    searchOverlay.addEventListener('click', (e) => {
      if (e.target === searchOverlay) closeSearch();
    });

    // Filter event listeners
    initFilterListeners();

    // Search input handling with state transitions
    let searchTimeout;
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        currentQuery = e.target.value.trim();

        // State transition logic
        if (currentQuery.length === 0) {
          setState('idle');
          showInitialState();
          return;
        } else if (currentQuery.length === 1 && searchState === 'idle') {
          setState('active');
        }

        // Debounced search
        searchTimeout = setTimeout(() => {
          if (currentQuery.length > 0) {
            performSearch();
          }
        }, 300);
      });
    }

    if (searchSubmit) {
      searchSubmit.addEventListener('click', () => {
        if (searchInput && searchInput.value.trim()) {
          currentQuery = searchInput.value.trim();
          if (searchState === 'idle') {
            setState('active');
          }
          performSearch();
        }
      });
    }

    // Load more functionality
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', () => {
        loadMoreResults();
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
      if (e.key === 'Enter' && searchOverlay.classList.contains('active') && searchInput && searchInput.value.trim()) {
        currentQuery = searchInput.value.trim();
        if (searchState === 'idle') {
          setState('active');
        }
        performSearch();
      }
    });

    function initFilterListeners() {
      // Section filters (initial state)
      document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const section = btn.dataset.section;
          currentFilters.section = section;

          // Update active state
          document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          if (currentQuery) performSearch();
        });
      });

      // Tag filters
      document.querySelectorAll('.tag-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const tag = chip.dataset.tag;
          const index = currentFilters.tags.indexOf(tag);

          if (index > -1) {
            currentFilters.tags.splice(index, 1);
            chip.classList.remove('active');
          } else {
            currentFilters.tags.push(tag);
            chip.classList.add('active');
          }

          if (currentQuery) performSearch();
        });
      });

      // Sort options (results state)
      document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const sort = btn.dataset.sort;
          currentFilters.sort = sort;

          // Update active state
          document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          if (currentResults.length > 0) {
            sortResults();
            renderResults();
          }
        });
      });
    }

    function performSearch() {
      if (!currentQuery) return;

      // Show loading state
      if (resultsCount) resultsCount.textContent = 'Searching...';
      if (searchResults) searchResults.innerHTML = '<div class="loading">Searching...</div>';

      // Simulate API call - replace with real implementation
      setTimeout(() => {
        const results = getMockResults(currentQuery, currentFilters);
        currentResults = results;
        resultsOffset = resultsPerPage;
        renderSearchResults();
      }, 500);
    }

    function loadMoreResults() {
      const nextResults = getMockResults(currentQuery, currentFilters, resultsOffset, resultsPerPage);
      currentResults = [...currentResults, ...nextResults];
      resultsOffset += resultsPerPage;
      renderResults(true); // Append mode

      if (nextResults.length < resultsPerPage) {
        loadMoreContainer.style.display = 'none';
      }
    }

    function renderSearchResults() {
      updateUI();
      renderResults();
    }

    function updateUI() {
      const totalResults = currentResults.length;

      if (resultsCount) {
        if (totalResults === 0) {
          resultsCount.textContent = '0 results found';
        } else {
          resultsCount.textContent = totalResults === 1 ? '1 result found' : `${totalResults} results found`;
        }
      }

      // Show search stats
      const searchTime = Math.random() * 0.5 + 0.1; // Simulate search time
      if (searchStats) {
        searchStats.innerHTML = `<i class="ph-bold ph-clock"></i> ${searchTime.toFixed(2)}s`;
      }

      // Show load more if there are more results
      if (loadMoreContainer) {
        loadMoreContainer.style.display = totalResults >= resultsPerPage ? 'block' : 'none';
      }
    }

    function renderResults(append = false) {
      if (!searchResults) return;

      if (!append) {
        searchResults.innerHTML = '';
      }

      if (currentResults.length === 0) {
        searchResults.innerHTML = `
          <div class="no-results">
            <div class="no-results-icon">
              <i class="ph-bold ph-magnifying-glass"></i>
            </div>
            <h3>No Results Found</h3>
            <p>Try adjusting your search terms or filters</p>
          </div>
        `;
        return;
      }

      const resultsHTML = currentResults.map((result, index) =>
        createResultCard(result, append ? index + (resultsOffset - resultsPerPage) : index)
      ).join('');

      if (append) {
        searchResults.insertAdjacentHTML('beforeend', resultsHTML);
      } else {
        searchResults.innerHTML = resultsHTML;
      }
    }

    function createResultCard(result, index, append = false) {
      const delay = append ? 0 : index * 0.1;
      return `
        <div class="result-card" style="animation-delay: ${delay}s">
          <div class="result-media">
            ${result.image ? `<img src="${result.image}" alt="${result.title}" class="result-image">` :
          `<div class="result-icon"><i class="ph-bold ${result.icon || 'ph-article'}"></i></div>`}
          </div>
          <div class="result-content">
            <div class="result-category">${result.section || result.category}</div>
            <h3 class="result-title">${highlightText(result.title, currentQuery)}</h3>
            <p class="result-excerpt">${highlightText(result.excerpt, currentQuery)}</p>
            <div class="result-meta">
              <span class="result-author">${result.author || 'NekwasaR'}</span>
              <span class="result-date">${result.date || 'Recently'}</span>
              ${result.tags ? `<div class="result-tags">${result.tags.map(tag => `<span class="result-tag">${tag}</span>`).join('')}</div>` : ''}
              <span class="result-stats">
                <i class="ph-bold ph-eye"></i> ${result.views || Math.floor(Math.random() * 1000)}
              </span>
            </div>
          </div>
        </div>
      `;
    }

    function highlightText(text, query) {
      if (!query) return text;
      const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      return text.replace(regex, '<span class="highlight">$1</span>');
    }

    function sortResults() {
      currentResults.sort((a, b) => {
        switch (currentFilters.sort) {
          case 'recent':
            return new Date(b.date || 0) - new Date(a.date || 0);
          case 'popular':
            return (b.views || 0) - (a.views || 0);
          case 'relevance':
          default:
            return 0; // Keep original order for relevance
        }
      });
    }

    function getMockResults(query, filters, offset = 0, limit = resultsPerPage) {
      // Mock data - replace with real search implementation
      const allResults = [
        {
          title: 'The Future of Artificial Intelligence: What\'s Next in 2025',
          excerpt: 'Explore the cutting-edge developments in AI that will shape our world in the coming year, from quantum computing to advanced neural networks.',
          section: 'AI',
          category: 'AI & Technology',
          author: 'NekwasaR',
          date: 'Oct 30, 2025',
          views: 2100,
          tags: ['ai', 'technology', 'future'],
          image: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=250&fit=crop&crop=center',
          icon: 'ph-cpu'
        },
        {
          title: 'Building Billion-Dollar Ideas: Lessons from Successful Startups',
          excerpt: 'Learn from the most successful entrepreneurs and their journey to building world-changing companies that started from humble beginnings.',
          section: 'Business',
          category: 'Innovation',
          author: 'NekwasaR',
          date: 'Oct 28, 2025',
          views: 1800,
          tags: ['startup', 'business', 'innovation'],
          image: 'https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=400&h=250&fit=crop&crop=center',
          icon: 'ph-lightbulb'
        },
        {
          title: 'Modern Web Technologies: What Every Developer Should Know',
          excerpt: 'Stay ahead of the curve with the latest tools and frameworks that are revolutionizing web development and user experience.',
          section: 'Tutorials',
          category: 'Web Development',
          author: 'NekwasaR',
          date: 'Oct 25, 2025',
          views: 1500,
          tags: ['web-development', 'tutorial', 'technology'],
          image: 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=400&h=250&fit=crop&crop=center',
          icon: 'ph-code'
        },
        {
          title: 'Latest AI Models: A Comprehensive Guide',
          excerpt: 'Explore the most advanced AI models available today and understand their capabilities, use cases, and implementation strategies.',
          section: 'AI',
          category: 'AI',
          author: 'NekwasaR',
          date: 'Oct 20, 2025',
          views: 1200,
          tags: ['ai', 'models', 'guide'],
          image: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=250&fit=crop&crop=center',
          icon: 'ph-cpu'
        },
        {
          title: 'Emerging Technologies Shaping 2025',
          excerpt: 'Discover the breakthrough technologies that are set to transform industries and create new opportunities in the coming year.',
          section: 'Trending',
          category: 'Tech Trends',
          author: 'NekwasaR',
          date: 'Oct 18, 2025',
          views: 950,
          tags: ['technology', 'trends', 'future'],
          image: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=250&fit=crop&crop=center',
          icon: 'ph-trend-up'
        }
      ];

      // Filter results
      let filteredResults = allResults.filter(result => {
        // Text search
        const searchText = `${result.title} ${result.excerpt} ${result.tags.join(' ')}`.toLowerCase();
        const matchesQuery = searchText.includes(query.toLowerCase());

        // Section filter
        const matchesSection = filters.section === 'all' || result.section.toLowerCase() === filters.section;

        // Tag filter
        const matchesTags = filters.tags.length === 0 || filters.tags.some(tag => result.tags.includes(tag));

        return matchesQuery && matchesSection && matchesTags;
      });

      // Apply sorting
      filteredResults.sort((a, b) => {
        switch (filters.sort) {
          case 'recent':
            return new Date(b.date) - new Date(a.date);
          case 'popular':
            return b.views - a.views;
          case 'relevance':
          default:
            return 0;
        }
      });

      // Apply pagination
      return filteredResults.slice(offset, offset + limit);
    }

    // Initialize suggestions
    initSuggestions();

    function initSuggestions() {
      const suggestions = document.querySelectorAll('.suggestion-item');
      suggestions.forEach(suggestion => {
        suggestion.addEventListener('click', () => {
          const type = suggestion.dataset.type;
          let searchTerm = '';

          switch (type) {
            case 'trending':
              searchTerm = 'AI ethics';
              break;
            case 'recent':
              searchTerm = 'web development';
              break;
            case 'popular':
              searchTerm = 'blockchain guide';
              break;
          }

          if (searchInput) {
            searchInput.value = searchTerm;
            currentQuery = searchTerm;
            performSearch();
          }
        });
      });
    }
  }

  // Mobile Menu Modal Functionality
  function initMenuModal() {
    const menuBtn = document.getElementById('mobileMenuToggle') || document.getElementById('mobile-menu-toggle');
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
    if (!form) return;

    const message = document.getElementById('newsletterMessage');
    const submitBtn = document.getElementById('subscribeBtn');
    const btnText = submitBtn ? submitBtn.querySelector('.btn-text') : null;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const nameEl = document.getElementById('subscriberName') || { value: (document.getElementById('newsletterEmail')?.value || '').split('@')[0] };
      const emailEl = document.getElementById('subscriberEmail') || document.getElementById('newsletterEmail');

      const name = nameEl?.value || '';
      const email = emailEl?.value || '';

      // Basic validation
      if (!email.trim()) {
        showMessage('Please enter an email address.', 'error');
        return;
      }

      if (!isValidEmail(email)) {
        showMessage('Please enter a valid email address.', 'error');
        return;
      }

      // Show loading state
      submitBtn.disabled = true;
      if (btnText) btnText.textContent = 'Subscribing...';

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
        if (btnText) btnText.textContent = 'Subscribe';
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
    document.querySelectorAll('.card-link, .post-link, .slide-link, .banner-link, .tag-item, .trending-link').forEach(card => {
      card.onclick = function (e) {
        const href = this.getAttribute('data-href') || this.getAttribute('href');
        if (href) {
          e.preventDefault();

          // If it's a blog post, try to open in modal or navigate via SPA
          if (href.startsWith('/blog/')) {
            const slug = href.replace('/blog/', '');
            if (window.openPostModal && typeof window.openPostModal === 'function') {
              window.openPostModal(slug);
            } else {
              window.location.href = href;
            }
          } else if (window.RouteManager && typeof window.RouteManager.navigate === 'function') {
            // Handle regular SPA routes
            const route = href.startsWith('/') ? href.substring(1) : href;
            window.RouteManager.navigate(route || 'home');
          } else {
            window.location.href = href;
          }
        }
      };
    });
  }
  window.initCardLinks = initCardLinks;

  // Post Modal Functionality
  function initPostModal() {
    const modal = document.getElementById('postModal');
    const closeBtn = document.getElementById('postModalClose');
    const overlay = document.getElementById('postModal');

    if (!modal) return;

    // Close button functionality
    if (closeBtn) {
      closeBtn.addEventListener('click', closePostModal);
    }

    // Overlay click to close
    if (overlay) {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          closePostModal();
        }
      });
    }

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('active')) {
        closePostModal();
      }
    });

    // Initialize like functionality
    initPostLike();
  }

  function openPostModal(postUrl) {
    const modal = document.getElementById('postModal');
    const content = document.getElementById('postModalContent');
    const title = document.querySelector('.post-modal-title-text');
    const category = document.querySelector('.post-modal-category');

    if (!modal || !content) return;

    // Show loading state
    content.innerHTML = `
      <div class="post-modal-loading">
        <div class="loading-spinner"></div>
        <p>Loading post content...</p>
      </div>
    `;

    // Set default title
    if (title) title.textContent = 'Loading...';
    if (category) category.textContent = 'Article';

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Fetch post content (mock for now - replace with real API call)
    loadPostContent(postUrl);
  }

  function closePostModal() {
    const modal = document.getElementById('postModal');
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  // Like functionality for post modal
  function initPostLike() {
    const likeBtn = document.getElementById('postModalLike');
    if (!likeBtn) return;

    let isLiked = false;
    let currentLikes = 0;
    let currentPostId = null;

    // Function to reset like state for new post
    window.resetPostLike = function (postId, likeCount = 0) {
      currentPostId = postId;
      currentLikes = likeCount;
      isLiked = false; // Reset to not liked for new post

      const countSpan = likeBtn.querySelector('.action-count');
      const icon = likeBtn.querySelector('i');

      if (countSpan) {
        countSpan.textContent = currentLikes;
      }
      if (icon) {
        icon.className = 'ph-bold ph-heart';
      }
    };

    likeBtn.addEventListener('click', async () => {
      const countSpan = likeBtn.querySelector('.action-count');
      const icon = likeBtn.querySelector('i');

      try {
        // Toggle like state
        isLiked = !isLiked;

        // Update UI immediately
        if (isLiked) {
          icon.className = 'ph-fill ph-heart text-red-500';
          currentLikes++;
        } else {
          icon.className = 'ph-bold ph-heart';
          currentLikes--;
        }

        if (countSpan) {
          countSpan.textContent = currentLikes;
        }

        // Send like/unlike request to backend API
        const userIdentifier = 'user_' + Date.now(); // Simple identifier for demo

        if (isLiked) {
          // Like the post
          const response = await fetch(`/api/blogs/${currentPostId}/likes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_identifier: userIdentifier })
          });

          if (!response.ok) {
            throw new Error(`Like failed: ${response.status}`);
          }
        } else {
          // Unlike the post
          const response = await fetch(`/api/blogs/${currentPostId}/likes?user_identifier=${userIdentifier}`, {
            method: 'DELETE'
          });

          if (!response.ok) {
            throw new Error(`Unlike failed: ${response.status}`);
          }
        }

      } catch (error) {
        console.error('Like error:', error);
        // Revert UI on error
        isLiked = !isLiked;
        if (isLiked) {
          icon.className = 'ph-fill ph-heart text-red-500';
          currentLikes++;
        } else {
          icon.className = 'ph-bold ph-heart';
          currentLikes--;
        }
        if (countSpan) {
          countSpan.textContent = currentLikes;
        }
      }
    });
  }

  async function loadPostContent(postUrl) {
    try {
      // Extract post slug from URL
      const slug = postUrl.split('/').pop();
      const apiUrl = `/api/blogs/${slug}`;

      const response = await fetch(apiUrl);
      const postData = await response.json();

      renderPostInModal(postData);
    } catch (error) {
      console.error('Error loading post:', error);
      // Fallback to mock content
      renderMockPostInModal(postUrl);
    }
  }

  function renderPostInModal(postData) {
    const content = document.getElementById('postModalContent');
    const title = document.querySelector('.post-modal-title-text');
    const category = document.querySelector('.post-modal-category');

    if (!content) return;

    // Update title and category
    if (title) title.textContent = postData.title || 'Post Title';
    if (category) category.textContent = postData.category || 'Article';

    // Reset like state for new post
    if (window.resetPostLike) {
      window.resetPostLike(postData.id || postData.slug, postData.like_count || 0);
    }

    // Render content
    content.innerHTML = `
      <div class="post-meta">
        <span class="author">${postData.author || 'NekwasaR'}</span>
        <span class="date">${postData.published_at ? new Date(postData.published_at).toLocaleDateString() : 'Recent'}</span>
        <span class="views">${postData.view_count || 0} views</span>
      </div>
      <div class="post-content">
        ${postData.content || '<p>Post content would appear here...</p>'}
      </div>
    `;
  }

  function renderMockPostInModal(postUrl) {
    const content = document.getElementById('postModalContent');
    const title = document.querySelector('.post-modal-title-text');
    const category = document.querySelector('.post-modal-category');

    if (!content) return;

    // Mock data based on URL
    const mockPosts = {
      'ai-revolutionizing-healthcare': {
        title: 'How AI is Revolutionizing Healthcare',
        category: 'Technology',
        author: 'NekwasaR',
        like_count: 42,
        content: `
          <h2>The Future of Medical Diagnosis</h2>
          <p>Artificial Intelligence is transforming healthcare in unprecedented ways. From early disease detection to personalized treatment plans, AI systems are becoming indispensable tools for medical professionals.</p>

          <h3>Key Applications</h3>
          <ul>
            <li>Medical imaging analysis</li>
            <li>Drug discovery acceleration</li>
            <li>Patient risk prediction</li>
            <li>Telemedicine enhancement</li>
          </ul>

          <blockquote>
            "AI doesn't replace doctors—it empowers them to make better decisions faster."
          </blockquote>

          <p>The integration of AI in healthcare represents one of the most promising developments of our time, with the potential to save millions of lives and improve healthcare outcomes worldwide.</p>
        `
      },
      'rise-of-quantum-computing': {
        title: 'The Rise of Quantum Computing',
        category: 'Technology',
        author: 'NekwasaR',
        like_count: 28,
        content: `
          <h2>Understanding Quantum Advantage</h2>
          <p>Quantum computing represents a paradigm shift in computational power. Unlike classical computers that use bits, quantum computers use quantum bits or qubits that can exist in multiple states simultaneously.</p>

          <h3>Current Developments</h3>
          <p>Major tech companies and research institutions are racing to build practical quantum computers. Recent breakthroughs in error correction and qubit stability have brought us closer to quantum advantage.</p>

          <h3>Real-World Applications</h3>
          <ul>
            <li>Cryptographic systems</li>
            <li>Drug discovery</li>
            <li>Financial modeling</li>
            <li>Climate simulation</li>
          </ul>
        `
      }
    };

    const slug = postUrl.split('/').pop();
    const postData = mockPosts[slug] || {
      title: 'Post Title',
      category: 'Article',
      author: 'NekwasaR',
      like_count: 0,
      content: '<p>This is a preview of the post content. Click "Read Full Article" to view the complete post.</p>'
    };

    if (title) title.textContent = postData.title;
    if (category) category.textContent = postData.category;

    // Reset like state for new post
    if (window.resetPostLike) {
      window.resetPostLike(slug, postData.like_count);
    }

    content.innerHTML = `
      <div class="post-meta">
        <span class="author">${postData.author}</span>
        <span class="date">Recent</span>
        <span class="views">1.2k views</span>
      </div>
      <div class="post-content">
        ${postData.content}
      </div>
    `;
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
    return function () {
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

  // Expose re-init for SPA route swaps
  window.BlogPageInit = initBlog;

  // Share functions for inline social buttons
  window.shareOnFacebook = function () {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(document.title);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}&title=${title}`, '_blank', 'width=600,height=400');
  };

  window.shareOnTelegram = function () {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(document.title);
    window.open(`https://t.me/share/url?url=${url}&text=${text}`, '_blank');
  };

  window.shareOnReddit = function () {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(document.title);
    window.open(`https://www.reddit.com/submit?url=${url}&title=${title}`, '_blank');
  };

  window.shareOnWhatsApp = function () {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(document.title);
    window.open(`https://wa.me/?text=${text}%20${url}`, '_blank');
  };

})();
