from app.similarity import cosine


def test_identical_vectors():
    assert cosine([1, 0], [1, 0]) == 1.0


def test_orthogonal_vectors():
    assert cosine([1, 0], [0, 1]) == 0.0


def test_zero_vector_is_safe():
    assert cosine([0, 0], [1, 1]) == 0.0
