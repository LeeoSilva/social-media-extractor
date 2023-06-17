from src.collectors.cnn import CNNExtractor
from src.schemas import settings
import pathlib


if __name__ == "__main__":
    cnn_settings = {
        "base_url": settings().CNN_BASE_URL,
        "target_path": pathlib.Path("data/cnn"),
    }

    cnn_extractor = CNNExtractor(**cnn_settings)
    cnn_extractor.get_articles("policial", limit=-1, rate_limit_per_second=0.5)
