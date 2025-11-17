from flask import Blueprint, render_template, session, redirect, url_for
import pandas as pd
import numpy as np  # np.nan を使うためにインポート
import matplotlib
matplotlib.use('Agg')  # GUI不要でmatplotlib利用
import matplotlib.pyplot as plt
import io
import base64
from models import User, Menu, Review

analysis_bp = Blueprint('analysis', __name__)

# 日本語フォント設定（環境に合わせて調整が必要な場合があります）
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
plt.rcParams['axes.unicode_minus'] = False


def plot_to_base64(fig):
    """matplotlibのfigureをbase64エンコードした画像に変換"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


@analysis_bp.route('/analysis')
def analysis_dashboard():
    """データ分析ダッシュボード"""
    # ログインチェック
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    
    # レビューデータをDataFrameに変換
    reviews = Review.query.all()
    if not reviews:
        return render_template('analysis.html', 
                             user=user,
                             charts={})
    
    review_data = []
    for r in reviews:
        review_data.append({
            'menu_id': r.menu_id,
            'menu_name': r.menu.name,
            'category': r.menu.category.name,
            'price': r.menu.price,
            'rating': r.rating,
            # 0ではなく np.nan を使い、平均計算時に無視されるようにする
            'taste_rating': r.taste_rating if r.taste_rating is not None else np.nan,
            'volume_rating': r.volume_rating if r.volume_rating is not None else np.nan,
            'price_rating': r.price_rating if r.price_rating is not None else np.nan,
            'user_id': r.user_id
        })
    
    df = pd.DataFrame(review_data)
    
    # グラフ生成
    charts = {}

    # --- グラフ1: カテゴリー別の平均評価 (棒グラフ) ---
    try:
        columns_to_average = ['rating', 'taste_rating', 'volume_rating', 'price_rating']
        # グラフ表示用に凡例を日本語にする
        rename_map = {
            'rating': '総合評価',
            'taste_rating': '味の評価',
            'volume_rating': '量の評価',
            'price_rating': 'コスパ評価'
        }
        # カテゴリでグループ化し、指定したカラムの平均を計算（np.nanは無視される）
        category_means = df.groupby('category')[columns_to_average].mean().rename(columns=rename_map)
        
        fig, ax = plt.subplots(figsize=(12, 7))
        category_means.plot(kind='bar', ax=ax)
        ax.set_title('カテゴリー別の平均評価')
        ax.set_ylabel('平均評価 (1-5)')
        ax.set_xlabel('カテゴリ')
        ax.tick_params(axis='x', rotation=0)  # X軸のラベルを横向きに
        ax.legend(title='評価項目')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        charts['category_ratings'] = plot_to_base64(fig)
    except Exception as e:
        print(f"グラフ1の生成エラー: {e}")

    # --- グラフ2: カテゴリー別の価格と評価の関係 (散布図) ---
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = df['category'].unique()
        # カテゴリごとに異なる色を自動で割り当てる
        colors = plt.cm.get_cmap('tab10', len(categories))
        
        for i, category in enumerate(categories):
            category_df = df[df['category'] == category]
            ax.scatter(category_df['price'], category_df['rating'], label=category, color=colors(i), alpha=0.7, s=50)
            
        ax.set_title('カテゴリー別の価格と総合評価の関係')
        ax.set_xlabel('価格 (円)')
        ax.set_ylabel('総合評価 (1-5)')
        ax.legend(title='カテゴリ', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, linestyle='--', alpha=0.6)
        charts['price_vs_rating'] = plot_to_base64(fig)
    except Exception as e:
        print(f"グラフ2の生成エラー: {e}")

    # --- 既存のグラフ: 人気メニューTOP10 ---
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        menu_counts = df['menu_name'].value_counts().head(10)
        # グラフの向きを人気順（上から下）にする
        menu_counts.sort_values(ascending=True).plot(kind='barh', ax=ax, color='lightgreen')
        ax.set_title('レビュー数が多いメニュー TOP10')
        ax.set_xlabel('レビュー数')
        ax.set_ylabel('メニュー名')
        charts['popular_menus'] = plot_to_base64(fig)
    except Exception as e:
        print(f"人気メニューグラフの生成エラー: {e}")
    
    return render_template('analysis.html',
                         user=user,
                         charts=charts)