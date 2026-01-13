# Healthcare AI Assistant - Frontend

A clean, professional HTML/CSS/JavaScript frontend for the Healthcare AI Chatbot.

## Features

✅ **No Framework Required** - Pure HTML, CSS, and vanilla JavaScript
✅ **Professional Healthcare Theme** - Clean, modern design
✅ **Responsive Design** - Works on desktop, tablet, and mobile
✅ **JWT Authentication** - Secure login and registration
✅ **Real-time Chat** - Interactive chat interface
✅ **Chat History** - Loads previous conversations
✅ **Intent & Source Display** - Shows AI classification metadata
✅ **Password Toggle** - Show/hide password functionality
✅ **Loading States** - Visual feedback during API calls
✅ **Error Handling** - User-friendly error messages

## File Structure

```
frontend/
├── index.html          # Login page
├── register.html       # Registration page
├── chat.html           # Main chat interface
├── css/
│   └── styles.css      # All styles (professional healthcare theme)
└── js/
    ├── auth.js         # Authentication utilities & API calls
    ├── login.js        # Login page logic
    ├── register.js     # Registration page logic
    └── chat.js         # Chat page logic & message handling
```

## How to Run

### Step 1: Start the Backend Server

```bash
cd C:\capstone_ic_ik\ai-healthcare-chatbot-api-main
ichealthchatbot\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Backend will run on: `http://localhost:8001`

### Step 2: Open the Frontend

Simply open the `index.html` file in your browser:

**Option 1: Double-click**
- Navigate to `C:\capstone_ic_ik\ai-healthcare-chatbot-api-main\frontend\`
- Double-click `index.html`

**Option 2: Use a local server (recommended for development)**
```bash
# If you have Python installed
cd frontend
python -m http.server 8080

# Then open: http://localhost:8080
```

**Option 3: Use VS Code Live Server**
- Right-click on `index.html`
- Select "Open with Live Server"

### Step 3: Login or Register

**Default Credentials** (if database is seeded):
- Email: `admin@cityhospital.com`
- Password: `password123`

Or create a new account using the registration page.

## API Configuration

The frontend is configured to connect to the backend at:
```javascript
API_BASE_URL = 'http://localhost:8001'
```

If your backend runs on a different port, update this in `js/auth.js`.

## Pages

### 1. Login Page (`index.html`)
- Email and password authentication
- Form validation
- Password show/hide toggle
- "Remember me" functionality via localStorage
- Link to registration page

### 2. Registration Page (`register.html`)
- Email, password, and client code fields
- Real-time validation
- Success message with auto-redirect
- Link back to login page

### 3. Chat Interface (`chat.html`)
- Clean message bubble design
- User and bot avatars
- Typing indicator animation
- Message timestamps
- Intent and data source chips
- Auto-scroll to latest message
- Chat history loading
- Clear chat functionality
- Logout option

## Features Explained

### Authentication
- JWT tokens stored in localStorage
- Auto-redirect if not authenticated
- Token sent with every API request
- Automatic logout on 401 errors

### Chat Functionality
- Send messages with Enter key
- Shift+Enter for new lines
- Auto-resizing textarea
- Message history persistence
- Real-time AI responses
- Error handling with user-friendly messages

### Responsive Design
- Mobile-friendly layout
- Touch-optimized controls
- Adaptive font sizes
- Responsive message bubbles

## Browser Compatibility

Tested and working on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

## Security Notes

1. **CORS**: Backend must allow `http://localhost:*` in development
2. **HTTPS**: Use HTTPS in production
3. **Tokens**: JWT tokens stored in localStorage (consider httpOnly cookies for production)
4. **Validation**: Client-side validation + server-side validation

## Troubleshooting

### "Failed to fetch" error
- Make sure backend is running on port 8001
- Check CORS settings in backend `.env` file
- Ensure `CORS_ORIGINS=http://localhost:4200,http://localhost:8080,http://localhost:3000` includes your frontend URL

### Login not working
- Check browser console for errors
- Verify backend is accessible at `http://localhost:8001/health`
- Check database connection
- Ensure user exists in database

### Chat messages not sending
- Check authentication token in localStorage
- Verify API endpoint is correct
- Check backend logs for errors

## Production Deployment

For production:

1. **Update API URL** in `js/auth.js`:
   ```javascript
   const API_BASE_URL = 'https://your-api-domain.com';
   ```

2. **Enable HTTPS**

3. **Update CORS** in backend `.env`:
   ```
   CORS_ORIGINS=https://your-frontend-domain.com
   ```

4. **Minify Assets** (optional):
   - Minify CSS and JavaScript
   - Optimize images
   - Enable gzip compression

## Support

For issues or questions, check the backend API logs or contact support.

---

**Built with ❤️ for Healthcare**
