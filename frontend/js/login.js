// ============================================
// Login Page Logic
// ============================================

// Redirect to chat if already authenticated
if (isAuthenticated()) {
    window.location.href = 'chat.html';
}

// Handle login form submission
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Clear previous errors
    clearError('emailError');
    clearError('passwordError');
    hideFormError();

    // Get form values
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    // Validate inputs
    let isValid = true;

    if (!validateEmail(email)) {
        showError('emailError', 'Please enter a valid email address');
        isValid = false;
    }

    if (!validatePassword(password)) {
        showError('passwordError', 'Password must be at least 8 characters');
        isValid = false;
    }

    if (!isValid) return;

    // Show loading state
    setLoading('loginBtn', true);

// console.write('Attempting to log in with email:', email);
console.log('Password:', password);

    try {
        // Call login API
        const response = await apiCall('/login', {
            method: 'POST',
            skipAuth: true,
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        // console.write('Response...........', response);
        console.log('Response:', response);
        // Save token
        saveToken(response.access_token);

        // Redirect to chat
        window.location.href = 'chat.html';

    } catch (error) {
        setLoading('loginBtn', false);
        showFormError(error.message || 'Invalid email or password. Please try again.');
    }
});
