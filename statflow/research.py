"""연구 설계·가설·코드북 입력을 안전한 ResearchContext로 정규화한다."""
from __future__ import annotations

import re

from .schema import ResearchContext, ResearchDesign


class ResearchContextError(ValueError):
    pass


def parse_codebook(text: str, *, allowed_variables: set[str]) -> tuple[tuple[str, str], ...]:
    """`변수명: 설명` 또는 `변수명 = 설명` 형식의 코드북을 검증한다."""
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = re.split(r'\s*[:=]\s*', line, maxsplit=1)
        if len(parts) != 2:
            raise ResearchContextError(f'코드북 {line_number}행은 `변수명: 설명` 형식이어야 합니다.')
        variable, description = (part.strip() for part in parts)
        if variable not in allowed_variables:
            raise ResearchContextError(f'코드북 {line_number}행의 변수 `{variable}`가 데이터에 없습니다.')
        if variable in seen:
            raise ResearchContextError(f'코드북에 `{variable}`가 중복되었습니다.')
        if not description:
            raise ResearchContextError(f'코드북 {line_number}행의 설명이 비어 있습니다.')
        if len(description) > 500:
            raise ResearchContextError(f'코드북 `{variable}` 설명은 500자 이하여야 합니다.')
        seen.add(variable)
        entries.append((variable, description))
        if len(entries) > 100:
            raise ResearchContextError('코드북은 최대 100개 변수까지 입력할 수 있습니다.')

    return tuple(entries)


def build_research_context(
    *,
    design: ResearchDesign,
    hypothesis: str = '',
    codebook_text: str = '',
    allowed_variables: set[str],
) -> ResearchContext:
    hypothesis = hypothesis.strip()
    if len(hypothesis) > 2000:
        raise ResearchContextError('연구가설은 2000자 이하여야 합니다.')
    return ResearchContext(
        design=design,
        hypothesis=hypothesis or None,
        codebook=parse_codebook(codebook_text, allowed_variables=allowed_variables),
    )
