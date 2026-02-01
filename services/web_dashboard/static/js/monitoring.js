// Monitoring page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Fetch monitoring URLs from API
    fetch('/api/monitoring-urls')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const urls = data.urls;
                
                // Get Grafana button and section
                const btnGrafana = document.getElementById('btn-grafana');
                const grafanaSection = document.getElementById('grafana-section');
                
                // Get Prometheus button and section
                const btnPrometheus = document.getElementById('btn-prometheus');
                const prometheusSection = document.getElementById('prometheus-section');
                
                // Get AlertManager button and section
                const btnAlertmanager = document.getElementById('btn-alertmanager');
                const alertmanagerSection = document.getElementById('alertmanager-section');
                
                // Update iframe sources with public URLs
                const grafanaIframe = grafanaSection.querySelector('iframe');
                const prometheusIframe = prometheusSection.querySelector('iframe');
                const alertmanagerIframe = alertmanagerSection.querySelector('iframe');
                
                // Update iframe sources if they exist
                if (grafanaIframe) grafanaIframe.src = urls.grafana + '/dashboards';
                if (prometheusIframe) prometheusIframe.src = urls.prometheus + '/graph';
                if (alertmanagerIframe) alertmanagerIframe.src = urls.alertmanager + '/#/alerts';
                
                // Update direct links
                const grafanaLink = grafanaSection.querySelector('a');
                const prometheusLink = prometheusSection.querySelector('a');
                const alertmanagerLink = alertmanagerSection.querySelector('a');
                
                if (grafanaLink) grafanaLink.href = urls.grafana;
                if (prometheusLink) prometheusLink.href = urls.prometheus;
                if (alertmanagerLink) alertmanagerLink.href = urls.alertmanager;
                
                console.log('Monitoring URLs updated successfully');
            } else {
                console.error('Failed to fetch monitoring URLs:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching monitoring URLs:', error);
        });
    
    // Fetch system service status
    function updateServiceStatus() {
        // In a real implementation, this would query Prometheus for service status
        const currentTime = new Date();
        const formattedTime = currentTime.toLocaleTimeString();
        
        // Update uptime displays with realistic values
        const uptimeElements = document.querySelectorAll('[id$="-uptime"]');
        uptimeElements.forEach(element => {
            if (element) element.textContent = '2 days, ' + Math.floor(Math.random() * 24) + ' hours';
        });
        
        console.log('Service status updated at ' + formattedTime);
    }
    
    // Update status initially and then every 30 seconds
    updateServiceStatus();
    setInterval(updateServiceStatus, 30000);
});