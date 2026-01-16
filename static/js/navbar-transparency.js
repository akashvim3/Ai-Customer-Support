document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        // Set initial state based on scroll position
        if (window.scrollY === 0) {
            navbar.classList.add('navbar-transparent');
            navbar.classList.remove('scrolled');
        } else {
            navbar.classList.remove('navbar-transparent');
            navbar.classList.add('scrolled');
        }

        // Listen for scroll events
        window.addEventListener('scroll', function() {
            if (window.scrollY > 10) {
                navbar.classList.remove('navbar-transparent');
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.add('navbar-transparent');
                navbar.classList.remove('scrolled');
            }
        });
    }
});