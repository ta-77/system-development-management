from flask import Blueprint, render_template, session, redirect, url_for
from models import User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
def admin_index():
    # 簡易ログインチェック（未ログインならログインページへ）
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    return render_template('admin.html', user=user)
