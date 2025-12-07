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
    conversationHistory = session.history || [];

    console.log('Session created:', sessionId);

    // Clear chat history from UI
    clearChatHistory();

    // Display greeting
    displayMessage('assistant', session.greeting);

    // Show deal status section
    document.getElementById('deal-status').classList.remove('hidden');

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

    // Update deal metrics if available
    if (result.missing_terms) {
      updateDealMetrics(result.missing_terms);
    }

    // Check for agreement
    if (result.agreement_detected && result.agreed_terms) {
      negotiationState = 'CLOSING';
      handleAgreementDetected(result.agreed_terms);
    } else if (result.missing_terms && result.missing_terms.length > 0) {
      // Still negotiating
      const missing = result.missing_terms.join(', ');
      updateNegotiationStatus(`Waiting on: ${missing}`);
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
  contentDiv.textContent = content; // Use textContent to prevent XSS

  messageDiv.appendChild(contentDiv);
  chatHistory.appendChild(messageDiv);

  // Auto-scroll to bottom
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

/**
 * Clear chat history from UI (but not from state)
 */
function clearChatHistory() {
  const chatHistory = document.getElementById('chat-history');
  // Keep the initial greeting if exists, or clear all
  chatHistory.innerHTML = '';
}

/**
 * Update deal metrics display when partial agreement is reached
 */
function updateDealMetrics(missingTerms) {
  const dealStatus = document.getElementById('deal-status');

  // Parse missing terms and extract current values
  // This is a simplified version - full implementation would parse conversation
  const priceElement = document.getElementById('metric-price');
  const deliveryElement = document.getElementById('metric-delivery');
  const volumeElement = document.getElementById('metric-volume');

  if (!missingTerms.includes('price') && priceElement) {
    priceElement.textContent = 'Agreed ✓';
    priceElement.style.color = 'var(--success-text)';
  }

  if (!missingTerms.includes('delivery') && deliveryElement) {
    deliveryElement.textContent = 'Agreed ✓';
    deliveryElement.style.color = 'var(--success-text)';
  }

  if (!missingTerms.includes('volume') && volumeElement) {
    volumeElement.textContent = 'Agreed ✓';
    volumeElement.style.color = 'var(--success-text)';
  }
}

/**
 * Update negotiation status text
 */
function updateNegotiationStatus(status) {
  // This can be expanded to update a status display element
  console.log('Status:', status);
}

/**
 * Handle agreement detection - show confirmation dialog
 */
function handleAgreementDetected(agreedTerms) {
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
    <h3 style="color: var(--text-primary); margin-bottom: 1rem;">✅ Deal Confirmed!</h3>
    <div style="background: var(--success-bg); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.95rem;">
      <p style="margin-bottom: 0.5rem;"><strong>Price:</strong> $${agreedTerms.price} per unit</p>
      <p style="margin-bottom: 0.5rem;"><strong>Delivery:</strong> ${agreedTerms.delivery} days</p>
      <p><strong>Volume:</strong> ${agreedTerms.volume?.toLocaleString() || 'Standard'} units</p>
    </div>
    <div style="display: flex; gap: 1rem;">
      <button id="confirm-deal-btn" style="
        flex: 1;
        background: var(--primary-color);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
      ">Finalize Deal</button>
      <button id="continue-negotiating-btn" style="
        flex: 1;
        background: var(--border-color);
        color: var(--text-primary);
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
    modal.remove();
    await finalizeDeal(agreedTerms);
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

    displayMessage('assistant', 'Excellent! Your deal has been finalized. Generating your performance evaluation...');

    // Fetch evaluation
    const evaluation = await api.evaluateDeal();

    // Display evaluation report
    displayEvaluation(evaluation);

  } catch (error) {
    console.error('Error finalizing deal:', error);
    displayMessage('error', 'Failed to generate evaluation. Please try again.');
  }
}

/**
 * Display comprehensive evaluation report
 */
function displayEvaluation(evaluation) {
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

  const scoreColor = evaluation.overall_score >= 80 ? '#16a34a' : 
                     evaluation.overall_score >= 60 ? '#ea580c' : '#dc2626';

  const box = document.createElement('div');
  box.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 2rem;
    max-width: 500px;
    margin: 2rem auto;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  `;

  const metricsHtml = Object.entries(evaluation.metrics).map(([key, metric]) => `
    <div style="margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <strong style="text-transform: capitalize;">${key.replace(/_/g, ' ')}</strong>
        <span style="background: ${scoreColor}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-weight: 600;">
          ${metric.score}/100 (${metric.grade})
        </span>
      </div>
      <small style="color: var(--text-secondary);">Weight: ${metric.weight}</small>
    </div>
  `).join('');

  box.innerHTML = `
    <h2 style="color: var(--text-primary); margin-bottom: 1.5rem; text-align: center;">📊 Negotiation Evaluation</h2>

    <div style="text-align: center; margin-bottom: 2rem; padding: 1.5rem; background: var(--assistant-msg-bg); border-radius: 8px;">
      <div style="font-size: 3em; color: ${scoreColor}; font-weight: bold;">${evaluation.overall_score}</div>
      <div style="font-size: 1.1rem; color: var(--text-primary); font-weight: 600;">Overall Score (${evaluation.overall_grade})</div>
    </div>

    <h3 style="color: var(--text-primary); margin-bottom: 1rem;">Metric Scores</h3>
    <div style="margin-bottom: 2rem;">${metricsHtml}</div>

    <h3 style="color: var(--text-primary); margin-bottom: 1rem;">Deal Analysis</h3>
    <div style="background: var(--assistant-msg-bg); padding: 1rem; border-radius: 8px; margin-bottom: 2rem; font-size: 0.9rem; line-height: 1.6;">
      <p><strong>Price:</strong> $${evaluation.negotiation_analysis.price_analysis.final} (Target: $${evaluation.negotiation_analysis.price_analysis.target})</p>
      <p><strong>Delivery:</strong> ${evaluation.negotiation_analysis.delivery_analysis.final} days (Target: ${evaluation.negotiation_analysis.delivery_analysis.target} days)</p>
      <p><strong>Volume:</strong> ${evaluation.negotiation_analysis.volume?.toLocaleString()} units</p>
      <p><strong>Rounds:</strong> ${evaluation.negotiation_rounds}</p>
    </div>

    <h3 style="color: var(--text-primary); margin-bottom: 1rem;">Feedback</h3>
    <div style="background: var(--user-msg-bg); padding: 1rem; border-radius: 8px; margin-bottom: 2rem; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap;">
${evaluation.feedback}
    </div>

    <button id="new-negotiation-btn" style="
      width: 100%;
      background: var(--primary-color);
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