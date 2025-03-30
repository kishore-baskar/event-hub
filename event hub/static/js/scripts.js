document.addEventListener('DOMContentLoaded', () => {
    // Scroll Direction Detection for Home Page Only
    let lastScrollTop = 0;
    const scrollContent = document.querySelector('.scroll-content');
    if (scrollContent) {
        window.addEventListener('scroll', () => {
            let currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
            if (currentScrollTop > lastScrollTop) {
                scrollContent.classList.add('hidden');
            } else {
                scrollContent.classList.remove('hidden');
            }
            lastScrollTop = currentScrollTop <= 0 ? 0 : currentScrollTop;
        });
    }

    // Login Form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const response = await fetch('/login', { method: 'POST', body: formData });
            const result = await response.json();
            alert(result.message);
            if (result.success) window.location.reload();
        });
    }

    // Register Form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(registerForm);
            const response = await fetch('/register', { method: 'POST', body: formData });
            const result = await response.json();
            if (result.success) {
                alert(result.message);
                window.location.href = '/';
            } else {
                alert("Registration failed: " + result.message);
            }
        });
    }

    // Add Event Form
    const addEventForm = document.getElementById('add-event-form');
    if (addEventForm) {
        addEventForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(addEventForm);
            const response = await fetch('/add_event', { method: 'POST', body: formData });
            const result = await response.text();
            document.open();
            document.write(result);
            document.close();
            window.scrollTo(0, 0);
        });
    }

    // Generate AI Description
    window.generateDescription = async () => {
        const form = document.getElementById('add-event-form');
        const formData = new FormData(form);
        const response = await fetch('/generate_description', { method: 'POST', body: formData });
        const result = await response.json();
        if (result.error) {
            alert(result.error);
        } else {
            document.getElementById('description').value = result.description;
        }
    };

    // Register Event
    const registerButtons = document.querySelectorAll('.register-btn');
    registerButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const eventId = button.getAttribute('data-event-id');
            const response = await fetch(`/register_event/${eventId}`, { method: 'POST' });
            const result = await response.json();
            alert(result.message);
        });
    });

    // Chatbot Toggle
    window.toggleChatbot = () => {
        const container = document.getElementById('chatbot-container');
        container.classList.toggle('chatbot-open');
        container.classList.toggle('chatbot-closed');
        if (container.classList.contains('chatbot-open')) {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    };

    // Chat Form
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(chatForm);
            const response = await fetch('/chatbot', { method: 'POST', body: formData });
            const result = await response.text();
            document.open();
            document.write(result);
            document.close();
            const container = document.getElementById('chatbot-container');
            container.classList.add('chatbot-open');
            container.classList.remove('chatbot-closed');
            setTimeout(() => {
                document.getElementById('chatbot-toggle').addEventListener('click', window.toggleChatbot);
            }, 100);
        });
    }

    // Crowd Monitor Functions
    window.toggleStallNameInput = () => {
        const isStallOwner = document.getElementById("is-stall-owner").checked;
        document.getElementById("stall-name-section").style.display = isStallOwner ? "block" : "none";
        document.getElementById("remove-stall-btn").style.display = isStallOwner ? "block" : "none";
    };

    window.updateLocation = () => {
        const userId = document.querySelector('input[name="user_id"]').value;
        if (!userId) {
            alert("User ID is missing.");
            return;
        }
        const status = document.getElementById("location-status") || document.createElement("p");
        status.id = "location-status";
        status.textContent = "Fetching location...";
        document.querySelector(".form-section").appendChild(status);

        const isStallOwner = document.getElementById("is-stall-owner").checked;
        const stallName = document.getElementById("stall-name").value;

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    sendLocation(userId, lat, lon, isStallOwner, stallName, status);
                },
                (error) => {
                    status.textContent = "Failed to get location. Using manual input.";
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        } else {
            status.textContent = "Geolocation not supported. Using manual input.";
        }
    };

    window.sendLocation = (userId, lat, lon, isStallOwner, stallName, status) => {
        fetch('/save-location', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                latitude: lat,
                longitude: lon,
                is_stall_owner: isStallOwner,
                stall_name: isStallOwner ? stallName : ""
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                status.textContent = `Location updated: (${lat}, ${lon})`;
                if (isStallOwner && data.message === "Stall registered") {
                    document.getElementById("is-stall-owner").disabled = true;
                    document.getElementById("stall-name").disabled = true;
                }
                window.location.reload();
            } else {
                status.textContent = `Failed to save location: ${data.error}`;
            }
        })
        .catch(error => {
            status.textContent = `Network error: ${error}`;
        });
    };

    window.checkCrowdDensity = () => {
        fetch('/crowd_density')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                window.location.reload(); // Refresh to update map and crowd data
            }
        })
        .catch(error => {
            alert(`Network error: ${error}`);
        });
    };

    window.removeStall = () => {
        const userId = document.querySelector('input[name="user_id"]').value;
        if (!userId) {
            alert("User ID is missing.");
            return;
        }
        if (!document.getElementById("is-stall-owner").checked) {
            alert("You are not a stall owner.");
            return;
        }

        fetch('/remove_stall', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                document.getElementById("is-stall-owner").checked = false;
                document.getElementById("is-stall-owner").disabled = false;
                document.getElementById("stall-name").value = "";
                document.getElementById("stall-name").disabled = false;
                document.getElementById("stall-name-section").style.display = "none";
                window.location.reload();
            } else {
                alert("Failed to remove stall: " + data.error);
            }
        })
        .catch(error => {
            alert("Network error while removing stall: " + error);
        });
    };
});