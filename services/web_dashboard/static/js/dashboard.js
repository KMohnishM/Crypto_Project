// Dashboard main JavaScript file

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    fetchDashboardData();
    setInterval(fetchDashboardData, 10000); // Refresh every 10 seconds
});

// Fetch dashboard data
function fetchDashboardData() {
    // Fetch metrics data
    fetch('/api/metrics')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateDashboardWidgets(data.data);
                updateAnomaliesList(data.data);
                updateHospitalHierarchy(data.data);
            } else {
                console.error('Error fetching metrics:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
        });
}

// Update dashboard widgets
function updateDashboardWidgets(data) {
    // Process the data
    const patientRecords = Object.values(data);
    const uniquePatients = new Set();
    let totalHeartRate = 0;
    let totalAnomalyScore = 0;
    let criticalPatients = 0;

    patientRecords.forEach(record => {
        uniquePatients.add(record.patient);
        totalHeartRate += record.heart_rate || 0;
        totalAnomalyScore += record.anomaly_score || 0;
        
        // Consider patients with anomaly score > 0.7 as critical
        if ((record.anomaly_score || 0) > 0.7) {
            criticalPatients++;
        }
    });

    // Update UI
    document.getElementById('total-patients').textContent = uniquePatients.size;
    document.getElementById('critical-patients').textContent = criticalPatients;
    
    const avgHeartRate = patientRecords.length > 0 ? (totalHeartRate / patientRecords.length).toFixed(1) : '--';
    const avgAnomalyScore = patientRecords.length > 0 ? (totalAnomalyScore / patientRecords.length).toFixed(2) : '--';
    
    document.getElementById('avg-heart-rate').textContent = avgHeartRate;
    document.getElementById('avg-anomaly-score').textContent = avgAnomalyScore;
}

// Update anomalies list
function updateAnomaliesList(data) {
    const anomaliesListElement = document.getElementById('anomalies-list');
    let anomaliesHtml = '<div class="list-group">';
    
    // Process the data to find anomalies
    const patientRecords = Object.values(data);
    
    // Sort by anomaly score, highest first
    patientRecords.sort((a, b) => (b.anomaly_score || 0) - (a.anomaly_score || 0));
    
    // Take the top 5 anomalies
    const topAnomalies = patientRecords.slice(0, 5);
    
    if (topAnomalies.length === 0) {
        anomaliesHtml += '<div class="list-group-item">No anomalies detected</div>';
    } else {
        topAnomalies.forEach(record => {
            const anomalyClass = record.anomaly_score > 0.7 ? 'list-group-item-danger' : 
                                record.anomaly_score > 0.5 ? 'list-group-item-warning' : 
                                'list-group-item-info';
            
            anomaliesHtml += `
                <div class="list-group-item ${anomalyClass}">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">Patient ${record.patient}</h6>
                        <small>Score: ${record.anomaly_score.toFixed(2)}</small>
                    </div>
                    <p class="mb-1">
                        HR: ${record.heart_rate} bpm | 
                        BP: ${record.bp_systolic}/${record.bp_diastolic} | 
                        SpO2: ${record.spo2}%
                    </p>
                    <small>Hospital: ${record.hospital} | Dept: ${record.dept} | Ward: ${record.ward}</small>
                </div>
            `;
        });
    }
    
    anomaliesHtml += '</div>';
    anomaliesListElement.innerHTML = anomaliesHtml;
}

// Update hospital hierarchy
function updateHospitalHierarchy(data) {
    const hierarchyElement = document.getElementById('hospital-hierarchy');
    
    // Process data to build the hierarchy
    const hierarchy = {};
    
    Object.values(data).forEach(record => {
        const hospital = record.hospital;
        const dept = record.dept;
        const ward = record.ward;
        const patient = record.patient;
        
        if (!hierarchy[hospital]) {
            hierarchy[hospital] = {};
        }
        
        if (!hierarchy[hospital][dept]) {
            hierarchy[hospital][dept] = {};
        }
        
        if (!hierarchy[hospital][dept][ward]) {
            hierarchy[hospital][dept][ward] = [];
        }
        
        if (!hierarchy[hospital][dept][ward].includes(patient)) {
            hierarchy[hospital][dept][ward].push(patient);
        }
    });
    
    // Build HTML
    let hierarchyHtml = '';
    
    for (const hospital in hierarchy) {
        hierarchyHtml += `
            <div class="hierarchy-node hierarchy-hospital">
                <strong>Hospital:</strong> ${hospital}
            </div>
        `;
        
        for (const dept in hierarchy[hospital]) {
            hierarchyHtml += `
                <div class="hierarchy-node hierarchy-department">
                    <strong>Department:</strong> ${dept}
                </div>
            `;
            
            for (const ward in hierarchy[hospital][dept]) {
                hierarchyHtml += `
                    <div class="hierarchy-node hierarchy-ward">
                        <strong>Ward:</strong> ${ward}
                    </div>
                `;
                
                hierarchy[hospital][dept][ward].forEach(patient => {
                    // Find patient data
                    const patientData = Object.values(data).find(record => 
                        record.hospital === hospital && 
                        record.dept === dept && 
                        record.ward === ward && 
                        record.patient === patient
                    );
                    
                    let statusClass = 'status-normal';
                    if (patientData && patientData.anomaly_score > 0.63) {
                        statusClass = 'status-critical';
                    } else if (patientData && patientData.anomaly_score > 0.53) {
                        statusClass = 'status-warning';
                    }
                    
                    hierarchyHtml += `
                        <div class="hierarchy-node hierarchy-patient ${statusClass}">
                            <strong>Patient:</strong> ${patient} 
                            <span class="float-end">
                                Score: ${patientData ? patientData.anomaly_score.toFixed(2) : 'N/A'}
                            </span>
                        </div>
                    `;
                });
            }
        }
    }
    
    if (hierarchyHtml === '') {
        hierarchyHtml = '<p class="text-center">No hierarchy data available</p>';
    }
    
    hierarchyElement.innerHTML = hierarchyHtml;
}