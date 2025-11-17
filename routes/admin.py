from functools import wraps
from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from models import db, User, Menu, Review, Category

# '/admin' というプレフィックスを持つBlueprintを作成
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# --- 1. 管理者かどうかをチェックするデコレータ ---
def admin_required(f):
    """
    管理者(is_admin == True)かどうかをチェックするデコレータ
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('ログインしてください')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        
        if not user or not user.is_admin: # models.py の is_admin を参照
            flash('管理者権限がありません')
            return redirect(url_for('index.index'))
        
        return f(*args, **kwargs)
    return decorated_function


# --- 2. 管理者専用ページ (ダッシュボード) ---
@admin_bp.route('/')
@admin_required
def admin_dashboard():
    """
    /admin というURLで管理者専用ページを表示するルート
    """
    # ログイン中の管理者情報を取得
    user = User.query.get(session['user_id'])
    
    # admin.html に渡すための全データを取得
    menus = Menu.query.order_by(Menu.id.asc()).all()
    users = User.query.order_by(User.id.asc()).all()
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    categories = Category.query.all() # メニュー追加フォーム用
    
    return render_template('admin.html', 
                         user=user, 
                         menus=menus, 
                         users=users, 
                         reviews=reviews,
                         categories=categories)


# --- 3. ルートの実装 (追加・削除) ---

@admin_bp.route('/add_menu', methods=['POST'])
@admin_required
def add_menu():
    """
    /admin/add_menu (メニュー追加)
    """
    name = request.form.get('name')
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    description = request.form.get('description', '')
    
    if not name or not price or not category_id:
        flash('メニュー名、価格、カテゴリは必須です')
        return redirect(url_for('admin.admin_dashboard'))
    
    try:
        new_menu = Menu(
            name=name,
            price=int(price),
            category_id=int(category_id),
            description=description
        )
        db.session.add(new_menu)
        db.session.commit()
        flash(f'メニュー「{name}」を追加しました')
    except Exception as e:
        db.session.rollback()
        flash(f'メニューの追加に失敗しました: {e}')
        
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/delete_menu/<int:id>')
@admin_required
def delete_menu(id):
    """
    /admin/delete_menu/<id> (メニュー削除)
    """
    menu = Menu.query.get_or_404(id)
    try:
        db.session.delete(menu)
        db.session.commit()
        flash(f'メニュー「{menu.name}」を削除しました')
    except Exception as e:
        db.session.rollback()
        flash(f'メニューの削除に失敗しました: {e}')
        
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/delete_user/<int:id>')
@admin_required
def delete_user(id):
    """
    /admin/delete_user/<id> (ユーザー削除)
    """
    user = User.query.get_or_404(id)
    
    if user.id == session['user_id']:
        flash('自分自身を削除することはできません')
        return redirect(url_for('admin.admin_dashboard'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'ユーザー「{user.username}」を削除しました')
    except Exception as e:
        db.session.rollback()
        flash(f'ユーザーの削除に失敗しました: {e}')
        
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/delete_review/<int:id>')
@admin_required
def delete_review(id):
    """
    /admin/delete_review/<id> (レビュー削除)
    """
    review = Review.query.get_or_404(id)
    try:
        db.session.delete(review)
        db.session.commit()
        flash(f'ID:{review.id} のレビューを削除しました')
    except Exception as e:
        db.session.rollback()
        flash(f'レビューの削除に失敗しました: {e}')
        
    return redirect(url_for('admin.admin_dashboard'))