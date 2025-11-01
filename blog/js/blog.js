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
    forceTextWrapping();
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
      slide.addEventListener('click', () => {
        const href = slide.getAttribute('data-href');
        if (href) {
          window.location.href = href;
        }
      });
      slide.style.cursor = 'pointer';
    });

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

  // Advanced Search Modal Functionality
  function initSearchModal() {
    const searchBtn = document.getElementById('searchToggle');
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
        }
        
        // Wait for fade out animation, then show idle state
        setTimeout(() => {
          if (searchSuggestions) searchSuggestions.classList.remove('hidden');
          if (typingState) typingState.classList.remove('hidden');
          if (initialFilters) initialFilters.classList.remove('hidden');
        }, 300);
      } else if (newState === 'active') {
        // Fade out idle state components
        if (searchSuggestions) searchSuggestions.classList.add('hidden');
        if (typingState) typingState.classList.add('hidden');
        if (initialFilters) initialFilters.classList.add('hidden');
        
        // Wait for fade out animation, then show active state
        setTimeout(() => {
          if (searchResultsSection) searchResultsSection.classList.add('visible');
        }, 300);
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