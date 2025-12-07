/**
 * API Client for AI Negotiation Backend
 * Handles all communication with FastAPI backend
 */

class NegotiationAPI {
  constructor() {
    this.sessionId = null;
    // Determine API URL based on environment
    this.baseUrl = this.getBaseUrl();
    console.log('API Base URL:', this.baseUrl);
  }

  /**
   * Get API base URL based on environment
   */
  getBaseUrl() {
    // Check for environment variable first
    if (typeof process !== 'undefined' && process.env.REACT_APP_API_URL) {
      return process.env.REACT_APP_API_URL;
    }

    // Check for localStorage override (useful for testing)
    const storedUrl = localStorage.getItem('API_BASE_URL');
    if (storedUrl) {
      return storedUrl;
    }

    // Default to relative path for same-origin requests
    const currentUrl = window.location.origin;
    
    // If in production (https), assume API is at same domain
    if (window.location.protocol === 'https:') {
      return currentUrl;
    }

    // For localhost development, try common ports
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }

    // Fallback to current origin
    return currentUrl;
  }

  /**
   * Override API URL (useful for testing/debugging)
   */
  setBaseUrl(url) {
    this.baseUrl = url;
    localStorage.setItem('API_BASE_URL', url);
    console.log('API URL updated to:', url);
  }

  /**
   * Make HTTP request with error handling
   */
  async request(endpoint, method = 'GET', body = null) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      mode: 'cors',
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${method} ${endpoint}]:`, error.message);
      throw error;
    }
  }

  /**
   * Create new negotiation session
   * @param {string|null} studentId - Optional student ID for reproducible parameters
   * @returns {Promise<Object>} Session data with greeting and parameters
   */
  async createSession(studentId = null) {
    const params = studentId ? `?student_id=${studentId}` : '';
    const data = await this.request(`/api/sessions/new${params}`, 'POST');
    this.sessionId = data.session_id;
    return data;
  }

  /**
   * Send user message and get AI response
   * @param {string} userInput - User's message/offer
   * @returns {Promise<Object>} AI response with agreement status
   */
  async sendMessage(userInput) {
    if (!this.sessionId) {
      throw new Error('No active session. Create a session first.');
    }

    return this.request('/api/chat', 'POST', {
      session_id: this.sessionId,
      user_input: userInput,
    });
  }

  /**
   * Retrieve complete session data
   * @returns {Promise<Object>} Full session with history
   */
  async getSession() {
    if (!this.sessionId) {
      throw new Error('No active session.');
    }

    return this.request(`/api/sessions/${this.sessionId}`);
  }

  /**
   * Get evaluation for completed negotiation
   * @returns {Promise<Object>} Evaluation report with scores and feedback
   */
  async evaluateDeal() {
    if (!this.sessionId) {
      throw new Error('No active session.');
    }

    return this.request(`/api/deals/${this.sessionId}/evaluate`);
  }

  /**
   * Delete/close a session
   * @returns {Promise<Object>} Confirmation message
   */
  async deleteSession() {
    if (!this.sessionId) {
      throw new Error('No active session.');
    }

    const result = await this.request(`/api/sessions/${this.sessionId}`, 'DELETE');
    this.sessionId = null;
    return result;
  }

  /**
   * List all active sessions (admin/testing)
   * @returns {Promise<Object>} List of sessions
   */
  async listSessions() {
    return this.request('/api/sessions');
  }

  /**
   * List all completed deals (admin/testing)
   * @returns {Promise<Object>} List of completed deals
   */
  async listCompletedDeals() {
    return this.request('/api/deals');
  }

  /**
   * Check API health/connectivity
   * @returns {Promise<boolean>} True if API is reachable
   */
  async checkHealth() {
    try {
      const response = await this.request('/health');
      return response.status === 'ok' || response.status === 'running';
    } catch (error) {
      console.warn('API health check failed:', error.message);
      return false;
    }
  }
}

// Make class available globally when loaded as script tag
if (typeof window !== 'undefined') {
  window.NegotiationAPI = NegotiationAPI;
}

// Also support CommonJS/ES6 export if used as module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NegotiationAPI;
}