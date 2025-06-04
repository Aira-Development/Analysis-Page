from flask import Blueprint, render_template
from utils.analysis import get_dashboard_summary

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    summary = get_dashboard_summary()
    return render_template('dashboard.html', summary=summary)
