# Flaskの最小構成
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)

# メモリ上で進捗データを一時保存
progress_data = {
	'completed': 4,  # 初期値はダミー
	'focus_time': 100  # 分単位（例: 100分=1時間40分）
}


@app.route('/')
def index():
	return render_template('index.html')

# 進捗データ取得
@app.route('/api/progress', methods=['GET'])
def get_progress():
	return jsonify(progress_data)

# 進捗データ保存
@app.route('/api/progress', methods=['POST'])
def post_progress():
	data = request.get_json()
	if not data:
		return jsonify({'error': 'No data'}), 400
	# 必須キーのみ更新
	for key in ['completed', 'focus_time']:
		if key in data:
			progress_data[key] = data[key]
	return jsonify({'result': 'ok', 'progress': progress_data})

if __name__ == '__main__':
	app.run(debug=True)
