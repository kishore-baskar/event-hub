// Initialize the map
let map = L.map('crowd-map').setView([12.8225, 80.2250], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Backend URL
const BACKEND_URL = "http://127.0.0.1:5000";

// Toggle stall name input visibility
function toggleStallNameInput() {
    const isStallOwner = document.getElementById("is-stall-owner").checked;
    document.getElementById("stall-name-section").style.display = isStallOwner ? "block" : "none";

    // Show or hide the Remove Stall button
    const removeStallBtn = document.getElementById("remove-stall-btn");
    if (isStallOwner) {
        removeStallBtn.style.display = "inline-block";  // Show button
    } else {
        removeStallBtn.style.display = "none";  // Hide button
    }
}


// Toggle manual input visibility
function toggleManualInput() {
    const useManualInput = document.getElementById("use-manual-input").checked;
    document.getElementById("manual-input-section").style.display = useManualInput ? "block" : "none";
}


// Update location using geolocation
// Update location using geolocation (tries 3 times and returns last obtained coordinates)
function updateLocation() {
    const userId = document.getElementById("user-id").value;
    if (!userId) {
        alert("Please enter a User ID.");
        return;
    }

    const status = document.getElementById("location-status");
    status.textContent = "Fetching location...";

    const isStallOwner = document.getElementById("is-stall-owner").checked;
    const stallName = document.getElementById("stall-name").value;

    let retryCount = 0;
    const MAX_RETRIES = 3;
    let lastLat = null, lastLon = null;

    function getLocation() {
        if (!navigator.geolocation) {
            status.textContent = "Geolocation not supported by browser.";
            return;
        }

        console.log(`Attempting to fetch location (Retry ${retryCount + 1}/${MAX_RETRIES})...`);
        navigator.geolocation.getCurrentPosition(
            (position) => {
                lastLat = position.coords.latitude;
                lastLon = position.coords.longitude;
                console.log(`Location attempt ${retryCount + 1}: lat=${lastLat}, lon=${lastLon}`);

                retryCount++;
                if (retryCount < MAX_RETRIES) {
                    setTimeout(getLocation, 3000); // Wait 3 seconds before retrying
                } else {
                    console.log(`Final location used: lat=${lastLat}, lon=${lastLon}`);
                    sendLocation(userId, lastLat, lastLon, isStallOwner, stallName, status);
                }
            },
            (error) => {
                console.error(`Geolocation Error (Attempt ${retryCount + 1}): Code ${error.code} - ${error.message}`);
                retryCount++;
                if (retryCount < MAX_RETRIES) {
                    console.log(`Retrying (${retryCount}/${MAX_RETRIES})...`);
                    setTimeout(getLocation, 3000);
                } else {
                    if (lastLat !== null && lastLon !== null) {
                        console.log(`Using last known location: lat=${lastLat}, lon=${lastLon}`);
                        sendLocation(userId, lastLat, lastLon, isStallOwner, stallName, status);
                    } else {
                        status.textContent = "Failed to get location.";
                    }
                }
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }

    getLocation();
}


// Fetch fallback location using ip-api.com
function fetchFallbackLocation(userId, isStallOwner, stallName, status) {
    fetch("http://ip-api.com/json")
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                console.log(`Fallback to IP-based location successful: lat=${data.lat}, lon=${data.lon} (accuracy ~2000m)`);
                sendLocation(userId, data.lat, data.lon, isStallOwner, stallName, status);
            } else {
                status.textContent = "Failed to get any location data. Please use manual input.";
            }
        })
        .catch(error => {
            console.error("Fallback to IP-based location failed:", error);
            status.textContent = "Failed to get any location data. Please use manual input.";
        });
}

// Send location to backend
function sendLocation(userId, lat, lon, isStallOwner, stallName, status) {
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        status.textContent = "Invalid latitude or longitude values.";
        return;
    }

    fetch(`${BACKEND_URL}/save-location`, {
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
        } else {
            status.textContent = `Failed to save location: ${data.error}`;
        }
    })
    .catch(error => {
        status.textContent = `Network error: ${error}`;
    });
}

// Submit manual location
function submitManualLocation() {
    const userId = document.getElementById("user-id").value;
    if (!userId) {
        alert("Please enter a User ID.");
        return;
    }

    const lat = parseFloat(document.getElementById("manual-lat").value);
    const lon = parseFloat(document.getElementById("manual-lon").value);
    const isStallOwner = document.getElementById("is-stall-owner").checked;
    const stallName = document.getElementById("stall-name").value;
    const status = document.getElementById("location-status");

    if (isNaN(lat) || isNaN(lon)) {
        status.textContent = "Invalid latitude or longitude. Enter numeric values.";
        return;
    }

    sendLocation(userId, lat, lon, isStallOwner, stallName, status);
}

function getArrowColor(crowdDensity) {
    if (crowdDensity <= 1) return "green";  // Very low
    if (crowdDensity <= 3) return "blue";   // Low
    if (crowdDensity <= 5) return "gold";   // Medium
    if (crowdDensity <= 7) return "orange"; // High
    return "red";                           // Very High
}


function createArrowIcon(crowdDensity) {
    let color = getArrowColor(crowdDensity); // Get color from density
    let iconUrl = `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${color}.png`;

    return L.icon({
        iconUrl: iconUrl,
        iconSize: [25, 41],  // Default Leaflet icon size
        iconAnchor: [12, 41],
        popupAnchor: [1, -34]
    });
}

// Check crowd density
function checkCrowdDensity() {
    const crowdDiv = document.getElementById("crowd-density");
    crowdDiv.innerHTML = "<p>Fetching crowd density...</p>";

    fetch(`${BACKEND_URL}/crowd_density`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                crowdDiv.innerHTML = `<p>${data.error}</p>`;
                renderDefaultMap();
                return;
            }

            // Clear existing map markers
            map.eachLayer(layer => {
                if (layer instanceof L.Marker) {
                    map.removeLayer(layer);
                }
            });

            // Prepare data for Plotly chart
            let stallNames = [];
            let crowdCounts = [];
            let stallLats = [];
            let stallLons = [];

            crowdDiv.innerHTML = "<h3>Crowd Levels</h3>";
            for (const [stall, details] of Object.entries(data)) {
                if (stall === "default") continue;
                const crowdLevel = details.crowd_level.toLowerCase().replace(" ", "-");
                crowdDiv.innerHTML += `
                    <div class="crowd-level ${crowdLevel}">
                        <span class="crowd-icon">👥</span>
                        <span><strong>${stall}</strong>: ${details.crowd_level} (${details.crowd_count} people)</span>
                    </div>
                `;
                stallNames.push(stall);
                crowdCounts.push(details.crowd_count);
                stallLats.push(details.latitude);
                stallLons.push(details.longitude);

                // Add marker to map
                const color = {
                    "Very Low": "green",
                    "Low": "lightgreen",
                    "Medium": "orange",
                    "High": "red",
                    "Very High": "darkred",
                    "Unknown": "blue"
                }[details.crowd_level] || "blue";

                L.marker([details.latitude, details.longitude], {
                    icon: createArrowIcon(details.crowd_count)
                })
                .bindPopup(`${stall}: ${details.crowd_count} people (${details.crowd_level})`)
                .addTo(map);
            }

            // Center map on average stall location
            if (stallLats.length && stallLons.length) {
                const avgLat = stallLats.reduce((a, b) => a + b, 0) / stallLats.length;
                const avgLon = stallLons.reduce((a, b) => a + b, 0) / stallLons.length;
                map.setView([avgLat, avgLon], 13);
            }

            // Plotly chart
            const trace = {
                x: stallNames,
                y: crowdCounts,
                type: 'bar',
                marker: {
                    color: crowdCounts.map(count => 
                        count <= 1 ? '#2ecc71' : 
                        count <= 3 ? '#27ae60' : 
                        count <= 5 ? '#f1c40f' : 
                        count <= 7 ? '#e67e22' : '#c0392b'
                    )
                },
                text: crowdCounts,
                textposition: 'auto'
            };
            const layout = {
                title: { text: "Crowd Density by Stall", x: 0.5, xanchor: 'center' },
                xaxis: { title: "Stalls" },
                yaxis: { title: "Number of People", range: [0, Math.max(...crowdCounts) + 1 || 5] },
                plot_bgcolor: '#2c3e50',
                paper_bgcolor: '#2c3e50',
                font: { color: '#ffffff' },
                height: 450,
                width: 650,
                margin: { l: 50, r: 50, t: 80, b: 50 }
            };
            Plotly.newPlot('crowd-density', [trace], layout);
        })
        .catch(error => {
            crowdDiv.innerHTML = `<p>Network error: ${error}</p>`;
        });
}

// Render default map if no stalls
function renderDefaultMap() {
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });
    map.setView([12.8225, 80.2250], 13);
    L.marker([12.8225, 80.2250], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gray.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34]
        })
    })
    .bindPopup("Default Location (SSN College, Kalavakkam)")
    .addTo(map);
}

function removeStall() {
    const userId = document.getElementById("user-id").value;
    if (!userId) {
        alert("Please enter a User ID.");
        return;
    }

    const isStallOwner = document.getElementById("is-stall-owner").checked;
    if (!isStallOwner) {
        alert("You are not a stall owner. Only stall owners can remove their stalls.");
        return;
    }
    
    const url = `${BACKEND_URL}/remove_stall`;
    console.log("Fetching URL:", url);  // ✅ Debugging line

    fetch(url, {
        method: "POST",
        mode: "cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
    })
    
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            
            // Disable stall-related inputs after removal
            document.getElementById("is-stall-owner").checked = false;
            document.getElementById("is-stall-owner").disabled = false;
            document.getElementById("stall-name").value = "";
            document.getElementById("stall-name").disabled = false;

            // Hide stall name input section
            document.getElementById("stall-name-section").style.display = "none";

            // Refresh the crowd density display
            checkCrowdDensity();
        } else {
            alert("Failed to remove stall: " + data.error);
        }
    })
    .catch(error => {
        alert("Network error while removing stall: " + error);
    });
}