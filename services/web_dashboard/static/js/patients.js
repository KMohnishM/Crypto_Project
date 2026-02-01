// Patients page JavaScript

// Chart objects
let heartRateChart;
let anomalyChart;

// Current patient
let currentPatient = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    fetchPatientList();
    setInterval(fetchPatientList, 10000); // Refresh every 10 seconds
});

// Fetch patient list
function fetchPatientList() {
    fetch('/api/patients')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updatePatientList(data.patients);
                
                // If a patient is selected, refresh their data
                if (currentPatient) {
                    fetchPatientData(currentPatient);
                }
            } else {
                console.error('Error fetching patients:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching patients:', error);
        });
}

// Update patient list
function updatePatientList(patients) {
    const patientListElement = document.getElementById('patient-list');
    let patientListHtml = '';
    
    if (patients.length === 0) {
        patientListHtml = '<a href="#" class="list-group-item list-group-item-action">No patients found</a>';
    } else {
        patients.forEach(patient => {
            const activeClass = currentPatient === patient ? 'active' : '';
            patientListHtml += `
                <a href="#" class="list-group-item list-group-item-action ${activeClass}" 
                   onclick="selectPatient('${patient}')">
                    Patient ${patient}
                </a>
            `;
        });
    }
    
    patientListElement.innerHTML = patientListHtml;
}

// Select a patient
function selectPatient(patientId) {
    currentPatient = patientId;
    document.getElementById('patient-name').textContent = `Patient ${patientId}`;
    
    // Update the patient list to show the selected patient
    const patientLinks = document.querySelectorAll('#patient-list a');
    patientLinks.forEach(link => {
        link.classList.remove('active');
        if (link.textContent.trim() === `Patient ${patientId}`) {
            link.classList.add('active');
        }
    });
    
    // Fetch and display patient data
    fetchPatientData(patientId);
}

// Fetch patient data
function fetchPatientData(patientId) {
    fetch(`/api/patient/${patientId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updatePatientInfo(data.data);
                updateVitalsTable(data.data);
                updateCharts(data.data);
            } else {
                console.error('Error fetching patient data:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching patient data:', error);
        });
}

// Update patient info
function updatePatientInfo(patientData) {
    const patientInfoElement = document.getElementById('patient-info');
    
    // Get the latest record
    const records = Object.values(patientData);
    if (records.length === 0) {
        patientInfoElement.innerHTML = '<p class="text-center">No data available for this patient</p>';
        return;
    }
    
    // Sort by timestamp (if available)
    records.sort((a, b) => {
        const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return timeB - timeA; // Most recent first
    });
    
    const latestRecord = records[0];
    
    // Determine status based on anomaly score
    let statusClass = 'text-success';
    let statusText = 'Normal';
    
    if (latestRecord.anomaly_score > 0.7) {
        statusClass = 'text-danger';
        statusText = 'Critical';
    } else if (latestRecord.anomaly_score > 0.5) {
        statusClass = 'text-warning';
        statusText = 'Warning';
    }
    
    patientInfoElement.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="alert alert-info">
                    <h6>Location</h6>
                    <p>Hospital: ${latestRecord.hospital}</p>
                    <p>Department: ${latestRecord.dept}</p>
                    <p>Ward: ${latestRecord.ward}</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="alert alert-${statusClass === 'text-success' ? 'success' : statusClass === 'text-warning' ? 'warning' : 'danger'}">
                    <h6>Status</h6>
                    <h3 class="${statusClass}">${statusText}</h3>
                    <p>Anomaly Score: ${latestRecord.anomaly_score.toFixed(2)}</p>
                </div>
            </div>
        </div>
    `;
}

// Update vitals table
function updateVitalsTable(patientData) {
    const vitalsTableElement = document.getElementById('vitals-table').querySelector('tbody');
    
    // Get the latest record
    const records = Object.values(patientData);
    if (records.length === 0) {
        vitalsTableElement.innerHTML = '<tr><td colspan="4" class="text-center">No data available</td></tr>';
        return;
    }
    
    // Sort by timestamp (if available)
    records.sort((a, b) => {
        const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return timeB - timeA; // Most recent first
    });
    
    const latestRecord = records[0];
    
    // Define normal ranges for vitals
    const normalRanges = {
        'heart_rate': '60-100 bpm',
        'bp_systolic': '90-120 mmHg',
        'bp_diastolic': '60-80 mmHg',
        'respiratory_rate': '12-20 breaths/min',
        'spo2': '95-100 %',
        'temperature': '36.5-37.5 °C',
        'wbc_count': '4.5-11.0 × 10⁹/L',
        'lactate': '0.5-1.0 mmol/L',
        'blood_glucose': '70-140 mg/dL'
    };
    
    // Define status check functions
    const statusChecks = {
        'heart_rate': (val) => val < 60 || val > 100 ? 'warning' : 'normal',
        'bp_systolic': (val) => val < 90 || val > 140 ? 'warning' : 'normal',
        'bp_diastolic': (val) => val < 60 || val > 90 ? 'warning' : 'normal',
        'respiratory_rate': (val) => val < 12 || val > 25 ? 'warning' : 'normal',
        'spo2': (val) => val < 95 ? 'warning' : 'normal',
        'temperature': (val) => val < 36 || val > 38 ? 'warning' : 'normal',
        'wbc_count': (val) => val < 4.5 || val > 11 ? 'warning' : 'normal',
        'lactate': (val) => val > 2.0 ? 'warning' : 'normal',
        'blood_glucose': (val) => val < 70 || val > 180 ? 'warning' : 'normal'
    };
    
    // Display names for vitals
    const displayNames = {
        'heart_rate': 'Heart Rate',
        'bp_systolic': 'BP Systolic',
        'bp_diastolic': 'BP Diastolic',
        'respiratory_rate': 'Respiratory Rate',
        'spo2': 'SpO2',
        'etco2': 'EtCO2',
        'fio2': 'FiO2',
        'temperature': 'Temperature',
        'wbc_count': 'WBC Count',
        'lactate': 'Lactate',
        'blood_glucose': 'Blood Glucose'
    };
    
    // Build table rows
    let tableHtml = '';
    
    for (const key in displayNames) {
        if (key in latestRecord) {
            const value = latestRecord[key];
            const normalRange = normalRanges[key] || 'N/A';
            
            let status = 'normal';
            if (statusChecks[key]) {
                status = statusChecks[key](value);
            }
            
            const statusClass = status === 'normal' ? 'status-normal' : 'status-warning';
            const statusIcon = status === 'normal' ? '✓' : '⚠';
            
            tableHtml += `
                <tr>
                    <td>${displayNames[key]}</td>
                    <td>${value}</td>
                    <td>${normalRange}</td>
                    <td class="${statusClass}">${statusIcon} ${status.charAt(0).toUpperCase() + status.slice(1)}</td>
                </tr>
            `;
        }
    }
    
    vitalsTableElement.innerHTML = tableHtml;
}

// Update charts
function updateCharts(patientData) {
    const records = Object.values(patientData);
    if (records.length === 0) {
        return;
    }
    
    // Sort by timestamp (if available)
    records.sort((a, b) => {
        const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return timeA - timeB; // Oldest first for timeline
    });
    
    // Prepare data for charts
    const labels = records.map((record, index) => {
        return record.timestamp ? new Date(record.timestamp).toLocaleTimeString() : `Point ${index + 1}`;
    });
    
    const heartRateData = records.map(record => record.heart_rate);
    const anomalyScoreData = records.map(record => record.anomaly_score);
    
    // Update heart rate chart
    updateHeartRateChart(labels, heartRateData);
    
    // Update anomaly score chart
    updateAnomalyChart(labels, anomalyScoreData);
}

// Update heart rate chart
function updateHeartRateChart(labels, data) {
    const ctx = document.getElementById('heart-rate-chart').getContext('2d');
    
    if (heartRateChart) {
        heartRateChart.destroy();
    }
    
    heartRateChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Heart Rate (BPM)',
                data: data,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Heart Rate Trend'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    suggestedMin: Math.min(...data) - 10,
                    suggestedMax: Math.max(...data) + 10
                }
            }
        }
    });
}

// Update anomaly chart
function updateAnomalyChart(labels, data) {
    const ctx = document.getElementById('anomaly-chart').getContext('2d');
    
    if (anomalyChart) {
        anomalyChart.destroy();
    }
    
    // Define threshold lines
    const warningThreshold = Array(labels.length).fill(0.5);
    const criticalThreshold = Array(labels.length).fill(0.7);
    
    anomalyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Anomaly Score',
                    data: data,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Warning Threshold',
                    data: warningThreshold,
                    borderColor: 'rgba(255, 206, 86, 0.8)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Critical Threshold',
                    data: criticalThreshold,
                    borderColor: 'rgba(255, 99, 132, 0.8)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Anomaly Score Trend'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMax: 1
                }
            }
        }
    });
}