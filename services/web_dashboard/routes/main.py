from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

# Import the API utility for consistency
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api import main_host_api

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Landing page for the application (now the only dashboard)"""
    # Pre-fetch data to ensure consistency with patients page
    dashboard_data = main_host_api.get_dashboard_data()
    return render_template('index.html', dashboard_available=dashboard_data is not None)

@main.route('/monitoring')
def monitoring():
    """Page with the embedded Grafana monitoring dashboard (public)"""
    return render_template('monitoring.html')

@main.route('/analytics')
def analytics():
    """Analytics dashboard with charts and statistics"""
    return render_template('analytics.html')