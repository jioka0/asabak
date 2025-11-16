/*! Blog Templates JavaScript - Professional Interactions
 * Matching NekwasaR Portfolio Brand
 * ------------------------------------------------ */

/**
 * Blog Templates JavaScript - Core functionality for all blog templates
 * Provides smooth interactions, social sharing, video controls, and more
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        smoothScrollDuration: 800,
        animationDuration: 600,
        socialShare: {
            twitter: 'https://twitter.com/intent/tweet?text=',
            linkedin: 'https://www.linkedin.com/sharing/share-offsite/?url=',
            facebook: 'https://www.facebook.com/sharer/sharer.php?u=',
            reddit: 'https://www.reddit.com/submit?url='
        },
        debug: false
    };

    // Utility Functions
    const Utils = {
        /**
         * Debounce function to limit function calls
         */
        debounce: function(func, wait, immediate) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    if (!immediate) func(...args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func(...args);
            };
        },

        /**
         * Check if element is in viewport
         */
        isInViewport: function(element) {
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        },

        /**
         * Get current page URL
         */
        getCurrentURL: function() {
            return window.location.href;
        },

        /**
         * Get page title
         */
        getPageTitle: function() {
            return document.title;
        },

        /**
         * Log debug messages
         */
        debug: function(message, data) {
            if (CONFIG.debug) {
                console.log('[Blog Templates]', message, data || '');
            }
        }
    };

    // Social Share Module
    const SocialShare = {
        init: function() {
            this.bindEvents();
            Utils.debug('Social Share initialized');
        },

        bindEvents: function() {
            // Share button clicks
            document.addEventListener('click', (e) => {
                const target = e.target.closest('.social-share-btn, [data-share]');
                if (target) {
                    e.preventDefault();
                    const platform = target.dataset.share || target.title.toLowerCase().includes('twitter') ? 'twitter' :
                                   target.title.toLowerCase().includes('linkedin') ? 'linkedin' :
                                   target.title.toLowerCase().includes('facebook') ? 'facebook' :
                                   target.title.toLowerCase().includes('reddit') ? 'reddit' :
                                   target.title.toLowerCase().includes('copy') ? 'copy' : null;
                    
                    if (platform) {
                        this.share(platform);
                    }
                }
            });
        },

        share: function(platform) {
            const url = encodeURIComponent(Utils.getCurrentURL());
            const title = encodeURIComponent(Utils.getPageTitle());
            const text = encodeURIComponent(document.querySelector('meta[name="description"]')?.content || title);

            let shareUrl = '';
            
            switch (platform) {
                case 'twitter':
                    shareUrl = `${CONFIG.socialShare.twitter}${text}&url=${url}`;
                    break;
                case 'linkedin':
                    shareUrl = `${CONFIG.socialShare.linkedin}${url}`;
                    break;
                case 'facebook':
                    shareUrl = `${CONFIG.socialShare.facebook}${url}`;
                    break;
                case 'reddit':
                    shareUrl = `${CONFIG.socialShare.reddit}${url}&title=${title}`;
                    break;
                case 'copy':
                    this.copyToClipboard();
                    return;
                default:
                    Utils.debug('Unknown share platform:', platform);
                    return;
            }

            // Open share window
            window.open(shareUrl, '_blank', 'width=600,height=400,scrollbars=yes,resizable=yes');
            
            Utils.debug('Shared to:', platform);
        },

        copyToClipboard: function() {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(Utils.getCurrentURL()).then(() => {
                    this.showCopyFeedback();
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = Utils.getCurrentURL();
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showCopyFeedback();
            }
        },

        showCopyFeedback: function() {
            const feedback = document.createElement('div');
            feedback.textContent = 'Link copied to clipboard!';
            feedback.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--accent);
                color: var(--t-opp-bright);
                padding: 1rem 2rem;
                border-radius: var(--_radius-m);
                z-index: 10000;
                font-family: var(--_font-default);
                font-size: 1.4rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                transform: translateX(100%);
                transition: transform 0.3s var(--_animbezier);
            `;
            
            document.body.appendChild(feedback);
            
            // Animate in
            setTimeout(() => {
                feedback.style.transform = 'translateX(0)';
            }, 10);
            
            // Animate out and remove
            setTimeout(() => {
                feedback.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    document.body.removeChild(feedback);
                }, 300);
            }, 2000);
        }
    };

    // Smooth Scrolling Module
    const SmoothScroll = {
        init: function() {
            this.bindEvents();
            Utils.debug('Smooth Scroll initialized');
        },

        bindEvents: function() {
            document.addEventListener('click', (e) => {
                const target = e.target.closest('a[href^="#"]');
                if (target && target.getAttribute('href') !== '#') {
                    e.preventDefault();
                    this.scrollToTarget(target.getAttribute('href'));
                }
            });
        },

        scrollToTarget: function(targetId) {
            const target = document.querySelector(targetId);
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed headers
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Update URL without jumping
                if (history.pushState) {
                    history.pushState(null, null, targetId);
                }
                
                Utils.debug('Scrolled to:', targetId);
            }
        }
    };

    // Reading Progress Module
    const ReadingProgress = {
        progressBar: null,

        init: function() {
            this.createProgressBar();
            this.bindEvents();
            Utils.debug('Reading Progress initialized');
        },

        createProgressBar: function() {
            this.progressBar = document.createElement('div');
            this.progressBar.id = 'reading-progress';
            this.progressBar.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 0%;
                height: 3px;
                background: linear-gradient(90deg, var(--accent), var(--secondary));
                z-index: 9999;
                transition: width 0.1s ease-out;
            `;
            document.body.appendChild(this.progressBar);
        },

        bindEvents: function() {
            window.addEventListener('scroll', Utils.debounce(() => {
                this.updateProgress();
            }, 100));
        },

        updateProgress: function() {
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight - windowHeight;
            const scrolled = window.scrollY;
            const progress = (scrolled / documentHeight) * 100;
            
            this.progressBar.style.width = Math.min(progress, 100) + '%';
        }
    };

    // Table of Contents Module
    const TableOfContents = {
        tocLinks: [],
        sections: [],

        init: function() {
            this.setupToc();
            this.bindEvents();
            Utils.debug('Table of Contents initialized');
        },

        setupToc: function() {
            this.tocLinks = Array.from(document.querySelectorAll('.toc-link'));
            this.sections = this.tocLinks.map(link => {
                return document.querySelector(link.getAttribute('href'));
            }).filter(section => section !== null);
        },

        bindEvents: function() {
            window.addEventListener('scroll', Utils.debounce(() => {
                this.highlightActiveSection();
            }, 100));

            // Initial highlight
            this.highlightActiveSection();
        },

        highlightActiveSection: function() {
            const scrollPos = window.scrollY + 100; // Offset for better UX
            
            let activeIndex = -1;
            for (let i = this.sections.length - 1; i >= 0; i--) {
                if (this.sections[i].offsetTop <= scrollPos) {
                    activeIndex = i;
                    break;
                }
            }

            // Update active states
            this.tocLinks.forEach((link, index) => {
                if (index === activeIndex) {
                    link.classList.add('active');
                    link.style.color = 'var(--t-accent)';
                } else {
                    link.classList.remove('active');
                    link.style.color = 'var(--t-medium)';
                }
            });
        }
    };

    // Animation Module
    const Animations = {
        observer: null,

        init: function() {
            this.setupIntersectionObserver();
            this.observeElements();
            Utils.debug('Animations initialized');
        },

        setupIntersectionObserver: function() {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });
        },

        observeElements: function() {
            const elementsToAnimate = document.querySelectorAll(
                '.blog-card, .listing-item, .content-section, blockquote'
            );
            
            elementsToAnimate.forEach(element => {
                this.observer.observe(element);
            });
        }
    };

    // Newsletter Module
    const Newsletter = {
        init: function() {
            this.bindEvents();
            Utils.debug('Newsletter initialized');
        },

        bindEvents: function() {
            const form = document.getElementById('newsletterForm');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleSubmission(form);
                });
            }
        },

        handleSubmission: function(form) {
            const formData = new FormData(form);
            const data = {
                name: formData.get('name') || document.getElementById('subscriberName')?.value,
                email: formData.get('email') || document.getElementById('subscriberEmail')?.value
            };

            // Show loading state
            const submitBtn = form.querySelector('.subscribe-btn');
            const originalText = submitBtn.textContent;
            submitBtn.innerHTML = '<i class="ph-bold ph-circle-notch" style="animation: spin 1s linear infinite;"></i> Subscribing...';
            submitBtn.disabled = true;

            // Simulate API call (replace with actual implementation)
            setTimeout(() => {
                this.showSuccessMessage(data.email);
                form.reset();
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                Utils.debug('Newsletter subscription:', data);
            }, 2000);
        },

        showSuccessMessage: function(email) {
            const message = document.getElementById('newsletterMessage') || 
                          document.createElement('div');
            message.id = 'newsletterMessage';
            message.innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <i class="ph-bold ph-check-circle" style="color: #22c55e; font-size: 4rem; margin-bottom: 1rem;"></i>
                    <h3 style="color: var(--t-bright); margin-bottom: 1rem;">Successfully Subscribed!</h3>
                    <p style="color: var(--t-medium);">Thank you for subscribing! We'll send the latest insights to ${email}.</p>
                </div>
            `;
            message.style.cssText = `
                background: var(--base);
                border: 1px solid var(--stroke-elements);
                border-radius: var(--_radius-xl);
                margin-top: 2rem;
                opacity: 0;
                transform: translateY(20px);
                transition: all 0.3s var(--_animbezier);
            `;
            
            if (!message.parentNode) {
                document.getElementById('newsletterForm')?.parentNode.appendChild(message);
            }
            
            // Animate in
            setTimeout(() => {
                message.style.opacity = '1';
                message.style.transform = 'translateY(0)';
            }, 10);
            
            // Remove after delay
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.parentNode.removeChild(message);
                    }
                }, 300);
            }, 5000);
        }
    };

    // Dark/Light Theme Toggle
    const ThemeToggle = {
        init: function() {
            this.bindEvents();
            Utils.debug('Theme Toggle initialized');
        },

        bindEvents: function() {
            // Bind to existing theme buttons in header
            const themeButtons = document.querySelectorAll('[onclick*="toggleTheme"]');
            themeButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleTheme();
                });
            });
        },

        toggleTheme: function() {
            const html = document.documentElement;
            const currentScheme = html.getAttribute('color-scheme') || 'light';
            const newScheme = currentScheme === 'light' ? 'dark' : 'light';

            html.setAttribute('color-scheme', newScheme);

            // Update all theme button icons
            const themeButtons = document.querySelectorAll('[onclick*="toggleTheme"] i');
            themeButtons.forEach(icon => {
                icon.className = newScheme === 'light' ?
                    'ph-bold ph-moon-stars text-lg' :
                    'ph-bold ph-sun text-lg';
            });

            // Save preference
            localStorage.setItem('color-scheme', newScheme);

            Utils.debug('Theme changed to:', newScheme);
        }
    };

    // Search Modal Module
    const SearchModal = {
        init: function() {
            this.bindEvents();
            Utils.debug('Search Modal initialized');
        },

        bindEvents: function() {
            // Bind to existing search buttons in header
            const searchButtons = document.querySelectorAll('[onclick*="openSearchModal"]');
            searchButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.openModal();
                });
            });

            // Close modal when clicking outside or on close button
            document.addEventListener('click', (e) => {
                const modal = document.getElementById('search-modal');
                const closeBtn = e.target.closest('.search-modal-close');
                if (modal && (e.target === modal || closeBtn)) {
                    this.closeModal();
                }
            });

            // Close on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.closeModal();
                }
            });
        },

        openModal: function() {
            const modal = document.getElementById('search-modal');
            if (modal) {
                modal.classList.add('active');
                const input = modal.querySelector('.search-modal-input');
                if (input) {
                    setTimeout(() => input.focus(), 100);
                }
            }
        },

        closeModal: function() {
            const modal = document.getElementById('search-modal');
            if (modal) {
                modal.classList.remove('active');
            }
        }
    };

    // Video Controls Module
    const VideoControls = {
        init: function() {
            this.bindEvents();
            Utils.debug('Video Controls initialized');
        },

        bindEvents: function() {
            document.addEventListener('click', (e) => {
                const playPauseBtn = e.target.closest('#playPauseBtn');
                const muteBtn = e.target.closest('#muteBtn');
                const fullscreenBtn = e.target.closest('#fullscreenBtn');
                
                const video = document.getElementById('heroVideo');
                if (!video) return;
                
                if (playPauseBtn) {
                    this.togglePlayPause(video, playPauseBtn);
                } else if (muteBtn) {
                    this.toggleMute(video, muteBtn);
                } else if (fullscreenBtn) {
                    this.toggleFullscreen(video, fullscreenBtn);
                }
            });
        },

        togglePlayPause: function(video, button) {
            if (video.paused) {
                video.play();
                button.innerHTML = '<i class="ph-bold ph-pause"></i>';
            } else {
                video.pause();
                button.innerHTML = '<i class="ph-bold ph-play"></i>';
            }
        },

        toggleMute: function(video, button) {
            if (video.muted) {
                video.muted = false;
                button.innerHTML = '<i class="ph-bold ph-speaker-simple-high"></i>';
            } else {
                video.muted = true;
                button.innerHTML = '<i class="ph-bold ph-speaker-simple-x"></i>';
            }
        },

        toggleFullscreen: function(video, button) {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                video.requestFullscreen().catch(err => {
                    Utils.debug('Fullscreen failed:', err);
                });
            }
        }
    };

    // Print Module
    const Print = {
        init: function() {
            this.bindEvents();
            Utils.debug('Print functionality initialized');
        },

        bindEvents: function() {
            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                    this.prepareForPrint();
                }
            });
        },

        prepareForPrint: function() {
            // Add print-specific styles
            const printStyles = document.createElement('style');
            printStyles.id = 'print-styles';
            printStyles.textContent = `
                @media print {
                    .social-share,
                    .video-controls,
                    .banner-cta,
                    #theme-toggle,
                    #reading-progress {
                        display: none !important;
                    }
                    
                    .blog-post {
                        background: white !important;
                        color: black !important;
                    }
                    
                    .blog-post h1,
                    .blog-post h2,
                    .blog-post h3,
                    .blog-post h4 {
                        color: black !important;
                        -webkit-text-fill-color: black !important;
                    }
                    
                    a {
                        color: black !important;
                        text-decoration: underline !important;
                    }
                    
                    .banner-image-overlay,
                    .banner-video-overlay {
                        display: none !important;
                    }
                    
                    .banner-content {
                        color: black !important;
                    }
                    
                    blockquote {
                        background: #f5f5f5 !important;
                        border-left: 4px solid #000 !important;
                        color: #000 !important;
                    }
                }
            `;
            
            document.head.appendChild(printStyles);
            
            // Remove after print
            setTimeout(() => {
                const styles = document.getElementById('print-styles');
                if (styles) {
                    styles.remove();
                }
            }, 1000);
        }
    };

    // Mobile Menu Module
    const MobileMenu = {
        init: function() {
            this.createMobileMenu();
            this.bindEvents();
            Utils.debug('Mobile Menu initialized');
        },

        createMobileMenu: function() {
            const menuToggle = document.createElement('button');
            menuToggle.id = 'mobile-menu-toggle';
            menuToggle.innerHTML = '<i class="ph-bold ph-list"></i>';
            menuToggle.style.cssText = `
                position: fixed;
                top: 20px;
                left: 20px;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: var(--base);
                border: 1px solid var(--stroke-elements);
                color: var(--t-medium);
                cursor: pointer;
                z-index: 9999;
                transition: all 0.3s var(--_animbezier);
                display: none;
                align-items: center;
                justify-content: center;
                font-size: 1.8rem;
            `;
            
            // Show on mobile
            if (window.innerWidth <= 768) {
                menuToggle.style.display = 'flex';
            }
            
            document.body.appendChild(menuToggle);
        },

        bindEvents: function() {
            const menuToggle = document.getElementById('mobile-menu-toggle');
            if (menuToggle) {
                menuToggle.addEventListener('click', () => {
                    this.toggleMenu();
                });
            }
            
            // Handle window resize
            window.addEventListener('resize', Utils.debounce(() => {
                const menuToggle = document.getElementById('mobile-menu-toggle');
                if (menuToggle) {
                    menuToggle.style.display = window.innerWidth <= 768 ? 'flex' : 'none';
                }
            }, 250));
        },

        toggleMenu: function() {
            // Create simple mobile menu
            const menu = document.createElement('div');
            menu.id = 'mobile-menu';
            menu.style.cssText = `
                position: fixed;
                top: 0;
                left: -100%;
                width: 80%;
                height: 100vh;
                background: var(--base);
                z-index: 9998;
                padding: 6rem 2rem 2rem;
                transition: left 0.3s var(--_animbezier);
                box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
            `;
            
            menu.innerHTML = `
                <nav style="display: flex; flex-direction: column; gap: 2rem;">
                    <a href="#content" style="color: var(--t-bright); text-decoration: none; font-size: 1.6rem; padding: 1rem 0; border-bottom: 1px solid var(--stroke-elements);">Content</a>
                    <a href="#introduction" style="color: var(--t-bright); text-decoration: none; font-size: 1.6rem; padding: 1rem 0; border-bottom: 1px solid var(--stroke-elements);">Introduction</a>
                    <a href="#conclusion" style="color: var(--t-bright); text-decoration: none; font-size: 1.6rem; padding: 1rem 0;">Conclusion</a>
                </nav>
            `;
            
            document.body.appendChild(menu);
            
            // Animate in
            setTimeout(() => {
                menu.style.left = '0';
            }, 10);
            
            // Close on outside click
            const closeMenu = (e) => {
                if (!menu.contains(e.target) && e.target !== menuToggle) {
                    this.closeMenu(menu, menuToggle);
                    document.removeEventListener('click', closeMenu);
                }
            };
            
            setTimeout(() => {
                document.addEventListener('click', closeMenu);
            }, 100);
            
            // Update toggle icon
            menuToggle.innerHTML = '<i class="ph-bold ph-x"></i>';
            menuToggle.onclick = () => this.closeMenu(menu, menuToggle);
        },

        closeMenu: function(menu, toggle) {
            menu.style.left = '-100%';
            toggle.innerHTML = '<i class="ph-bold ph-list"></i>';
            toggle.onclick = () => this.toggleMenu();
            
            setTimeout(() => {
                if (menu.parentNode) {
                    menu.parentNode.removeChild(menu);
                }
            }, 300);
        }
    };

    // Main initialization
    const BlogTemplates = {
        init: function() {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initializeModules());
            } else {
                this.initializeModules();
            }
        },

        initializeModules: function() {
            // Load saved theme preference
            const savedTheme = localStorage.getItem('color-scheme');
            if (savedTheme) {
                document.documentElement.setAttribute('color-scheme', savedTheme);
            }
            
            // Initialize all modules
            try {
                SmoothScroll.init();
                SocialShare.init();
                ReadingProgress.init();
                
                // Only initialize if elements exist
                if (document.querySelector('.toc')) {
                    TableOfContents.init();
                }
                
                if (document.querySelector('.blog-card, .listing-item, blockquote')) {
                    Animations.init();
                }
                
                if (document.getElementById('newsletterForm')) {
                    Newsletter.init();
                }
                
                if (document.getElementById('heroVideo')) {
                    VideoControls.init();
                }

                ThemeToggle.init();
                SearchModal.init();
                Print.init();
                MobileMenu.init();
                
                Utils.debug('All modules initialized successfully');
            } catch (error) {
                console.error('Error initializing modules:', error);
            }
        }
    };

    const RouteManager = {
        routes: ['latest','popular','others','featured','topics'],
        fallback: 'latest',
        init: function() {
            this.cache = {};
            this.container = document.getElementById('route-container');
            this.templates = document.getElementById('route-templates');
            this.bindNavLinks();
            window.addEventListener('popstate', () => this.renderRoute(this.getCurrentRoute()));
            this.renderRoute(this.getCurrentRoute());
        },
        bindNavLinks() {
            document.querySelectorAll('a[data-route]').forEach(link => {
                link.addEventListener('click', (event) => {
                    event.preventDefault();
                    const route = link.dataset.route;
                    this.navigate(route);
                });
            });
        },
        getCurrentRoute() {
            const path = window.location.pathname.replace(/^\/+|\/+$/g, '');
            return path || this.fallback;
        },
        navigate(route) {
            if (!this.routes.includes(route)) {
                route = this.fallback;
            }
            history.pushState({}, '', `/${route}`);
            this.renderRoute(route);
        },
        renderRoute(route) {
            const templateId = `route-${route}`;
            if (!this.templates) return;
            const fragment = this.templates.querySelector(`#${templateId}`);
            if (!fragment) return;
            this.container.innerHTML = '<div class="min-h-[80vh]"></div>';
            requestAnimationFrame(() => {
                this.container.innerHTML = fragment.innerHTML;
                document.title = fragment.dataset.title || fragment.querySelector('h1')?.textContent || 'NekwasaR Blog';
                const description = fragment.dataset.description || '';
                const meta = document.querySelector('meta[name="description"]');
                if (meta) meta.setAttribute('content', description);
                this.scrollToTop();
            });
        },
        scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    // Start the application
    BlogTemplates.init();

    // Export for global access if needed
    window.BlogTemplates = BlogTemplates;
    window.BlogTemplatesUtils = Utils;

})();