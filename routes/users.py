from flask import Blueprint, render_template
from utils.user_utils import get_user_detail

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/<user_id>')
def user_profile(user_id):
    user = get_user_detail(user_id)
    return render_template('user_detail.html', user=user)