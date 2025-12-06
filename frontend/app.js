// Configuration
// Update API_BASE_URL for your environment:
// - Local development: http://localhost:8000
// - Production: Your AWS API Gateway URL
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-api-gateway-url.amazonaws.com';  // TODO: Update for production

// State
let currentSessionId = null;
let studentId = null;

// DOM Elements
const startScreen = document.getElementById('startScreen');
const negotiationScreen = document.getElementById('negotiationScreen');
const evaluationScreen = document.getElementById('evaluationScreen');
const startForm = document.getElementById('startForm');
const chatForm = document.getElementById('chatForm');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startForm.addEventListener('submit', handleStartNegotiation);
    chatForm.addEventListener('submit', handleSendMessage);
});

// Start new negotiation session
async function handleStartNegotiation(e) {
    e.preventDefault();
    studentId = document.getElementById('studentId').value.trim();
    
    if (!studentId) {
        alert('Please enter your student ID');
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/sessions/new`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ student_id: studentId })
        });

        if (!response.ok) {
            throw new Error('Failed to create session');
        }

        const data = await response.json();
        currentSessionId = data.session_id;
        
        // Display deal parameters
        displayDealParameters(data.deal_parameters);
        
        // Add Alex's initial message
        addMessage('alex', data.initial_message.content);
        
        // Switch to negotiation screen
        startScreen.classList.add('hidden');
        negotiationScreen.classList.remove('hidden');
        
        messageInput.focus();
    } catch (error) {
        console.error('Error starting negotiation:', error);
        alert('Failed to start negotiation. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Send message to Alex
async function handleSendMessage(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error('Failed to send message');
        }

        const data = await response.json();
        
        // Add Alex's response
        addMessage('alex', data.alex_response);
        
        // Update status
        updateStatus(data);
        
        // Check if deal is closed
        if (data.deal_closed && data.evaluation) {
            setTimeout(() => {
                showEvaluation(data.evaluation);
            }, 1000);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Display deal parameters
function displayDealParameters(params) {
    const dealParams = document.getElementById('dealParams');
    dealParams.innerHTML = `
        <div class="param-item">
            <span class="param-label">Base Price:</span>
            <span class="param-value">$${params.base_price}/unit</span>
        </div>
        <div class="param-item">
            <span class="param-label">Target Quantity:</span>
            <span class="param-value">${params.target_quantity} units</span>
        </div>
        <div class="param-item">
            <span class="param-label">Delivery:</span>
            <span class="param-value">${params.delivery_days} days</span>
        </div>
        <div class="param-item">
            <span class="param-label">Quality:</span>
            <span class="param-value">Grade ${params.quality_grade}</span>
        </div>
        <div class="param-item">
            <span class="param-label">Warranty:</span>
            <span class="param-value">${params.warranty_months} months</span>
        </div>
    `;
}

// Add message to chat
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'alex' ? '🤖' : '👤';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update negotiation status
function updateStatus(data) {
    document.getElementById('turnCount').textContent = data.turn_count;
    document.getElementById('statusText').textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
    
    if (data.deal_closed) {
        document.getElementById('statusText').textContent = 'Deal Closed ✓';
        document.getElementById('statusText').style.color = '#22c55e';
    }
}

// Show evaluation results
function showEvaluation(evaluation) {
    const resultsDiv = document.getElementById('evaluationResults');
    
    if (!evaluation.deal_completed) {
        resultsDiv.innerHTML = '<p>Negotiation not completed yet.</p>';
        return;
    }

    const metrics = evaluation.metrics;
    const details = evaluation.deal_details;
    
    resultsDiv.innerHTML = `
        <div class="overall-score">
            <h3>Overall Score</h3>
            <div class="score-circle ${getScoreClass(evaluation.overall_score)}">
                ${evaluation.overall_score}
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h4>Price Achievement</h4>
                <div class="metric-score">${metrics.price_achievement}/100</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${metrics.price_achievement}%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h4>Efficiency</h4>
                <div class="metric-score">${metrics.efficiency}/100</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${metrics.efficiency}%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h4>Relationship Building</h4>
                <div class="metric-score">${metrics.relationship_building}/100</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${metrics.relationship_building}%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h4>Value Creation</h4>
                <div class="metric-score">${metrics.value_creation}/100</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${metrics.value_creation}%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h4>Strategic Negotiation</h4>
                <div class="metric-score">${metrics.strategic_negotiation}/100</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${metrics.strategic_negotiation}%"></div>
                </div>
            </div>
        </div>
        
        <div class="deal-summary">
            <h3>Final Deal Details</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-label">Final Price:</span>
                    <span class="summary-value">$${details.final_price}/unit</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Base Price:</span>
                    <span class="summary-value">$${details.base_price}/unit</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Savings:</span>
                    <span class="summary-value savings">$${details.base_price - details.final_price}/unit</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Quantity:</span>
                    <span class="summary-value">${details.quantity} units</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Delivery:</span>
                    <span class="summary-value">${details.delivery_days} days</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Turns Taken:</span>
                    <span class="summary-value">${details.turns_taken}</span>
                </div>
            </div>
        </div>
    `;
    
    negotiationScreen.classList.add('hidden');
    evaluationScreen.classList.remove('hidden');
}

// Get score class for color coding
function getScoreClass(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'average';
    return 'poor';
}

// Quick message helper
function quickMessage(message) {
    messageInput.value = message;
    messageInput.focus();
}

// Start new negotiation
function startNewNegotiation() {
    currentSessionId = null;
    chatMessages.innerHTML = '';
    document.getElementById('studentId').value = '';
    
    evaluationScreen.classList.add('hidden');
    startScreen.classList.remove('hidden');
}

// Loading state
function showLoading(isLoading) {
    const sendButton = chatForm.querySelector('button[type="submit"]');
    if (sendButton) {
        sendButton.disabled = isLoading;
        sendButton.textContent = isLoading ? 'Sending...' : 'Send';
    }
}
