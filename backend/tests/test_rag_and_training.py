import pytest
from app.ai.embeddings import _deterministic_hash_embedding


def test_deterministic_hash_embedding_properties():
    dim = 1536
    v1 = _deterministic_hash_embedding("machine learning capstone project", dim)
    v2 = _deterministic_hash_embedding("machine learning capstone project", dim)
    v3 = _deterministic_hash_embedding("completely different unrelated text", dim)

    assert len(v1) == dim
    assert v1 == v2  # Determinism guarantee
    assert v1 != v3  # Differentiation

    # Unit norm test
    magnitude = sum(x * x for x in v1)
    assert abs(magnitude - 1.0) < 0.001


def test_empty_string_embedding():
    dim = 1536
    v = _deterministic_hash_embedding("", dim)
    assert len(v) == dim
    magnitude = sum(x * x for x in v)
    assert abs(magnitude - 1.0) < 0.001
