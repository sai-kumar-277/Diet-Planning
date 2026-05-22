// static/script.js

// Auto-remove toasts after 5 seconds
document.addEventListener("DOMContentLoaded", function() {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) reverse';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 5000);
    });
});

// Chatbot UI Toggles
function toggleChat() {
    const chatbox = document.getElementById('chatbox-container');
    if (chatbox.style.display === 'none') {
        chatbox.style.display = 'flex';
    } else {
        chatbox.style.display = 'none';
    }
}

function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if (!message) return;

    const chatBody = document.getElementById('chatbox-body');

    // Append User Message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg user';
    userDiv.textContent = message;
    chatBody.appendChild(userDiv);

    input.value = "";
    chatBody.scrollTop = chatBody.scrollHeight;

    // Call API
    fetch('/chat', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => {
        const botDiv = document.createElement('div');
        botDiv.className = 'chat-msg bot';
        
        // Convert \n to <br> for HTML rendering
        botDiv.innerHTML = data.reply.replace(/\n/g, '<br>');
        
        chatBody.appendChild(botDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    })
    .catch(error => {
        console.error("Error:", error);
    });
}

// Diet Goals Banner Logic
document.addEventListener("DOMContentLoaded", function() {
    const banner = document.getElementById("diet-goals-banner");
    const textSpan = document.getElementById("diet-goals-text");
    
    if (banner && textSpan) {
        // Try to load from cache memory (localStorage)
        const cachedGoals = localStorage.getItem('diet_goals');
        if (cachedGoals && cachedGoals !== "No diet goals set") {
            textSpan.textContent = cachedGoals;
            banner.style.display = "block";
        }
        
        // Fetch fresh goals from API to keep it updated
        fetch('/api/get_goals')
            .then(res => res.json())
            .then(data => {
                if (data.goals && data.goals !== "No diet goals set") {
                    textSpan.textContent = data.goals;
                    banner.style.display = "block";
                    // Store in cache memory
                    localStorage.setItem('diet_goals', data.goals);
                } else {
                    banner.style.display = "none";
                    localStorage.removeItem('diet_goals');
                }
            })
            .catch(err => console.error("Error fetching diet goals:", err));
    }
});
