from flask import Blueprint, render_template
from utils.feedback_utils import get_feedback_summary, get_user_feedback

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback/summary')
def feedback_summary():
    summary = get_feedback_summary()
    return render_template('feedback_summary.html', summary=summary)


@feedback_bp.route('/feedback/user/<user_id>')
def feedback_user(user_id):
    feedback = get_user_feedback(user_id)
    return render_template('feedback_user.html', feedback=feedback)
