

// タイマー制御用変数
let timer = null;
let timeLeft = 25 * 60; // 秒単位
let isRunning = false;

function updateDisplay() {
	const min = String(Math.floor(timeLeft / 60)).padStart(2, '0');
	const sec = String(timeLeft % 60).padStart(2, '0');
	document.getElementById('timer-display').textContent = `${min}:${sec}`;

	// 円形プログレスバー更新
	const circle = document.getElementById('progress-bar');
	if (circle) {
		const total = 25 * 60;
		const percent = timeLeft / total;
		const circumference = 2 * Math.PI * 90; // r=90
		circle.setAttribute('stroke-dasharray', circumference);
		circle.setAttribute('stroke-dashoffset', (circumference * (1 - percent)).toString());
	}
}

function setButtonState(running) {
	const startBtn = document.getElementById('start-btn');
	const resetBtn = document.getElementById('reset-btn');
	if (running) {
		startBtn.disabled = true;
		resetBtn.disabled = false;
	} else {
		startBtn.disabled = false;
		resetBtn.disabled = false;
	}
}

function postProgress() {
	// 完了数・集中時間をAPIにPOST（ここではダミーで+1, +25分加算）
	const completed = Number(document.getElementById('completed-count').textContent) + 1;
	const focusText = document.getElementById('focus-time').textContent;
	// 「X時間Y分」→分数に変換
	let focus_time = 0;
	const match = focusText.match(/(\d+)時間/);
	if (match) focus_time += parseInt(match[1]) * 60;
	const match2 = focusText.match(/(\d+)分/);
	if (match2) focus_time += parseInt(match2[1]);
	focus_time += 25;
	fetch('/api/progress', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ completed, focus_time })
	})
	.then(res => res.json())
	.then(data => updateProgressUI(data.progress));
}

function startTimer() {
	if (isRunning) return;
	isRunning = true;
	setButtonState(true);
	timer = setInterval(() => {
		if (timeLeft > 0) {
			timeLeft--;
			updateDisplay();
		} else {
			clearInterval(timer);
			isRunning = false;
			setButtonState(false);
			// タイマー終了時の処理
			postProgress();
		}
	}, 1000);
}

function resetTimer() {
	clearInterval(timer);
	timeLeft = 25 * 60;
	isRunning = false;
	updateDisplay();
	setButtonState(false);
}


function updateProgressUI(data) {
	// 完了数
	if (data.completed !== undefined) {
		document.getElementById('completed-count').textContent = data.completed;
	}
	// 集中時間（分→「X時間Y分」形式）
	if (data.focus_time !== undefined) {
		const min = data.focus_time;
		const h = Math.floor(min / 60);
		const m = min % 60;
		let text = '';
		if (h > 0) text += h + '時間';
		if (m > 0 || h === 0) text += m + '分';
		document.getElementById('focus-time').textContent = text;
	}
}

function fetchProgress() {
	fetch('/api/progress')
		.then(res => res.json())
		.then(data => updateProgressUI(data));
}

document.addEventListener('DOMContentLoaded', function() {
	updateDisplay();
	setButtonState(false);
	document.getElementById('start-btn').addEventListener('click', startTimer);
	document.getElementById('reset-btn').addEventListener('click', resetTimer);
	fetchProgress();
});
