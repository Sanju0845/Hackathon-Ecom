// Check if user is admin
function checkAdmin() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (!user.is_admin) {
        console.log('Non-admin user detected, redirecting to login...');
        window.location.replace('/users/login.html');
        return false;
    }
    return true;
}

// Run check immediately
checkAdmin(); 