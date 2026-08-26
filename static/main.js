/**
 * Main JS Controller for Aether Calendar Assistant
 * Features: Chat, API calls, event management, and Web Speech API (TTS & STT).
 */

document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const chatHistory = document.getElementById("chat-history-container");
    const chatTextarea = document.getElementById("chat-textarea");
    const sendBtn = document.getElementById("send-btn");
    const micBtn = document.getElementById("mic-btn");
    const ttsToggleBtn = document.getElementById("tts-toggle-btn");
    const helpInfoBtn = document.getElementById("help-info-btn");
    
    const geminiKeyInput = document.getElementById("gemini-key-input");
    const saveKeyBtn = document.getElementById("save-key-btn");
    
    const quickAddForm = document.getElementById("quick-add-form");
    const eventsListContainer = document.getElementById("events-list-container");
    
    const statusIndicator = document.querySelector(".status-indicator");
    const statusText = document.querySelector(".status-text");

    // Mobile Sidebar Drawer Toggle
    const menuToggleBtn = document.getElementById("menu-toggle-btn");
    const closeSidebarBtn = document.getElementById("close-sidebar-btn");
    const sidebar = document.getElementById("app-sidebar");
    
    if (menuToggleBtn && closeSidebarBtn && sidebar) {
        menuToggleBtn.addEventListener("click", () => {
            sidebar.classList.add("active");
        });
        
        closeSidebarBtn.addEventListener("click", () => {
            sidebar.classList.remove("active");
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", (e) => {
            if (sidebar.classList.contains("active") && 
                !sidebar.contains(e.target) && 
                !menuToggleBtn.contains(e.target)) {
                sidebar.classList.remove("active");
            }
        });
    }

    // State Variables
    let isTtsEnabled = true;
    let isRecording = false;
    let recognition = null;
    
    // Auto-fill Gemini Key from LocalStorage
    const savedKey = localStorage.getItem("gemini_api_key");
    if (savedKey) {
        geminiKeyInput.value = savedKey;
    }

    // Save Gemini Key to LocalStorage
    saveKeyBtn.addEventListener("click", () => {
        const key = geminiKeyInput.value.trim();
        localStorage.setItem("gemini_api_key", key);
        
        // Visual feedback
        saveKeyBtn.innerHTML = '<i class="fa-solid fa-circle-check" style="color: #10b981;"></i>';
        setTimeout(() => {
            saveKeyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
        }, 1500);
    });

    // Auto-resize textarea as user types
    chatTextarea.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight - 10) + "px";
    });

    // Handle Enter key in textarea
    chatTextarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send Button Click
    sendBtn.addEventListener("click", sendMessage);

    // Initial Load
    fetchUpcomingEvents();

    // Help Dialog Tooltip
    helpInfoBtn.addEventListener("click", () => {
        addMessage("assistant", "💡 <strong>Aether Quick Tips:</strong><br>" + 
                   "1. Enter your Gemini API key in the sidebar for full natural language intelligence.<br>" +
                   "2. Click the Microphone to speak instead of typing.<br>" +
                   "3. Turn on the Speaker icon to hear responses read aloud.<br>" +
                   "4. You can use standard keywords like: <em>'today', 'tomorrow', 'list', 'delete [ID]'</em> or format <em>'add Event | YYYY-MM-DD | HH:MM AM/PM'</em> as fallback.");
    });

    // TTS Toggle
    ttsToggleBtn.addEventListener("click", () => {
        isTtsEnabled = !isTtsEnabled;
        if (isTtsEnabled) {
            ttsToggleBtn.classList.add("active");
            ttsToggleBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
        } else {
            ttsToggleBtn.classList.remove("active");
            ttsToggleBtn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i>';
            // Cancel current speech if any
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
        }
    });

    // --- API & COMMUNICATION FUNCTIONS ---

    // Fetch and display all events
    async function fetchUpcomingEvents() {
        try {
            const res = await fetch("/api/events");
            const data = await res.json();
            const events = data.events || [];
            renderEvents(events);
            checkUpcomingEventNotifications(events);
        } catch (err) {
            console.error("Error fetching events:", err);
            eventsListContainer.innerHTML = '<div class="events-loading" style="color: #ef4444;">Error loading events</div>';
        }
    }

    // Render event cards in the sidebar
    function renderEvents(events) {
        if (events.length === 0) {
            eventsListContainer.innerHTML = '<div class="events-loading">No events scheduled.</div>';
            return;
        }

        eventsListContainer.innerHTML = "";
        
        events.forEach(ev => {
            const card = document.createElement("div");
            card.className = "event-card animate-fade-in";
            
            const descHtml = ev.description ? `<span class="event-card-desc">${ev.description}</span>` : "";
            
            card.innerHTML = `
                <div class="event-card-left">
                    <span class="event-card-title">${ev.title}</span>
                    <div class="event-card-datetime">
                        <span><i class="fa-regular fa-calendar"></i> ${ev.event_date}</span>
                        <span><i class="fa-regular fa-clock"></i> ${ev.event_time}</span>
                    </div>
                    ${descHtml}
                </div>
                <button class="delete-event-btn" data-id="${ev.id}" title="Delete event">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            `;
            
            // Delete action
            card.querySelector(".delete-event-btn").addEventListener("click", async (e) => {
                const eventId = e.currentTarget.getAttribute("data-id");
                if (confirm(`Are you sure you want to delete event #${eventId}?`)) {
                    await deleteEventDirect(eventId);
                }
            });

            eventsListContainer.appendChild(card);
        });
    }

    // Delete Event API call
    async function deleteEventDirect(id) {
        try {
            const res = await fetch(`/api/events/${id}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                fetchUpcomingEvents();
                addMessage("assistant", `I've deleted event #${id}.`);
            } else {
                alert("Failed to delete event.");
            }
        } catch (err) {
            console.error("Error deleting event:", err);
        }
    }

    // Submit Quick Add Form
    quickAddForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const title = document.getElementById("event-title").value;
        const date = document.getElementById("event-date").value;
        const time = document.getElementById("event-time").value;
        const desc = document.getElementById("event-desc").value;
        
        try {
            const res = await fetch("/api/events", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: title,
                    event_date: date,
                    event_time: time,
                    description: desc
                })
            });
            
            const data = await res.json();
            if (data.success) {
                quickAddForm.reset();
                fetchUpcomingEvents();
                addMessage("assistant", `Event scheduled successfully: <strong>${title}</strong> on ${date} at ${time}.`);
            } else {
                alert("Failed to schedule: " + data.error);
            }
        } catch (err) {
            console.error("Error scheduling event:", err);
        }
    });

    // Send chat message to backend
    async function sendMessage() {
        const text = chatTextarea.value.trim();
        if (!text) return;
        
        // Add User message in bubble
        addMessage("user", text);
        chatTextarea.value = "";
        chatTextarea.style.height = "auto";
        
        // Set typing indicator
        const typingBubble = showTypingIndicator();

        try {
            const api_key = localStorage.getItem("gemini_api_key") || "";
            
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    api_key: api_key
                })
            });
            
            const data = await response.json();
            
            // Remove typing bubble
            typingBubble.remove();
            
            if (data.response) {
                // Formatting response text slightly for beautiful presentation
                const formattedResponse = data.response.replace(/\n/g, "<br>");
                addMessage("assistant", formattedResponse);
                
                // Read out load if enabled
                if (isTtsEnabled) {
                    speak(data.response);
                }
                
                // Refresh list of events in the sidebar
                fetchUpcomingEvents();
            } else {
                addMessage("assistant", "I couldn't process that query correctly.");
            }
            
        } catch (err) {
            typingBubble.remove();
            console.error("Chat error:", err);
            addMessage("assistant", "Failed to connect to assistant server. Please check that Flask is running.");
        }
    }

    // Helpers to append messages
    function addMessage(sender, text) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}-message animate-fade-in`;
        
        const avatarIcon = sender === "user" ? "fa-user" : "fa-robot";
        
        const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${avatarIcon}"></i></div>
            <div class="message-content-wrapper">
                <div class="message-content">
                    <p>${text}</p>
                </div>
                <span class="timestamp">${timeNow}</span>
            </div>
        `;
        
        chatHistory.appendChild(messageDiv);
        scrollChatToBottom();
        return messageDiv;
    }

    function showTypingIndicator() {
        const messageDiv = document.createElement("div");
        messageDiv.className = "message assistant-message animate-fade-in";
        messageDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content-wrapper">
                <div class="message-content" style="padding: 12px 20px;">
                    <span style="color: var(--text-muted);"><i class="fa-solid fa-ellipsis fa-fade"></i> thinking...</span>
                </div>
            </div>
        `;
        chatHistory.appendChild(messageDiv);
        scrollChatToBottom();
        return messageDiv;
    }

    function scrollChatToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // --- VOICE CAPABILITIES (WEB SPEECH API) ---

    // 1. Text-To-Speech (TTS)
    function speak(text) {
        if (!window.speechSynthesis) return;
        
        // Cancel existing speech
        window.speechSynthesis.cancel();
        
        // Clean markdown symbols (like stars, hashes, bullet symbols) for cleaner speaking
        let cleanText = text.replace(/[*#•-]/g, "")
                            .replace(/<br>/g, ". ")
                            .replace(/<\/?[^>]+(>|$)/g, ""); // Strip HTML tags
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Use a nice voice if available
        const voices = window.speechSynthesis.getVoices();
        const englishVoice = voices.find(v => v.lang.startsWith("en-") && v.name.includes("Google")) || 
                             voices.find(v => v.lang.startsWith("en-"));
        if (englishVoice) {
            utterance.voice = englishVoice;
        }
        
        window.speechSynthesis.speak(utterance);
    }

    // 2. Speech-To-Text (STT) - Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";
        
        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add("recording");
            micBtn.innerHTML = '<i class="fa-solid fa-face-microphone"></i>';
            statusIndicator.className = "status-indicator listening";
            statusText.innerText = "Listening to you...";
        };
        
        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove("recording");
            micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
            statusIndicator.className = "status-indicator online";
            statusText.innerText = "Ready to help";
        };
        
        recognition.onerror = (e) => {
            console.error("Speech recognition error:", e.error);
            isRecording = false;
            micBtn.classList.remove("recording");
            micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
            statusIndicator.className = "status-indicator online";
            statusText.innerText = "Ready to help";
        };
        
        recognition.onresult = (e) => {
            const transcript = e.results[0][0].transcript;
            chatTextarea.value = transcript;
            // Trigger auto-send after a small delay
            setTimeout(() => {
                sendMessage();
            }, 600);
        };
        
        micBtn.addEventListener("click", () => {
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    } else {
        // Speech recognition not supported in this browser
        micBtn.style.display = "none";
        console.warn("Web Speech Recognition API is not supported in this browser.");
    }

    // --- PWA SERVICE WORKER & LOCAL NOTIFICATIONS ---

    // 1. Register Service Worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js')
                .then(reg => console.log('Service Worker registered successfully!', reg))
                .catch(err => console.error('Service Worker registration failed:', err));
        });
    }

    // 2. Request Notification Permission
    function requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                console.log('Notification permission status:', permission);
            });
        }
    }

    // Call permission request upon user interaction (first click on the main container)
    document.addEventListener('click', requestNotificationPermission, { once: true });

    // 3. Notification Checker
    function checkUpcomingEventNotifications(events) {
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            return;
        }

        const now = new Date();
        const notifiedDayBefore = JSON.parse(localStorage.getItem('notified_day_before') || '[]');
        const notified2h = JSON.parse(localStorage.getItem('notified_2h') || '[]');
        const notified15m = JSON.parse(localStorage.getItem('notified_events') || '[]');

        let updatedDayBefore = false;
        let updated2h = false;
        let updated15m = false;

        events.forEach(ev => {
            try {
                // Parse date YYYY-MM-DD
                const dateParts = ev.event_date.split('-');
                const year = parseInt(dateParts[0]);
                const month = parseInt(dateParts[1]) - 1;
                const day = parseInt(dateParts[2]);

                // Parse time HH:MM AM/PM
                const timeParts = ev.event_time.split(' ');
                const hm = timeParts[0].split(':');
                let hours = parseInt(hm[0]);
                const minutes = parseInt(hm[1]);
                const ampm = timeParts[1];

                if (ampm === 'PM' && hours < 12) hours += 12;
                if (ampm === 'AM' && hours === 12) hours = 0;

                const eventDate = new Date(year, month, day, hours, minutes, 0);

                // Check difference in milliseconds, hours, and minutes
                const diffMs = eventDate - now;
                const diffHours = diffMs / 1000 / 60 / 60;
                const diffMin = diffMs / 1000 / 60;

                const roomInfo = ev.description ? ev.description.split('|')[1] || ev.description : '';

                // Helper to send a notification
                const triggerNotification = (title, body) => {
                    const notificationOptions = {
                        body: body,
                        icon: '/static/icon.svg',
                        badge: '/static/icon.svg',
                        vibrate: [200, 100, 200]
                    };

                    if (navigator.serviceWorker.controller) {
                        navigator.serviceWorker.ready.then(reg => {
                            reg.showNotification(title, notificationOptions);
                        });
                    } else {
                        new Notification(title, notificationOptions);
                    }

                    if (isTtsEnabled) {
                        speak(body);
                    }
                };

                // INTERVAL 1: Day Before (starts in 12 to 24 hours AND not already notified)
                if (diffHours > 12 && diffHours <= 24 && !notifiedDayBefore.includes(ev.id)) {
                    triggerNotification(
                        `Imorgon: ${ev.title}`,
                        `Lektionen "${ev.title}" börjar imorgon kl. ${ev.event_time}. ${roomInfo}`
                    );
                    notifiedDayBefore.push(ev.id);
                    updatedDayBefore = true;
                }

                // INTERVAL 2: 2 Hours Before (starts in 1.75 to 2 hours AND not already notified)
                if (diffHours > 1.75 && diffHours <= 2.0 && !notified2h.includes(ev.id)) {
                    triggerNotification(
                        `Snart lektion: ${ev.title}`,
                        `Din lektion "${ev.title}" börjar om två timmar (kl. ${ev.event_time}). ${roomInfo}`
                    );
                    notified2h.push(ev.id);
                    updated2h = true;
                }

                // INTERVAL 3: 15 Minutes Before (starts in 0 to 15 minutes AND not already notified)
                if (diffMin > 0 && diffMin <= 15 && !notified15m.includes(ev.id)) {
                    triggerNotification(
                        `Lektion börjar strax: ${ev.title}`,
                        `Lektionen "${ev.title}" börjar om 15 minuter (kl. ${ev.event_time}). ${roomInfo}`
                    );
                    notified15m.push(ev.id);
                    updated15m = true;
                }
            } catch (e) {
                console.error('Error scheduling notification for event:', ev, e);
            }
        });

        // Save updated trackers back to localStorage
        if (updatedDayBefore) localStorage.setItem('notified_day_before', JSON.stringify(notifiedDayBefore));
        if (updated2h) localStorage.setItem('notified_2h', JSON.stringify(notified2h));
        if (updated15m) localStorage.setItem('notified_events', JSON.stringify(notified15m));
    }

    // 4. Set interval to poll upcoming schedule every 60 seconds
    setInterval(fetchUpcomingEvents, 60000);
});
