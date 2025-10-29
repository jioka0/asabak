// Contact Form Integration with Backend API
class ContactFormHandler {
    constructor(formSelector = '#contact-form') {
        this.form = document.querySelector(formSelector);
        this.submitBtn = this.form?.querySelector('button[type="submit"]');
        this.replyMessage = document.querySelector('.form__reply');
        this.replyIcon = document.querySelector('.reply__icon');
        this.replyTitle = document.querySelector('.reply__title');
        this.replyText = document.querySelector('.reply__text');

        if (this.form) {
            this.init();
        }
    }

    init() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(e) {
        e.preventDefault();

        // Get form data
        const formData = new FormData(this.form);
        const data = {
            name: formData.get('Name')?.trim(),
            email: formData.get('E-mail')?.trim(),
            message: formData.get('Message')?.trim()
        };

        // Basic client-side validation
        if (!this.validateForm(data)) {
            return;
        }

        // Disable submit button and show loading
        this.setLoadingState(true);

        try {
            const response = await fetch('http://127.0.0.1:8001/api/contacts/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess('Message sent successfully! I\'ll get back to you soon.');
                this.form.reset();
            } else {
                const error = await response.json();
                this.showError(this.parseError(error));
            }
        } catch (error) {
            console.error('Contact form error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            this.setLoadingState(false);
        }
    }

    validateForm(data) {
        // Clear previous errors
        this.clearErrors();

        let isValid = true;
        const errors = [];

        // Name validation
        if (!data.name || data.name.length < 2) {
            errors.push('Name must be at least 2 characters long');
            isValid = false;
        }

        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!data.email || !emailRegex.test(data.email)) {
            errors.push('Please enter a valid email address');
            isValid = false;
        }

        // Message validation
        if (!data.message || data.message.length < 10) {
            errors.push('Message must be at least 10 characters long');
            isValid = false;
        }

        if (!isValid) {
            this.showError(errors.join('<br>'));
        }

        return isValid;
    }

    parseError(error) {
        if (error.detail) {
            if (Array.isArray(error.detail)) {
                return error.detail.map(err => {
                    if (err.loc && err.msg) {
                        const field = err.loc[err.loc.length - 1];
                        return `${field}: ${err.msg}`;
                    }
                    return err.msg || 'Validation error';
                }).join('<br>');
            }
            return error.detail;
        }
        return error.message || 'An error occurred. Please try again.';
    }

    setLoadingState(loading) {
        if (this.submitBtn) {
            this.submitBtn.disabled = loading;
            const btnCaption = this.submitBtn.querySelector('.btn-caption');
            if (btnCaption) {
                btnCaption.textContent = loading ? 'Sending...' : 'Send Message';
            }
        }
    }

    showSuccess(message) {
        this.showReply('success', 'Done!', message);
    }

    showError(message) {
        this.showReply('error', 'Error', message);
    }

    showReply(type, title, message) {
        if (this.replyMessage) {
            // Reset classes
            this.replyMessage.className = 'form__reply centered text-center';

            if (type === 'success') {
                this.replyMessage.classList.add('success');
                if (this.replyIcon) {
                    this.replyIcon.className = 'ph-bold ph-smiley reply__icon';
                }
            } else {
                this.replyMessage.classList.add('error');
                if (this.replyIcon) {
                    this.replyIcon.className = 'ph-bold ph-x-circle reply__icon';
                }
            }

            if (this.replyTitle) {
                this.replyTitle.textContent = title;
            }

            if (this.replyText) {
                this.replyText.innerHTML = message;
            }

            this.replyMessage.style.display = 'block';

            // Auto-hide success messages after 5 seconds
            if (type === 'success') {
                setTimeout(() => {
                    this.replyMessage.style.display = 'none';
                }, 5000);
            }
        }
    }

    clearErrors() {
        if (this.replyMessage) {
            this.replyMessage.style.display = 'none';
        }
    }
}

// Initialize contact form when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ContactFormHandler();
});

// Export for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ContactFormHandler;
}