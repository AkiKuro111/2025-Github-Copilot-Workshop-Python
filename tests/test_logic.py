# test_logic.py
# ビジネスロジックのテスト雛形


# タイマーの残り時間表示ロジックのテスト
def format_time(seconds):
    min = str(seconds // 60).zfill(2)
    sec = str(seconds % 60).zfill(2)
    return f"{min}:{sec}"

import pytest

@pytest.mark.parametrize("seconds,expected", [
    (1500, "25:00"),
    (0, "00:00"),
    (59, "00:59"),
    (61, "01:01"),
    (600, "10:00"),
])
def test_format_time(seconds, expected):
    assert format_time(seconds) == expected
