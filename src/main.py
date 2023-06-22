from src.collectors.cnn import CNNExtractor
from src.schemas import settings
import pathlib


if __name__ == "__main__":
    cnn_settings = {
        "base_url": settings().CNN_BASE_URL,
        "target_path": pathlib.Path("data/cnn"),
    }

    cnn_extractor = CNNExtractor(**cnn_settings)
    cnn_extractor.get_headlines("policial", limit=-1, rate_limit_per_second=0.5)
    # cnn_extractor.get_news_articles_from_headlines(limit=-1, rate_limit_per_second=0.5)
