// Theme management functionality
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Initialize theme from localStorage
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// Add loading animation to page transitions
function initializePageTransitions() {
    // Create loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.style.display = 'none';
    
    const loadingImg = document.createElement('img');
    loadingImg.src = '/assets/login-signup-loading.gif';
    loadingImg.alt = 'Loading...';
    loadingOverlay.appendChild(loadingImg);
    
    document.body.appendChild(loadingOverlay);

    // Add click event listeners to all navigation links
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && link.href && !link.href.startsWith('javascript:')) {
            e.preventDefault();
            loadingOverlay.style.display = 'flex';
            setTimeout(() => {
                window.location.href = link.href;
            }, 5000); // Show animation for 5 seconds before navigation
        }
    });
}

// Export functions
window.themeManager = {
    toggleTheme,
    initializeTheme,
    initializePageTransitions
}; 