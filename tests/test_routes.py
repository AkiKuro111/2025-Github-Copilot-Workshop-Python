
# test_routes.py
# Flaskルートのテスト
import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'ポモドーロタイマー' in response.data.decode('utf-8')


def test_get_progress(client):
    res = client.get('/api/progress')
    assert res.status_code == 200
    data = res.get_json()
    assert 'completed' in data
    assert 'focus_time' in data

def test_post_progress(client):
    # 進捗データをPOST
    payload = {'completed': 7, 'focus_time': 123}
    res = client.post('/api/progress', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['result'] == 'ok'
    assert data['progress']['completed'] == 7
    assert data['progress']['focus_time'] == 123


def test_post_progress_invalid(client):
    # 空データ
    res = client.post('/api/progress', json={})
    assert res.status_code == 400  # 空データは400エラー
    data = res.get_json()
    assert 'error' in data

    # 不正なJSON（None）
    res2 = client.post('/api/progress', data=None)
    assert res2.status_code == 415  # Content-Type不正は415エラー
