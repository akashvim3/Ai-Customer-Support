/**
 * Chatbot JavaScript
 * Handles chatbot UI interactions and API communication
 */

(function($) {
    'use strict';

    // Chatbot Object
    const Chatbot = {
        // Configuration
        config: {
            apiEndpoint: '/api/chatbot/chat/message/',
            websocketUrl: null,
            sessionId: null,
            maxMessageLength: 5000,
            typingDelay: 1000
        },

        // State
        state: {
            isOpen: false,
            isTyping: false,
            conversationHistory: [],
            unreadCount: 0
        },

        // Initialize
        init: function() {
            console.log('Chatbot initializing...');
            this.getOrCreateSessionId();
            this.bindEvents();
            this.setupWebSocket();
        },

        // Get or create session ID
        getOrCreateSessionId: function() {
            let sessionId = localStorage.getItem('chatbot_session_id');
            if (!sessionId) {
                sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('chatbot_session_id', sessionId);
            }
            this.config.sessionId = sessionId;
        },

        // Bind events
        bindEvents: function() {
            const self = this;

            // Toggle chatbot
            $('#chatbotToggle').on('click', function() {
                self.toggleChatbot();
            });

            // Close chatbot
            $('#closeChatbot').on('click', function() {
                self.closeChatbot();
            });

            // Send message on button click
            $('#sendMessage').on('click', function() {
                self.sendMessage();
            });

            // Send message on Enter key
            $('#chatbotInput').on('keypress', function(e) {
                if (e.which === 13 && !e.shiftKey) {
                    e.preventDefault();
                    self.sendMessage();
                }
            });

            // Auto-resize textarea
            $('#chatbotInput').on('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });

            // Quick action buttons
            $(document).on('click', '.quick-action-btn', function() {
                const action = $(this).data('action');
                self.handleQuickAction(action);
            });

            // Suggestion buttons
            $(document).on('click', '.suggestion-btn', function() {
                const suggestion = $(this).text();
                $('#chatbotInput').val(suggestion);
                self.sendMessage();
            });

            // Feedback buttons
            $(document).on('click', '.feedback-btn', function() {
                const messageId = $(this).closest('.chat-message').data('message-id');
                const isPositive = $(this).hasClass('feedback-positive');
                self.sendFeedback(messageId, isPositive);
                $(this).addClass('active').siblings().removeClass('active');
            });
        },

        // Setup WebSocket
        setupWebSocket: function() {
            if (!this.config.websocketUrl) return;

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.config.sessionId}/`;

            this.websocket = new WebSocket(wsUrl);

            this.websocket.open = function() {
                console.log('WebSocket connected');
            };

            this.websocket.message = function(event) {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            }.bind(this);

            this.websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };

            this.websocket.enclose = function() {
                console.log('WebSocket disconnected');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            }.bind(this);
        },

        // Handle WebSocket message
        handleWebSocketMessage: function(data) {
            if (data.type === 'chat_message') {
                this.addBotMessage(data.message, data.intent);
            }
        },

        // Toggle chatbot
        toggleChatbot: function() {
            if (this.state.isOpen) {
                this.closeChatbot();
            } else {
                this.openChatbot();
            }
        },

        // Open chatbot
        openChatbot: function() {
            $('#chatbotContainer').addClass('active');
            this.state.isOpen = true;
            this.resetUnreadCount();
            $('#chatbotInput').focus();
        },

        // Close chatbot
        closeChatbot: function() {
            $('#chatbotContainer').removeClass('active');
            this.state.isOpen = false;
        },

        // Send message
        sendMessage: function() {
            const input = $('#chatbotInput');
            const message = input.val().trim();

            if (!message || message.length > this.config.maxMessageLength) {
                return;
            }

            // Add user message to UI
            this.addUserMessage(message);

            // Clear input
            input.val('').css('height', 'auto');

            // Show typing indicator
            this.showTypingIndicator();

            // Send to API
            $.ajax({
                url: this.config.apiEndpoint,
                method: 'POST',
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: JSON.stringify({
                    message: message,
                    session_id: this.config.sessionId
                }),
                success: function(response) {
                    this.hideTypingIndicator();
                    this.handleResponse(response);
                }.bind(this),
                error: function(xhr, status, error) {
                    this.hideTypingIndicator();
                    this.addBotMessage(
                        "I apologize, but I'm having trouble responding right now. Please try again.",
                        'error'
                    );
                    console.error('Chat error:', error);
                }.bind(this)
            });

            // Store in conversation history
            this.state.conversationHistory.push({
                type: 'user',
                message: message,
                timestamp: new Date()
            });
        },

        // Handle API response
        handleResponse: function(response) {
            // Add bot message
            this.addBotMessage(response.response, response.intent);

            // Add suggestions if available
            if (response.suggestions && response.suggestions.length > 0) {
                this.addSuggestions(response.suggestions);
            }

            // Check if escalation needed
            if (response.should_escalate) {
                this.showEscalationMessage();
            }

            // Store in conversation history
            this.state.conversationHistory.push({
                type: 'bot',
                message: response.response,
                intent: response.intent,
                timestamp: new Date()
            });
        },

        // Add user message
        addUserMessage: function(message) {
            const messageHtml = `
                <div class="chat-message user-message" data-timestamp="${Date.now()}">
                    <div class="message-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="message-content">
                        <p>${this.escapeHtml(message)}</p>
                        <div class="message-time">${this.formatTime(new Date())}</div>
                    </div>
                </div>
            `;

            $('#chatbotBody').append(messageHtml);
            this.scrollToBottom();
        },

        // Add bot message
        addBotMessage: function(message, intent = 'general') {
            const messageId = 'msg_' + Date.now();
            const messageHtml = `
                <div class="chat-message bot-message" data-message-id="${messageId}" data-intent="${intent}">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <p>${this.escapeHtml(message)}</p>
                        <div class="message-time">${this.formatTime(new Date())}</div>
                        <div class="message-feedback">
                            <button class="feedback-btn feedback-positive" title="Helpful">
                                <i class="fas fa-thumbs-up"></i>
                            </button>
                            <button class="feedback-btn feedback-negative" title="Not helpful">
                                <i class="fas fa-thumbs-down"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;

            $('#chatbotBody').append(messageHtml);
            this.scrollToBottom();

            // Increment unread count if closed
            if (!this.state.isOpen) {
                this.incrementUnreadCount();
            }
        },

        // Add suggestions
        addSuggestions: function(suggestions) {
            const suggestionsHtml = `
                <div class="suggestions-container">
                    ${suggestions.map(suggestion => `
                        <button class="suggestion-btn">${this.escapeHtml(suggestion)}</button>
                    `).join('')}
                </div>
            `;

            $('#chatbotBody').append(suggestionsHtml);
            this.scrollToBottom();
        },

        // Show typing indicator
        showTypingIndicator: function() {
            if ($('#typingIndicator').length) return;

            const typingHtml = `
                <div class="chat-message bot-message" id="typingIndicator">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content typing-indicator">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;

            $('#chatbotBody').append(typingHtml);
            this.scrollToBottom();
            this.state.isTyping = true;
        },

        // Hide typing indicator
        hideTypingIndicator: function() {
            $('#typingIndicator').remove();
            this.state.isTyping = false;
        },

        // Show escalation message
        showEscalationMessage: function() {
            const escalationHtml = `
                <div class="chat-message system-message">
                    <div class="message-content">
                        <p><i class="fas fa-info-circle"></i> This conversation has been escalated to a human agent. You'll receive a response soon.</p>
                    </div>
                </div>
            `;

            $('#chatbotBody').append(escalationHtml);
            this.scrollToBottom();
        },

        // Send feedback
        sendFeedback: function(messageId, isPositive) {
            $.ajax({
                url: '/api/chatbot/feedback/',
                method: 'POST',
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: JSON.stringify({
                    message_id: messageId,
                    is_positive: isPositive,
                    session_id: this.config.sessionId
                }),
                success: function() {
                    console.log('Feedback sent');
                },
                error: function(error) {
                    console.error('Error sending feedback:', error);
                }
            });
        },

        // Handle quick actions
        handleQuickAction: function(action) {
            const actionMessages = {
                'track_order': 'I need help tracking my order',
                'billing_help': 'I have a billing question',
                'technical_support': 'I need technical support',
                'general_inquiry': 'I have a general question'
            };

            const message = actionMessages[action] || action;
            $('#chatbotInput').val(message);
            this.sendMessage();
        },

        // Increment unread count
        incrementUnreadCount: function() {
            this.state.unreadCount++;
            this.updateUnreadBadge();
        },

        // Reset unread count
        resetUnreadCount: function() {
            this.state.unreadCount = 0;
            this.updateUnreadBadge();
        },

        // Update unread badge
        updateUnreadBadge: function() {
            const badge = $('.chatbot-badge');
            if (this.state.unreadCount > 0) {
                badge.text(this.state.unreadCount).show();
            } else {
                badge.hide();
            }
        },

        // Scroll to bottom
        scrollToBottom: function() {
            const chatBody = $('#chatbotBody');
            chatBody.animate({
                scrollTop: chatBody[0].scrollHeight
            }, 300);
        },

        // Format time
        formatTime: function(date) {
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        // Escape HTML
        escapeHtml: function(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }
    };

    // Initialize on document ready
    $(document).ready(function() {
        if ($('#chatbotWidget').length) {
            Chatbot.init();
        }
    });

    // Make Chatbot globally accessible
    window.Chatbot = Chatbot;

})(jQuery);
