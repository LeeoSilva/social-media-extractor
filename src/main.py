from src.collectors.cnn import CNNExtractor
from src.schemas import settings
import typing
import pathlib


if __name__ == "__main__":
    cnn_settings = {
        "base_url": settings().CNN_BASE_URL,
        "target_path": pathlib.Path("data/cnn"),
    }

    categories_to_get: typing.List[str] = [
        "policial",
        "crime",
        "tiroteio",
        "violencia",
        "ataque-a-escolas",
        "ataque",
        "ataque-aos-tres-poderes",
        "ataque-cibernetico",
        "prisao",
        "hacker",
        "hackers",
        "policia-federal-pf",
        "policia-federal",
        "fraude",
    ]

    cnn_extractor = CNNExtractor(**cnn_settings)

    # for categories in categories_to_get:
    #     cnn_extractor.get_headlines(categories, limit=-1, rate_limit_per_second=0.5)

    cnn_extractor.get_news_articles_from_headlines(limit=-1, rate_limit_per_second=0.5)
    # topics = cnn_extractor.generates_topics()
