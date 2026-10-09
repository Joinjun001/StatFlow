"""연구 질문과 연구 맥락을 구조화된 통계 분석 계획으로 바꾸는 fallback planner."""
import re

import pandas as pd

from .data import level_map
from .schema import (
    AnalysisMethod,
    AnalysisPlan,
    METHOD_ASSUMPTIONS,
    ResearchContext,
    ResearchDesign,
)


def _normalize(text: str) -> str:
    return re.sub(r'[\s_\-]+', '', text).lower()


def mentioned_columns(question: str, columns: list[str]) -> list[str]:
    normalized_question = _normalize(question)
    hits = []
    for col in columns:
        token = _normalize(str(col))
        if token and token in normalized_question:
            hits.append(str(col))
    return hits


def recommend_plan(
    question: str,
    frame: pd.DataFrame,
    context: ResearchContext | None = None,
) -> AnalysisPlan:
    context = context or ResearchContext()
    levels = level_map(frame)
    planning_text = question + (' ' + context.hypothesis if context.hypothesis else '')
    mentions = mentioned_columns(planning_text, [str(c) for c in frame.columns])
    numeric = [c for c, level in levels.items() if level in {'연속형', '서열형'}]
    categorical = [c for c, level in levels.items() if level == '명목형']
    mentioned_numeric = [c for c in mentions if c in numeric]
    mentioned_categorical = [c for c in mentions if c in categorical]
    q = _normalize(planning_text)

    difference_words = ('차이', '비교', '다른가', '높은가', '낮은가')
    influence_words = ('영향', '예측', '회귀', '통제', '설명', '증가할수록', '감소할수록', '증가하면', '감소하면')
    relation_words = ('상관', '관련', '관계', '연관')

    if any(word in q for word in difference_words) and (mentioned_categorical or categorical):
        group = (mentioned_categorical or categorical)[0]
        outcome_candidates = mentioned_numeric or [c for c in numeric if c != group]
        outcome = outcome_candidates[0] if outcome_candidates else None
        group_count = int(frame[group].nunique(dropna=True))
        method = AnalysisMethod.WELCH_T if group_count == 2 else AnalysisMethod.ONE_WAY_ANOVA
        reason = (
            f'질문/가설이 집단 간 차이를 묻고 있고, {group}의 유효 집단 수가 {group_count}개입니다.',
            f'{outcome or "종속변수"}의 평균 차이를 검정하는 계획입니다.',
        )
        return AnalysisPlan(method, question, outcome=outcome, group=group, rationale=reason,
                            assumptions=tuple(METHOD_ASSUMPTIONS[method]), confidence='high' if mentions else 'medium')

    if any(word in q for word in influence_words):
        candidates = mentioned_numeric or numeric
        predictor = candidates[0] if candidates else None
        outcome = candidates[1] if len(candidates) > 1 else (numeric[1] if len(numeric) > 1 else None)
        predictors = (predictor,) if predictor and predictor != outcome else ()
        reason = [
            '질문/가설이 영향·예측 관계를 묻고 있어 회귀모형을 우선 제안합니다.',
        ]
        confidence = 'high' if len(mentioned_numeric) >= 2 else 'medium'
        if context.design == ResearchDesign.EXPERIMENTAL:
            reason.append('실험 연구로 표시되었지만 무작위배정·조작·탈락 등 설계 세부사항을 확인한 뒤 인과적으로 해석해야 합니다.')
        else:
            design_name = {
                ResearchDesign.UNKNOWN: '연구 설계가 미정인 상태',
                ResearchDesign.CROSS_SECTIONAL: '횡단 연구',
                ResearchDesign.LONGITUDINAL: '종단 관찰 연구',
                ResearchDesign.REPEATED_MEASURES: '반복측정 연구',
            }.get(context.design, context.design.value)
            reason.append(f'{design_name}에서는 회귀계수를 인과효과로 확정할 수 없습니다.')
            if confidence == 'high':
                confidence = 'medium'
        return AnalysisPlan(AnalysisMethod.LINEAR_REGRESSION, question, outcome=outcome,
                            predictors=predictors, rationale=tuple(reason),
                            assumptions=tuple(METHOD_ASSUMPTIONS[AnalysisMethod.LINEAR_REGRESSION]),
                            confidence=confidence)

    if any(word in q for word in relation_words) or len(mentioned_numeric) >= 2:
        candidates = mentioned_numeric or numeric
        predictors = tuple(candidates[:2])
        reason = (
            '질문/가설이 두 수치형 변수의 관계를 묻고 있어 Pearson 상관분석을 우선 제안합니다.',
            '선형 관계와 극단치를 확인한 뒤 결과를 해석해야 합니다.',
        )
        return AnalysisPlan(AnalysisMethod.PEARSON, question, predictors=predictors, rationale=reason,
                            assumptions=tuple(METHOD_ASSUMPTIONS[AnalysisMethod.PEARSON]),
                            confidence='high' if len(mentioned_numeric) >= 2 else 'low')

    candidates = mentioned_numeric or numeric
    return AnalysisPlan(
        AnalysisMethod.PEARSON,
        question,
        predictors=tuple(candidates[:2]),
        rationale=('질문과 가설에서 통계적 의도를 명확히 확정하지 못해 탐색적 상관분석을 임시 후보로 제안합니다.',
                   '분석 방법과 변수 역할을 반드시 직접 확인하세요.'),
        assumptions=tuple(METHOD_ASSUMPTIONS[AnalysisMethod.PEARSON]),
        confidence='low',
    )
