import pytest

from src.collectors.cnn import CNNExtractor
import pathlib
import datetime


@pytest.fixture
def cnn_extractor():
    return CNNExtractor(
        base_url="https://www.cnnbrasil.com.br",
        target_path="tests/assets/cnn",
    )


@pytest.fixture
def categories_path():
    categories_path = pathlib.Path("tests/assets/cnn/categories.txt")
    categories_path.write_text("")

    yield categories_path

    if categories_path.exists():
        categories_path.unlink()


def test_get_categories_without_categories_file(cnn_extractor, categories_path):
    categories_path.unlink()
    assert not categories_path.exists()

    categories = cnn_extractor.get_categories()

    assert categories == []
    assert categories_path.exists()


def test_get_categories_with_clean_categories_file(cnn_extractor, categories_path):
    assert categories_path.exists()
    assert categories_path.read_text() == ""

    categories = cnn_extractor.get_categories()

    assert categories == []
    assert categories_path.read_text() == ""


def test_treat_datetime(cnn_extractor):
    test_string = "30/05/2023 às 08:31"
    expected = datetime.datetime(year=2023, month=5, day=30, hour=8, minute=31)

    result = cnn_extractor.treat_datetime(test_string)
    assert result == expected
