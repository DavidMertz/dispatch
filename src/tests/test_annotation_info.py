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


def partially_annotated_args(a: int, b, c=42):
    return a + b + c


def test_partially_annotated_args():
    annotations = annotation_info(partially_annotated_args)
    assert annotations == {
        "a": AnnotationInfo(int, "True"),
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


def types_and_predicate(a: int & 3 <= a <= 17, b: float, c: int = 42):  # type: ignore
    return a + b + c


def test_types_and_predicate():
    annotations = annotation_info(types_and_predicate)
    assert annotations == {
        "a": AnnotationInfo(int, "3 <= a <= 17"),
        "b": AnnotationInfo(float, "True"),
        "c": AnnotationInfo(int, "True"),
    }


def predicate_only(a: a > 42 & a < 500, b, c=42):  # type: ignore
    return a + b + c


def test_predicate_only():
    annotations = annotation_info(predicate_only)
    assert annotations == {
        "a": AnnotationInfo(Any, "a > 42 & a < 500"),
        "b": AnnotationInfo(Any, "True"),
        "c": AnnotationInfo(Any, "True"),
    }

def non_contextual_predicates(a: 2 + 2 == 4, b: 5 < 4):  # type: ignore
    return a + b

def test_non_contextual_predicates():
    annotations = annotation_info(non_contextual_predicates)
    assert annotations == {
        "a": AnnotationInfo(Any, "True"),
        "b": AnnotationInfo(Any, "False"),
    }


def type_and_non_contextual_predicates(
    a: int & 2 + 2 == 4 & 4 < 5,  # type: ignore
    b: int | float & 5 < 4,  # type: ignore
): 
    return a + b


def test_type_and_non_contextual_predicates():
    """It is _possible_ to pre-evaluate the non-contextual predicates.

    We do not currently support this feature when a type annotation occurs.
    """
    annotations = annotation_info(type_and_non_contextual_predicates)
    assert annotations == {
        "a": AnnotationInfo(int, "2 + 2 == 4 & 4 < 5"),  # i.e. always True
        "b": AnnotationInfo(int | float, "5 < 4"),  # i.e. always False
    }
