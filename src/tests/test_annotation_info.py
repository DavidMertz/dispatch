from __future__ import annotations
from typing import Any

from dispatch.dispatch import annotation_info, AnnotationInfo

def bare_args(a, b, c):
    return a + b + c


def test_bare_args():
    annotations = annotation_info(bare_args)
    assert annotations == {
        "a": AnnotationInfo(Any, "True"),
        "b": AnnotationInfo(Any, "True"),
        "c": AnnotationInfo(Any, "True"),
    }

def bare_keywords(a, b, c=42):
    return a + b + c

def test_bare_keywords():
    annotations = annotation_info(bare_keywords)
    assert annotations == {
        "a": AnnotationInfo(Any, "True"),
        "b": AnnotationInfo(Any, "True"),
        "c": AnnotationInfo(Any, "True"),
    }

def annotated_args(a: int | float | complex, b: float, c: int = 42):
    return a + b + c

def test_annotated_args():
    annotations = annotation_info(annotated_args)
    assert annotations == {
        "a": AnnotationInfo(int | float | complex, "True"),
        "b": AnnotationInfo(float, "True"),
        "c": AnnotationInfo(int, "True"),
    }


# - int & 3 <= a <= 17      # A type annotation with a predicate
# - a > 42 & a < 500        # Bare predicate (perhaps with several bitwise operators)
# - str | bytes & 2+2==4    # Type annotation and non-contextual predicate
# - 4 > 5                   # Only a non-contextual predicate
