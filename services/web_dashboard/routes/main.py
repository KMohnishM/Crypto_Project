from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

# Import the API utility for consistency
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api import main_host_api

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Landing page - redirects based on authentication status"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - requires authentication"""
    # Pre-fetch data to ensure consistency with patients page
    dashboard_data = main_host_api.get_dashboard_data()
    return render_template('dashboard.html', dashboard_available=dashboard_data is not None)

@main.route('/api/metrics')
@login_required
def api_metrics():
    """API endpoint to fetch real-time patient metrics from main_host"""
    try:
        dashboard_data = main_host_api.get_dashboard_data()
        if dashboard_data and dashboard_data.get('status') == 'success':
            return jsonify(dashboard_data)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch data from main host',
                'data': {}
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 500

@main.route('/monitoring')
def monitoring():
    """Page with the embedded Grafana monitoring dashboard (public)"""
    return render_template('monitoring.html')

@main.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard with charts and statistics - requires authentication"""
    return render_template('analytics.html')