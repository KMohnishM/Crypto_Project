import requests
import logging
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class MainHostAPI:
    """Utility class to interact with the main host service API"""
    
    def __init__(self):
        # Get main host URL from environment or use default
        self.base_url = os.getenv('MAIN_HOST_URL', 'http://main_host:8000')
        # Fallback to localhost if running in development
        if 'localhost' in os.getenv('FLASK_ENV', '') or os.getenv('DEVELOPMENT', False):
            self.base_url = 'http://localhost:8000'
    
    def get_dashboard_data(self) -> Optional[Dict]:
        """Get all dashboard data from main host"""
        try:
            response = requests.get(f"{self.base_url}/api/dashboard-data", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch dashboard data: {e}")
            return None
    
    def get_patients(self) -> List[str]:
        """Get list of all patients from main host"""
        try:
            response = requests.get(f"{self.base_url}/api/patients", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('patients', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch patients: {e}")
            return []
    
    def get_patient_data(self, patient_id: str) -> Optional[Dict]:
        """Get data for a specific patient from main host"""
        try:
            response = requests.get(f"{self.base_url}/api/patient/{patient_id}", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch patient data for {patient_id}: {e}")
            return None

# Global instance
main_host_api = MainHostAPI()