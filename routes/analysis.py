from flask import Blueprint, render_template
from utils.analysis import get_mental_health_data, get_usage_data

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis/mental-health')
def mental_health():
    data = get_mental_health_data()
    return render_template('mental_health.html', users=data)


@analysis_bp.route('/analysis/usage')
def usage():
    data = get_usage_data()
    return render_template('usage.html', users=data)