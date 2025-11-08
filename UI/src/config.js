const isLocalhost = window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1'

export const API_URL = isLocalhost
  ? 'https://etsignage-backend-dev.onrender.com'
  : 'https://etsignage-backend.onrender.com'

console.log('🔧 Using API:', API_URL)