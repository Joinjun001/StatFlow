from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_default_app_renders_example_workflow():
    app_path = Path(__file__).resolve().parents[1] / 'app.py'
    app = AppTest.from_file(app_path, default_timeout=10).run()
    assert not app.exception
    assert app.title[0].value == 'StatFlow'
    assert any('연구 질문' in item.value for item in app.subheader)
    assert any('분석 실행' in item.value for item in app.subheader)


def test_default_app_exposes_research_context_inputs():
    app_path = Path(__file__).resolve().parents[1] / 'app.py'
    app = AppTest.from_file(app_path, default_timeout=10).run()
    assert not app.exception
    assert any(item.label == '연구 설계' for item in app.selectbox)
    assert any(item.label == '연구가설 (선택)' for item in app.text_area)
    assert any(item.label == '코드북 (선택)' for item in app.text_area)
