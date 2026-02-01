// Analytics page JavaScript

// Chart objects
let deptHeartRateChart;
let deptAnomalyChart;
let heartRateHistogram;
let spo2Histogram;
let anomalyTimelineChart;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    fetchAnalyticsData();
    setInterval(fetchAnalyticsData, 30000); // Refresh every 30 seconds
});

// Fetch analytics data
function fetchAnalyticsData() {
    // Try to fetch from main host API
    fetch('http://localhost:8000/api/dashboard-data')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateAnalyticsCharts(data.data);
            } else {
                console.error('Error fetching metrics:', data.message);
                // Generate demo data if API fails
                generateDemoData();
            }
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
            // Generate demo data if API fails
            generateDemoData();
        });
}

// Generate demo data for testing
function generateDemoData() {
    const demoData = {};
    const departments = ['Cardiology', 'Emergency', 'ICU', 'Pediatrics'];
    const patients = ['Patient001', 'Patient002', 'Patient003', 'Patient004', 'Patient005'];
    
    patients.forEach((patient, index) => {
        const dept = departments[index % departments.length];
        const key = `Hospital1|${dept}|Ward${index + 1}|${patient}`;
        
        demoData[key] = {
            hospital: 'Hospital1',
            dept: dept,
            ward: `Ward${index + 1}`,
            patient: patient,
            heart_rate: 60 + Math.random() * 40,
            spo2: 95 + Math.random() * 5,
            bp_systolic: 110 + Math.random() * 30,
            bp_diastolic: 70 + Math.random() * 20,
            temperature: 36.5 + Math.random() * 2,
            anomaly_score: Math.random(),
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString()
        };
    });
    
    updateAnalyticsCharts(demoData);
}

// Update analytics charts
function updateAnalyticsCharts(data) {
    const records = Object.values(data);
    if (records.length === 0) {
        return;
    }
    
    // Process data for department averages
    const deptData = {};
    
    records.forEach(record => {
        const dept = record.dept;
        
        if (!deptData[dept]) {
            deptData[dept] = {
                heartRateSum: 0,
                anomalyScoreSum: 0,
                count: 0
            };
        }
        
        deptData[dept].heartRateSum += record.heart_rate || 0;
        deptData[dept].anomalyScoreSum += record.anomaly_score || 0;
        deptData[dept].count++;
    });
    
    // Calculate averages
    const departments = Object.keys(deptData);
    const heartRateAvgs = departments.map(dept => deptData[dept].heartRateSum / deptData[dept].count);
    const anomalyScoreAvgs = departments.map(dept => deptData[dept].anomalyScoreSum / deptData[dept].count);
    
    // Update department charts
    updateDeptHeartRateChart(departments, heartRateAvgs);
    updateDeptAnomalyChart(departments, anomalyScoreAvgs);
    
    // Process data for histograms
    const heartRates = records.map(record => record.heart_rate).filter(Boolean);
    const spo2Levels = records.map(record => record.spo2).filter(Boolean);
    
    // Update histograms
    updateHeartRateHistogram(heartRates);
    updateSpo2Histogram(spo2Levels);
    
    // Process data for anomaly timeline
    // Sort by timestamp (if available)
    records.sort((a, b) => {
        const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return timeA - timeB; // Oldest first for timeline
    });
    
    // Prepare data for anomaly timeline
    const timeLabels = records.map((record, index) => {
        return record.timestamp ? new Date(record.timestamp).toLocaleTimeString() : `Point ${index + 1}`;
    });
    
    const anomalyScores = records.map(record => record.anomaly_score);
    const patientLabels = records.map(record => `Patient ${record.patient}`);
    
    // Update anomaly timeline chart
    updateAnomalyTimelineChart(timeLabels, anomalyScores, patientLabels);
}

// Update department heart rate chart
function updateDeptHeartRateChart(departments, heartRateAvgs) {
    const ctx = document.getElementById('dept-heart-rate-chart').getContext('2d');
    
    if (deptHeartRateChart) {
        deptHeartRateChart.destroy();
    }
    
    deptHeartRateChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: departments,
            datasets: [{
                label: 'Average Heart Rate (BPM)',
                data: heartRateAvgs,
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgb(255, 99, 132)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Average Heart Rate by Department'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    suggestedMin: Math.min(...heartRateAvgs) - 5,
                    suggestedMax: Math.max(...heartRateAvgs) + 5
                }
            }
        }
    });
}

// Update department anomaly chart
function updateDeptAnomalyChart(departments, anomalyScoreAvgs) {
    const ctx = document.getElementById('dept-anomaly-chart').getContext('2d');
    
    if (deptAnomalyChart) {
        deptAnomalyChart.destroy();
    }
    
    deptAnomalyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: departments,
            datasets: [{
                label: 'Average Anomaly Score',
                data: anomalyScoreAvgs,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Average Anomaly Score by Department'
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

// Update heart rate histogram
function updateHeartRateHistogram(heartRates) {
    const ctx = document.getElementById('heart-rate-histogram').getContext('2d');
    
    if (heartRateHistogram) {
        heartRateHistogram.destroy();
    }
    
    // Create bins for the histogram
    const min = Math.min(...heartRates);
    const max = Math.max(...heartRates);
    const binSize = 5; // 5 BPM per bin
    const numBins = Math.ceil((max - min) / binSize);
    
    const bins = Array(numBins).fill(0);
    const binLabels = [];
    
    for (let i = 0; i < numBins; i++) {
        const binStart = min + (i * binSize);
        const binEnd = binStart + binSize;
        binLabels.push(`${binStart}-${binEnd}`);
    }
    
    heartRates.forEach(rate => {
        const binIndex = Math.floor((rate - min) / binSize);
        if (binIndex >= 0 && binIndex < numBins) {
            bins[binIndex]++;
        }
    });
    
    heartRateHistogram = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: binLabels,
            datasets: [{
                label: 'Frequency',
                data: bins,
                backgroundColor: 'rgba(255, 159, 64, 0.5)',
                borderColor: 'rgb(255, 159, 64)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Heart Rate Distribution'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Update SpO2 histogram
function updateSpo2Histogram(spo2Levels) {
    const ctx = document.getElementById('spo2-histogram').getContext('2d');
    
    if (spo2Histogram) {
        spo2Histogram.destroy();
    }
    
    // Create bins for the histogram
    const min = Math.min(...spo2Levels);
    const max = Math.max(...spo2Levels);
    const binSize = 1; // 1% per bin
    const numBins = Math.ceil((max - min) / binSize);
    
    const bins = Array(numBins).fill(0);
    const binLabels = [];
    
    for (let i = 0; i < numBins; i++) {
        const binStart = min + (i * binSize);
        const binEnd = binStart + binSize;
        binLabels.push(`${binStart}-${binEnd}`);
    }
    
    spo2Levels.forEach(level => {
        const binIndex = Math.floor((level - min) / binSize);
        if (binIndex >= 0 && binIndex < numBins) {
            bins[binIndex]++;
        }
    });
    
    spo2Histogram = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: binLabels,
            datasets: [{
                label: 'Frequency',
                data: bins,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgb(75, 192, 192)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'SpO2 Distribution'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Update anomaly timeline chart
function updateAnomalyTimelineChart(timeLabels, anomalyScores, patientLabels) {
    const ctx = document.getElementById('anomaly-timeline-chart').getContext('2d');
    
    if (anomalyTimelineChart) {
        anomalyTimelineChart.destroy();
    }
    
    // Generate colors for each patient
    const patientSet = new Set(patientLabels);
    const patients = Array.from(patientSet);
    
    // Group data by patient
    const patientData = {};
    
    patients.forEach(patient => {
        patientData[patient] = {
            times: [],
            scores: []
        };
    });
    
    for (let i = 0; i < timeLabels.length; i++) {
        const patient = patientLabels[i];
        patientData[patient].times.push(timeLabels[i]);
        patientData[patient].scores.push(anomalyScores[i]);
    }
    
    // Create datasets for each patient
    const datasets = patients.map((patient, index) => {
        const hue = (index * 137) % 360; // Generate distinct colors
        return {
            label: patient,
            data: patientData[patient].scores,
            borderColor: `hsl(${hue}, 70%, 60%)`,
            backgroundColor: `hsla(${hue}, 70%, 60%, 0.2)`,
            fill: false,
            tension: 0.1
        };
    });
    
    // Add threshold lines
    const warningThreshold = Array(timeLabels.length).fill(0.5);
    const criticalThreshold = Array(timeLabels.length).fill(0.7);
    
    datasets.push({
        label: 'Warning Threshold',
        data: warningThreshold,
        borderColor: 'rgba(255, 206, 86, 0.8)',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0
    });
    
    datasets.push({
        label: 'Critical Threshold',
        data: criticalThreshold,
        borderColor: 'rgba(255, 99, 132, 0.8)',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0
    });
    
    anomalyTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Anomaly Scores Over Time'
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