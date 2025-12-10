/**
 * AI Negotiation Frontend - Main Application Logic
 * Handles session management, message flow, agreement detection, and evaluation
 */

// Global state
let api = null;
let dealParams = null;
let conversationHistory = [];
let sessionId = null;
let negotiationState = 'SETUP'; // SETUP, NEGOTIATING, CLOSING, EVALUATION

/**
 * Initialize API and event listeners on page load
 */
document.addEventListener('DOMContentLoaded', function() {
  // Initialize API (it's loaded as a global from api.js script tag in HTML)
  if (typeof NegotiationAPI !== 'undefined') {
    api = new NegotiationAPI();
    console.log('API initialized:', api);
  } else {
    console.error('API class not found. Check api.js is loaded.');
  }

  // Event Listeners
  const newChatBtn = document.getElementById('new-chat-btn');
  const sendBtn = document.getElementById('send-btn');
  const userInput = document.getElementById('user-input');
  
  if (newChatBtn) newChatBtn.addEventListener('click', startNewNegotiation);
  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  if (userInput) userInput.addEventListener('keypress', handleKeyPress);

  // Radio button handlers for parameter source
  const radioButtons = document.querySelectorAll('input[name="seedParams"]');
  radioButtons.forEach(radio => {
    radio.addEventListener('change', handleParameterSourceChange);
  });

  console.log('Event listeners registered');
});

/**
 * Handle parameter source selection (Random vs Student ID)
 */
function handleParameterSourceChange(e) {
  const studentIdGroup = document.getElementById('student-id-group');
  if (e.target.value === 'student') {
    studentIdGroup.style.display = 'flex';
  } else {
    studentIdGroup.style.display = 'none';
  }
}

/**
 * Start new negotiation session
 */
async function startNewNegotiation() {
  try {
    negotiationState = 'NEGOTIATING';

    // Get student ID if Student ID mode is selected
    const seedMode = document.querySelector('input[name="seedParams"]:checked')?.value;
    let studentId = null;

    if (seedMode === 'student') {
      studentId = document.getElementById('student-id-input')?.value || null;
      if (!studentId) {
        displayMessage('error', 'Please enter a Student ID');
        return;
      }
    }

    // Disable button during loading
    const newChatBtn = document.getElementById('new-chat-btn');
    newChatBtn.disabled = true;
    newChatBtn.textContent = 'Starting...';

    // Create new session
    const session = await api.createSession(studentId);
    sessionId = session.session_id;
    dealParams = session.deal_params;
    
    // API v2 returns greeting directly, v1 returned history
    const greeting = session.greeting || (session.history ? session.history[0].content : "Hello!");
    
    console.log('Session created:', sessionId);

    // Clear chat history from UI
    clearChatHistory();

    // Display greeting
    displayMessage('assistant', greeting);

    // Show deal status section & reset metrics
    document.getElementById('deal-status').classList.remove('hidden');
    resetMetrics();

    // Re-enable button
    newChatBtn.disabled = false;
    newChatBtn.textContent = '↻ New Chat';

  } catch (error) {
    console.error('Error starting negotiation:', error);
    displayMessage('error', 'Failed to start negotiation. Please try again.');
    document.getElementById('new-chat-btn').disabled = false;
  }
}

/**
 * Handle Enter key in message input
 */
function handleKeyPress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

/**
 * Send user message and get AI response
 */
async function sendMessage() {
  const input = document.getElementById('user-input');
  const userMessage = input.value.trim();

  if (!userMessage || !sessionId) {
    return;
  }

  try {
    // Disable send button during processing
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;

    // Display user message
    displayMessage('user', userMessage);
    input.value = '';
    input.style.height = 'auto'; // Reset textarea height

    // Get AI response
    const result = await api.sendMessage(userMessage);
    displayMessage('assistant', result.ai_response);

    // --- UPDATED LOGIC FOR NEW BACKEND ---
    // 1. Update Metrics if terms were proposed
    if (result.proposed_terms) {
      updateDealMetrics(result.proposed_terms);
    }

    // 2. Check if Backend flagged "Deal Ready"
    if (result.deal_ready && result.proposed_terms) {
       negotiationState = 'CLOSING';
       handleAgreementDetected(result.proposed_terms);
    }

    // Re-enable send button
    sendBtn.disabled = false;
    input.focus();

  } catch (error) {
    console.error('Error sending message:', error);
    displayMessage('error', 'Failed to send message. Please try again.');
    document.getElementById('send-btn').disabled = false;
  }
}

/**
 * Display message in chat window
 */
function displayMessage(role, content) {
  const chatHistory = document.getElementById('chat-history');

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  
  // Handle newlines better for AI responses
  const formattedContent = content.replace(/\n/g, '<br>');
  contentDiv.innerHTML = formattedContent; 

  messageDiv.appendChild(contentDiv);
  chatHistory.appendChild(messageDiv);

  // Auto-scroll to bottom
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

/**
 * Clear chat history from UI
 */
function clearChatHistory() {
  const chatHistory = document.getElementById('chat-history');
  chatHistory.innerHTML = '';
}

/**
 * Reset metric displays
 */
function resetMetrics() {
    document.getElementById('metric-price').textContent = '--';
    document.getElementById('metric-delivery').textContent = '--';
    document.getElementById('metric-volume').textContent = '--';
}

/**
 * Update deal metrics display
 */
function updateDealMetrics(terms) {
  const priceElement = document.getElementById('metric-price');
  const deliveryElement = document.getElementById('metric-delivery');
  const volumeElement = document.getElementById('metric-volume');

  if (terms.price) {
    priceElement.textContent = `$${terms.price}`;
    priceElement.style.color = 'var(--success-text)'; // Use your CSS variable
  }
  if (terms.delivery) {
    deliveryElement.textContent = `${terms.delivery} days`;
    deliveryElement.style.color = 'var(--success-text)';
  }
  if (terms.volume) {
    // Format number with commas
    volumeElement.textContent = terms.volume.toLocaleString() + ' units';
    volumeElement.style.color = 'var(--success-text)';
  }
}


/**
 * Handle agreement detection - show confirmation dialog
 */
function handleAgreementDetected(agreedTerms) {
  // Remove existing modals if any
  const existingModal = document.querySelector('.confirmation-modal');
  if (existingModal) existingModal.remove();

  // Create and display confirmation modal
  const modal = document.createElement('div');
  modal.className = 'confirmation-modal';
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  `;

  const box = document.createElement('div');
  box.className = 'confirmation-box';
  box.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 2rem;
    max-width: 400px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  `;

  box.innerHTML = `
    <h3 style="color: #333; margin-bottom: 1rem;">✅ Deal Confirmed!</h3>
    <div style="background: #f0fdf4; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.95rem;">
      <p style="margin-bottom: 0.5rem;"><strong>Price:</strong> $${agreedTerms.price} per unit</p>
      <p style="margin-bottom: 0.5rem;"><strong>Delivery:</strong> ${agreedTerms.delivery} days</p>
      <p><strong>Volume:</strong> ${agreedTerms.volume?.toLocaleString() || 'Standard'} units</p>
    </div>
    <div style="display: flex; gap: 1rem;">
      <button id="confirm-deal-btn" style="
        flex: 1;
        background: #16a34a;
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
      ">Finalize & Grade</button>
      <button id="continue-negotiating-btn" style="
        flex: 1;
        background: #e5e7eb;
        color: #374151;
        border: none;
        padding: 0.75rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
      ">Continue Negotiating</button>
    </div>
  `;

  modal.appendChild(box);
  document.body.appendChild(modal);

  // Event handlers
  document.getElementById('confirm-deal-btn').addEventListener('click', async () => {
    // Show loading state
    document.getElementById('confirm-deal-btn').textContent = "Grading...";
    document.getElementById('confirm-deal-btn').disabled = true;
    await finalizeDeal(agreedTerms);
    modal.remove();
  });

  document.getElementById('continue-negotiating-btn').addEventListener('click', () => {
    modal.remove();
    negotiationState = 'NEGOTIATING';
    document.getElementById('user-input').focus();
  });
}

/**
 * Finalize deal and trigger evaluation
 */
async function finalizeDeal(agreedTerms) {
  try {
    negotiationState = 'EVALUATION';

    displayMessage('assistant', 'Excellent! Deal confirmed. Generating your performance evaluation...');

    // Fetch evaluation from backend
    // PASSING TERMS TO API
    const result = await api.evaluateDeal(agreedTerms);

    // Display evaluation report
    displayEvaluation(result.evaluation_report);

  } catch (error) {
    console.error('Error finalizing deal:', error);
    displayMessage('error', 'Failed to generate evaluation. Please try again.');
  }
}

/**
 * Display comprehensive evaluation report
 * UPDATED: Handles the text string returned by Bedrock
 */
function displayEvaluation(reportText) {
  const modal = document.createElement('div');
  modal.className = 'evaluation-modal';
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    overflow-y: auto;
  `;

  const box = document.createElement('div');
  box.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 2rem;
    max-width: 600px;
    width: 90%;
    margin: 2rem auto;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    max-height: 80vh;
    overflow-y: auto;
  `;

  // Render the text report cleanly
  box.innerHTML = `
    <h2 style="color: #333; margin-bottom: 1.5rem; text-align: center;">📊 Negotiation Report</h2>

    <div style="background: #f9fafb; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; font-size: 1rem; line-height: 1.6; white-space: pre-wrap; font-family: sans-serif;">
${reportText}
    </div>

    <button id="new-negotiation-btn" style="
      width: 100%;
      background: #2563eb;
      color: white;
      border: none;
      padding: 1rem;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      font-size: 1rem;
    ">Start New Negotiation</button>
  `;

  modal.appendChild(box);
  document.body.appendChild(modal);

  document.getElementById('new-negotiation-btn').addEventListener('click', () => {
    modal.remove();
    location.reload(); // Fresh start
  });
}
