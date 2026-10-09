import pytest

from statflow.research import ResearchContextError, build_research_context, parse_codebook
from statflow.schema import ResearchDesign


def test_parse_codebook_accepts_colon_and_equals():
    result = parse_codebook(
        '학습시간: 하루 평균 시간\n스트레스점수 = 0~10 점수',
        allowed_variables={'학습시간', '스트레스점수'},
    )
    assert dict(result) == {
        '학습시간': '하루 평균 시간',
        '스트레스점수': '0~10 점수',
    }


def test_parse_codebook_rejects_unknown_or_duplicate_variables():
    with pytest.raises(ResearchContextError, match='데이터에 없습니다'):
        parse_codebook('없는변수: 설명', allowed_variables={'학습시간'})
    with pytest.raises(ResearchContextError, match='중복'):
        parse_codebook('학습시간: a\n학습시간: b', allowed_variables={'학습시간'})


def test_build_research_context_normalizes_optional_text():
    context = build_research_context(
        design=ResearchDesign.LONGITUDINAL,
        hypothesis='  시간에 따라 변화한다.  ',
        codebook_text='',
        allowed_variables={'x'},
    )
    assert context.design == ResearchDesign.LONGITUDINAL
    assert context.hypothesis == '시간에 따라 변화한다.'
    assert context.codebook == ()
