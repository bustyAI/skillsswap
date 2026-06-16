from app.recommender.embeddings import EMBEDDING_DIM, encode


def test_encode_returns_384_dim_list() -> None:
    result = encode("test text for embedding")

    assert isinstance(result, list)
    assert len(result) == EMBEDDING_DIM
    assert len(result) == 384
    assert all(isinstance(x, float) for x in result)


def test_encode_different_texts_produce_different_embeddings() -> None:
    result1 = encode("python programming")
    result2 = encode("cooking recipes")

    assert result1 != result2


def test_encode_empty_string_still_works() -> None:
    result = encode(" ")

    assert isinstance(result, list)
    assert len(result) == 384
