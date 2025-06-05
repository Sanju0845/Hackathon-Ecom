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
    loadingOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.8);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 99999;
    `;
    // Lottie container
    const lottieContainer = document.createElement('div');
    lottieContainer.id = 'loadingLottieContainer';
    lottieContainer.style.width = '400px';
    lottieContainer.style.height = '400px';
    loadingOverlay.appendChild(lottieContainer);
    document.body.appendChild(loadingOverlay);

    // Initialize Lottie animation
    let lottieInstance = null;
    function showLottie() {
        if (!lottieInstance) {
            lottieInstance = lottie.loadAnimation({
                container: lottieContainer,
                renderer: 'svg',
                loop: true,
                autoplay: true,
                path: '/assets/loading-signup.json'
            });
        } else {
            lottieInstance.goToAndPlay(0);
        }
    }

    // Add click event listeners to all navigation links
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && link.href && !link.href.startsWith('javascript:')) {
            e.preventDefault();
            loadingOverlay.style.display = 'flex';
            showLottie();
            setTimeout(() => {
                window.location.href = link.href;
            }, 2000); // 2 seconds for faster transition
        }
    });
}

// Export functions
window.themeManager = {
    toggleTheme,
    initializeTheme,
    initializePageTransitions
}; 