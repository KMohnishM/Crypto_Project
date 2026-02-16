/**
 * WebSocket Real-Time Updates
 * Connects to Flask-SocketIO for real-time patient vitals
 */

// Initialize Socket.IO connection
let socket = null;
let connectionStatus = 'disconnected';

// Initialize WebSocket connection
function initWebSocket() {
    console.log('🔌 Initializing Socket.IO connection...');
    
    // Connect to Flask-SocketIO with polling transport (websocket upgrade fails in dev server)
    socket = io.connect(window.location.origin, {
        transports: ['polling'],  // Use polling only for Flask development server compatibility
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 10
    });
    
    // Connection events
    socket.on('connect', function() {
        console.log('✅ Socket.IO connected (polling transport)');
        connectionStatus = 'connected';
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', function() {
        console.log('❌ Socket.IO disconnected');
        connectionStatus = 'disconnected';
        updateConnectionStatus(false);
    });
    
    socket.on('connect_error', function(error) {
        console.error('🔴 Socket.IO connection error:', error);
        connectionStatus = 'error';
        updateConnectionStatus(false);
    });
    
    socket.on('reconnect', function(attemptNumber) {
        console.log('🔄 Socket.IO reconnected after', attemptNumber, 'attempts');
        connectionStatus = 'connected';
        updateConnectionStatus(true);
    });
    
    // Listen for vitals updates
    socket.on('vitals_update', function(data) {
        console.log('📊 Received vitals update via WebSocket');
        // Update dashboard with live data
        if (data.status === 'success' && data.data) {
            if (typeof updateDashboardWidgets === 'function') {
                updateDashboardWidgets(data.data);
            }
            if (typeof updateAnomaliesList === 'function') {
                updateAnomaliesList(data.data);
            }
            if (typeof updateHospitalHierarchy === 'function') {
                updateHospitalHierarchy(data.data);
            }
        }
    });
}

// Update connection status indicator
function updateConnectionStatus(isConnected) {
    const indicator = document.getElementById('websocket-status');
    if (indicator) {
        if (isConnected) {
            indicator.innerHTML = '<span class="badge badge-success">🔴 Live</span>';
            indicator.title = 'Real-time updates active';
        } else {
            indicator.innerHTML = '<span class="badge badge-secondary">⏸️ Offline</span>';
            indicator.title = 'Real-time updates disconnected';
        }
    }
}

// Handle vitals update event
function handleVitalsUpdate(data) {
    const { patient_id, vitals, anomaly_score, timestamp } = data;
    
    // Update patient card if visible on dashboard
    updatePatientCard(patient_id, vitals, anomaly_score, timestamp);
    
    // Show notification for high anomaly scores
    if (anomaly_score && anomaly_score > 0.7) {
        showAnomalyNotification(patient_id, anomaly_score, vitals);
    }
    
    // Trigger dashboard refresh if available
    if (typeof fetchDashboardData === 'function') {
        // Only refresh every 5 seconds max to avoid overwhelming
        if (!window.lastDashboardRefresh || (Date.now() - window.lastDashboardRefresh) > 5000) {
            fetchDashboardData();
            window.lastDashboardRefresh = Date.now();
        }
    }
    
    // Flash update indicator
    flashUpdateIndicator(patient_id);
}

// Update patient card in real-time
function updatePatientCard(patient_id, vitals, anomaly_score, timestamp) {
    const patientCard = document.querySelector(`[data-patient-id="${patient_id}"]`);
    if (!patientCard) return;
    
    // Update vitals display
    if (vitals.heart_rate) {
        const hrElement = patientCard.querySelector('.heart-rate');
        if (hrElement) hrElement.textContent = vitals.heart_rate;
    }
    
    if (vitals.spo2) {
        const spo2Element = patientCard.querySelector('.spo2');
        if (spo2Element) spo2Element.textContent = vitals.spo2;
    }
    
    if (vitals.bp_systolic && vitals.bp_diastolic) {
        const bpElement = patientCard.querySelector('.blood-pressure');
        if (bpElement) bpElement.textContent = `${vitals.bp_systolic}/${vitals.bp_diastolic}`;
    }
    
    if (vitals.temperature) {
        const tempElement = patientCard.querySelector('.temperature');
        if (tempElement) tempElement.textContent = vitals.temperature;
    }
    
    // Update anomaly score badge
    if (anomaly_score !== undefined) {
        const scoreElement = patientCard.querySelector('.anomaly-score');
        if (scoreElement) {
            scoreElement.textContent = anomaly_score.toFixed(2);
            
            // Update badge color based on score
            scoreElement.classList.remove('badge-success', 'badge-warning', 'badge-danger');
            if (anomaly_score > 0.7) {
                scoreElement.classList.add('badge-danger');
            } else if (anomaly_score > 0.5) {
                scoreElement.classList.add('badge-warning');
            } else {
                scoreElement.classList.add('badge-success');
            }
        }
    }
    
    // Update timestamp
    const timestampElement = patientCard.querySelector('.last-update');
    if (timestampElement) {
        timestampElement.textContent = `Last update: ${timestamp}`;
    }
}

// Show notification for critical anomalies
function showAnomalyNotification(patient_id, anomaly_score, vitals) {
    // Create toast notification
    const notification = document.createElement('div');
    notification.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    notification.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <strong>⚠️ Critical Alert: Patient ${patient_id}</strong>
        <p class="mb-1">Anomaly Score: ${anomaly_score.toFixed(2)}</p>
        <small>HR: ${vitals.heart_rate} | SpO2: ${vitals.spo2}%</small>
        <button type="button" class="close" data-dismiss="alert">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 10000);
    
    // Play alert sound if available
    try {
        const audio = new Audio('/static/audio/alert.mp3');
        audio.volume = 0.3;
        audio.play().catch(e => console.log('Audio play prevented:', e));
    } catch (e) {
        console.log('No alert sound available');
    }
}

// Flash visual indicator for update
function flashUpdateIndicator(patient_id) {
    const patientCard = document.querySelector(`[data-patient-id="${patient_id}"]`);
    if (!patientCard) return;
    
    // Add flash animation
    patientCard.classList.add('vitals-update-flash');
    setTimeout(() => {
        patientCard.classList.remove('vitals-update-flash');
    }, 1000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 WebSocket module loaded');
    
    // Check if Socket.IO library is available
    if (typeof io !== 'undefined') {
        initWebSocket();
    } else {
        console.error('❌ Socket.IO library not loaded. Please include socket.io.js in your HTML.');
    }
});

// Export functions for external use
window.websocketAPI = {
    getStatus: () => connectionStatus,
    reconnect: () => socket && socket.connect(),
    disconnect: () => socket && socket.disconnect()
};
