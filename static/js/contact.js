document.addEventListener('DOMContentLoaded', function() {
    // Handle FAQ accordion
    const faqItems = document.querySelectorAll('.faq-question');
    
    faqItems.forEach(item => {
        item.addEventListener('click', function() {
            const answer = this.nextElementSibling;
            const isOpen = answer.classList.contains('open');
            
            // Close all other FAQ items
            document.querySelectorAll('.faq-answer').forEach(ans => {
                ans.classList.remove('open');
            });
            
            document.querySelectorAll('.faq-question').forEach(q => {
                q.classList.remove('active');
            });
            
            // Toggle current item
            if (!isOpen) {
                answer.classList.add('open');
                this.classList.add('active');
            }
        });
    });
    
    // Handle form submission
    const contactForm = document.querySelector('form[method="post"]');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const submitBtn = this.querySelector('.submit-btn');
            const originalText = submitBtn.textContent;
            
            submitBtn.textContent = 'Sending...';
            submitBtn.disabled = true;
            this.classList.add('form-loading');
            
            // Simulate form submission (replace with actual AJAX call)
            setTimeout(() => {
                // Reset form
                this.reset();
                
                // Show success message
                showContactAlert('success', 'Thank you! Your message has been sent successfully.');
                
                // Reset button
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                this.classList.remove('form-loading');
                
                // Hide alert after 5 seconds
                setTimeout(() => {
                    const alert = document.querySelector('.contact-alert');
                    if (alert) {
                        alert.style.opacity = '0';
                        setTimeout(() => alert.remove(), 300);
                    }
                }, 5000);
            }, 2000);
        });
    }
    
    // Form validation
    const formControls = document.querySelectorAll('.form-control');
    formControls.forEach(control => {
        control.addEventListener('blur', function() {
            validateField(this);
        });
        
        control.addEventListener('input', function() {
            if (this.classList.contains('invalid')) {
                validateField(this);
            }
        });
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Remove existing error classes
    field.classList.remove('invalid', 'valid');
    
    // Validation rules
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    } else if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    } else if (field.name === 'name' && value.length < 2) {
        isValid = false;
        errorMessage = 'Name must be at least 2 characters';
    } else if (field.name === 'subject' && value.length < 5) {
        isValid = false;
        errorMessage = 'Subject must be at least 5 characters';
    } else if (field.name === 'message' && value.length < 10) {
        isValid = false;
        errorMessage = 'Message must be at least 10 characters';
    }
    
    // Apply validation styling
    if (isValid) {
        field.classList.add('valid');
    } else {
        field.classList.add('invalid');
        showErrorTooltip(field, errorMessage);
    }
    
    return isValid;
}

function showErrorTooltip(field, message) {
    // Remove existing tooltip
    const existingTooltip = field.parentNode.querySelector('.error-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }
    
    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'error-tooltip';
    tooltip.textContent = message;
    tooltip.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        background: var(--danger-color);
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: var(--border-radius);
        font-size: 0.875rem;
        margin-top: 0.25rem;
        z-index: 1000;
        box-shadow: var(--shadow-medium);
        max-width: 300px;
    `;
    
    field.parentNode.style.position = 'relative';
    field.parentNode.appendChild(tooltip);
    
    // Remove tooltip after 3 seconds
    setTimeout(() => {
        if (tooltip.parentNode) {
            tooltip.style.opacity = '0';
            tooltip.style.transform = 'translateY(-10px)';
            setTimeout(() => tooltip.remove(), 300);
        }
    }, 3000);
}

function showContactAlert(type, message) {
    // Remove existing alerts
    const existingAlert = document.querySelector('.contact-alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `contact-alert contact-alert-${type}`;
    alert.innerHTML = `
        <div style="display: flex; align-items: center;">
            <span style="margin-right: 0.75rem; font-size: 1.25rem;">
                ${type === 'success' ? '✓' : '✗'}
            </span>
            <span>${message}</span>
        </div>
    `;
    
    // Insert at the top of the form
    const formContainer = document.querySelector('.contact-form-container');
    if (formContainer) {
        formContainer.insertBefore(alert, formContainer.firstChild);
        
        // Add animation
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            alert.style.transition = 'all 0.3s ease';
            alert.style.opacity = '1';
            alert.style.transform = 'translateY(0)';
        }, 100);
    }
}

// Google Maps integration (optional)
function initMap() {
    // This would be replaced with actual Google Maps API integration
    const mapPlaceholder = document.querySelector('.map-placeholder');
    if (mapPlaceholder) {
        mapPlaceholder.innerHTML = `
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📍</div>
                <div>Interactive Map Would Appear Here</div>
                <div style="font-size: 0.875rem; margin-top: 0.5rem; opacity: 0.7;">
                    Integration with Google Maps API
                </div>
            </div>
        `;
    }
}

// Initialize map when page loads
if (document.querySelector('.map-section')) {
    window.initMap = initMap;
}