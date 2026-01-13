// ============================================
// Authentication Utilities
// ============================================

// Use dynamic URL that works on both localhost and HuggingFace Spaces
// For local development on port 3000 or 8080, use backend on port 8001
// For HuggingFace Spaces, use the embedded API from same origin
const API_BASE_URL = (window.location.port === '3000' || window.location.port === '8080' || window.location.hostname === 'localhost') 
    ? 'http://localhost:8001'  // Local development - connect to backend on 8001
    : window.location.origin;  // Production (HuggingFace Spaces)

// Token Management
const AUTH_TOKEN_KEY = 'healthcare_auth_token';

function saveToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function removeToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
}

function isAuthenticated() {
    return !!getToken();
}

// Logout function
function logout() {
    removeToken();
    window.location.href = 'index.html';
}

// API Call Helper
async function apiCall(endpoint, options = {}) {
    const token = getToken();

    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    };

    // Add authorization header if token exists
    if (token && !options.skipAuth) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        console.log('Calling:', API_BASE_URL + endpoint, config);
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);

        // Handle connection errors
        if (!response) {
            throw new Error('Unable to connect to server. Please make sure the backend is running on http://localhost:8001');
        }

        // Try to parse JSON response
        let data;
        try {
            data = await response.json();
        } catch (parseError) {
            console.error('Failed to parse response:', parseError);
            data = { detail: 'Invalid response from server' };
        }

        console.log('Response data:', data);

        // Handle 401 Unauthorized
        if (response.status === 401) {
            removeToken();
            window.location.href = 'index.html';
            throw new Error('Session expired. Please login again.');
        }

        // Handle error responses
        if (!response.ok) {
            const errorMessage = data.detail || data.message || 'An error occurred';
            throw new Error(errorMessage);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Form Validation Helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
    }
}

function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '';
        element.style.display = 'none';
    }
}

function showFormError(message) {
    const errorDiv = document.getElementById('formError');
    const errorText = document.getElementById('formErrorText');
    if (errorDiv && errorText) {
        errorText.textContent = message;
        errorDiv.style.display = 'flex';
    }
}

function hideFormError() {
    const errorDiv = document.getElementById('formError');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function showFormSuccess(message) {
    const successDiv = document.getElementById('formSuccess');
    const successText = document.getElementById('formSuccessText');
    if (successDiv && successText) {
        successText.textContent = message;
        successDiv.style.display = 'flex';
    }
}

function hideFormSuccess() {
    const successDiv = document.getElementById('formSuccess');
    if (successDiv) {
        successDiv.style.display = 'none';
    }
}

// Loading State Helpers
function setLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    const btnText = button.querySelector('.btn-text');
    const loader = button.querySelector('.loader');

    if (isLoading) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (loader) loader.style.display = 'block';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'block';
        if (loader) loader.style.display = 'none';
    }
}

// Password Toggle
function setupPasswordToggle() {
    const toggleBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
        });
    }
}

// Initialize password toggle on page load
document.addEventListener('DOMContentLoaded', setupPasswordToggle);
