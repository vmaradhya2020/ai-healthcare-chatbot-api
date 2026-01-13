// ============================================
// Register Page Logic
// ============================================

// Redirect to chat if already authenticated
if (isAuthenticated()) {
    window.location.href = 'chat.html';
}

// Handle registration form submission
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Clear previous messages
    clearError('emailError');
    clearError('passwordError');
    clearError('clientCodeError');
    hideFormError();
    hideFormSuccess();

    // Get form values
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const clientCode = document.getElementById('client_code').value.trim();

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

    if (!clientCode) {
        showError('clientCodeError', 'Client code is required');
        isValid = false;
    }

    if (!isValid) return;

    // Show loading state
    setLoading('registerBtn', true);

    try {
        // Call register API
        const response = await apiCall('/register', {
            method: 'POST',
            skipAuth: true,
            body: JSON.stringify({
                email: email,
                password: password,
                client_code: clientCode
            })
        });

        // Show success message
        showFormSuccess('Account created successfully! Redirecting to login...');

        // Save token and redirect after 2 seconds
        saveToken(response.access_token);
        setTimeout(() => {
            window.location.href = 'chat.html';
        }, 2000);

    } catch (error) {
        setLoading('registerBtn', false);
        showFormError(error.message || 'Registration failed. Please try again or contact support.');
    }
});
