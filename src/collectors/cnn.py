from bs4 import BeautifulSoup
from src.schemas import Headline, News, Topic
import json
import time
import typing
import pathlib
import requests
import datetime
import sys
import glob
from src.utils import get_logger
from pydantic.json import pydantic_encoder

# CNNs site has 30 articles per page
ARTICLES_PER_PAGE: int = 30

# Default rate limit per second for requests (each page is 1 request).
DEFAULT_RATE_LIMIT: int = 1

MAX_FILE_SIZE_BYTES: int = 10 * 1024**2  # 10MB

logger = get_logger(__name__)


def treat_datetime(datetime_str: str) -> datetime.datetime:
    """Treats the CNN datetime string into a datetime object.

    Args:
        datetime_str (str): a "%d/%m/%Y às %Hh%M" formated string

    Returns:
        datetime.datetime: a Datetime formated string
    """
    datetime_str = datetime_str.replace("às", "").strip()
    return datetime.datetime.strptime(datetime_str, "%d/%m/%Y %H:%M")


class CNNExtractor:
    base_url: str
    target_path: pathlib.Path

    def __init__(
        self, base_url: str, target_path: typing.Union[pathlib.Path, str]
    ) -> None:
        self.base_url = base_url

        if isinstance(target_path, str):
            target_path = pathlib.Path(target_path)
        self.target_path = target_path

    def get_headlines(
        self,
        category: str,
        limit: int = ARTICLES_PER_PAGE,
        rate_limit_per_second: int = DEFAULT_RATE_LIMIT,
        max_file_size: int = MAX_FILE_SIZE_BYTES,
    ) -> None:
        articles_url: str = f"{self.base_url}/tudo-sobre/{category}"
        headlines: typing.Dict[str, typing.Any] = {
            "headlines": [],
            "next_page_url": None,
        }

        total_size: int = sys.getsizeof(headlines)

        try:
            while True:
                if category not in articles_url:
                    logger.error(f"Redirected to a different category: {articles_url}")
                    break

                current_headlines = self.extract_headlines_from_page(articles_url)
                headlines["headlines"].extend(current_headlines["headlines"])
                headlines["next_page_url"] = current_headlines["next_page_url"]

                total_size += sys.getsizeof(current_headlines)
                total_size += sys.getsizeof(headlines["headlines"])

                articles_url = headlines["next_page_url"]

                if headlines["next_page_url"] is None:
                    break

                if limit != -1 and len(headlines["headlines"]) >= limit:
                    break

                if total_size >= max_file_size:
                    logger.info(f"Maximum file size reached: {max_file_size} bytes")
                    self.save_headlines_in_json(category, headlines["headlines"])
                    headlines["headlines"] = []
                    total_size = sys.getsizeof(headlines)

                time.sleep(rate_limit_per_second)
                logger.info(f"Current size of headlines: {total_size / 1024**2}MB")
            self.save_headlines_in_json(category, headlines["headlines"])
        except Exception as e:
            logger.error(f"Error while fetching headlines: {e}")
            self.save_headlines_in_json(category, headlines["headlines"])
            raise

    def extract_headlines_from_page(self, url) -> typing.Dict[str, typing.Any]:
        logger.info(f"Fetching page: {url}")
        request = requests.get(url)
        soup: BeautifulSoup = BeautifulSoup(request.content, "html.parser")
        items: typing.List[str] = soup.select(".home__list__item")

        headlines: typing.List[Headline] = []

        for item in items:
            headline: Headline = Headline()
            main_tag = item.select_one(".home__list__tag")
            tag_info = item.select_one(".latest__news__infos")

            headline.title = item.select_one(".news-item-header__title").text
            logger.info(f"Fetching headline: {headline.title}")
            headline.link = main_tag.attrs["href"]
            headline.created_at = treat_datetime(
                tag_info.select_one(".home__title__date").text
            )
            headline.tag = tag_info.select_one(".latest__news__category").text
            headlines.append(headline)

        return {"headlines": headlines, "next_page_url": self.find_next_button(soup)}

    def find_next_button(self, soup: BeautifulSoup) -> str:
        page_container = soup.select_one(".latest__news__pagination")
        
        if page_container is None:
            return None

        items = page_container.find_all("li", class_="latest__news__page__item")

        # TODO: There MUST be a better way to find the next button. o_0
        for item in items:
            next_button = item.find(text="Avançar")
            if next_button is not None:
                return next_button.parent.parent.attrs["href"]

        return None

    def save_headlines_in_json(
        self, category: str, headlines: typing.List[Headline]
    ) -> None:
        timestr = time.strftime("%Y%m%d%H%M%S")

        headlines_path = self.target_path.joinpath(
            "headlines", category, f"headlines-{timestr}.json"
        )
        logger.info(f"Saving {len(headlines)} headlines to {headlines_path}")

        if not headlines_path.exists():
            headlines_path.parent.mkdir(parents=True, exist_ok=True)

        json_data = {"headlines": []}
        for headline in headlines:
            json_data["headlines"].append(headline.dict())

        with headlines_path.open("w", encoding="utf-8") as headlines_file:
            json.dump(
                json_data,
                headlines_file,
                indent=4,
                default=pydantic_encoder,
            )

    def get_news_articles_from_headlines(
        self,
        limit: int = -1,
        rate_limit_per_second: int = DEFAULT_RATE_LIMIT,
    ) -> None:
        glob_paths = str(self.target_path.joinpath("headlines", "*", "*.json"))

        articles: typing.Dict[str, typing.Any] = {
            "articles": [],
        }

        total_size = sys.getsizeof(articles)

        try:
            for path in glob.glob(glob_paths):
                logger.info(f"Reading headlines from {path}")
                with open(path, "r", encoding="utf-8") as headlines_file:
                    json_headlines = json.load(headlines_file)

                for json_headline in json_headlines["headlines"]:
                    headline = Headline(**json_headline)
                    article = self.get_news_article(headline)

                    articles["articles"].append(article.dict())

                    total_size += sys.getsizeof(article)
                    total_size += sys.getsizeof(articles["articles"])

                    if total_size >= MAX_FILE_SIZE_BYTES:
                        logger.info(
                            f"Maximum file size reached: {MAX_FILE_SIZE_BYTES} bytes"
                        )
                        self.save_headlines_in_json(articles)
                        articles["articles"] = []
                        total_size = sys.getsizeof(articles)

                    if limit != -1 and len(articles["articles"]) >= limit:
                        break

                    time.sleep(rate_limit_per_second)
                    logger.info(
                        f"Current size of news articles: {total_size / 1024**2}MB"
                    )

        except Exception as e:
            logger.error(e)
            self.save_news_in_json(articles)
            raise
        finally:
            self.save_news_in_json(articles)

    def get_news_article(self, headline: Headline) -> News:
        logger.info(f"Fetching news article: {headline.title}")
        request = requests.get(headline.link)
        soup: BeautifulSoup = BeautifulSoup(request.content, "html.parser")
        return self.extract_news_from_page(soup, headline)

    def extract_news_from_page(self, soup: BeautifulSoup, headline: Headline) -> News:
        news = News()
        news_extractor = CNNNewsExtractor(soup)

        news.headline = headline
        news.subtitle = news_extractor.extract_subtitle()

        created_at, updated_at = news_extractor.extract_dates()
        news.headline.created_at = created_at
        news.updated_at = updated_at

        news.content = news_extractor.extract_content()
        news.topics = news_extractor.extract_topics()

        return news

    def save_news_in_json(
        self, news: typing.Dict[str, typing.Any], category: str = "something-something"
    ) -> None:
        if len(news.get("articles", [])) == 0:
            return

        timestr = time.strftime("%Y%m%d%H%M%S")
        news_path = self.target_path.joinpath("news", category)

        if not news_path.exists():
            news_path.mkdir(parents=True)

        news_path = news_path.joinpath(f"news-{timestr}.json")

        logger.info(f"Saving {len(news)} news to {news_path}")

        if news_path.exists():
            news_path.unlink()

        with news_path.open("w", encoding="utf-8") as news_file:
            json.dump(
                news,
                news_file,
                indent=4,
                default=pydantic_encoder,
            )

    # def generates_topics(self) -> typing.List[str]:
    #     topics_path = self.target_path

    #     for topic in


# TODO: Create a Headlines extractor
class CNNHealinesExtractor:
    pass


class CNNNewsExtractor:
    def __init__(self, soup: BeautifulSoup) -> None:
        self.soup = soup
        self.header = None

    def get_header(self) -> BeautifulSoup:
        if self.header is None:
            self.header = self.soup.select_one(".post__header")

        return self.header

    def extract_subtitle(self) -> str:
        self.get_header()
        return self.header.select_one(".post__excerpt").text

    def extract_dates(self) -> typing.Tuple[datetime.datetime, datetime.datetime]:
        self.get_header()
        share = self.header.select_one(".higher__share")
        created_at_updated_at_text = share.select_one(".post__data").text
        created_at, updated_at = self.__extract_created_at_updated_at(
            created_at_updated_at_text
        )
        created_at = treat_datetime(created_at) if created_at is not None else None
        updated_at = treat_datetime(updated_at) if updated_at is not None else None

        return created_at, updated_at

    def extract_content(self) -> str:
        content = self.soup.select_one(".post__content")
        content = [p.text for p in content.find_all("p")]

        return " ".join(content)

    def extract_topics(self) -> typing.List[str]:
        topics_body = self.soup.select_one(".tags__topics")

        if topics_body is None:
            return []

        topics_list = topics_body.select_one(".tags__list")
        topics_li = topics_list.find_all("li")

        topics_list: typing.List[Topic] = []
        for topics in topics_li:
            topic = Topic()
            topics_a = topics.find_all("a")
            topic.topic = topics_a[0].text.strip()
            topic.link = topics_a[0].attrs["href"]

            topics_list.append(topic)

        logger.info(f"Extracted {len(topics_list)} topics")
        return topics_list

    def __extract_created_at_updated_at(
        self, created_at_updated_at: str
    ) -> typing.Tuple[str, str]:
        logger.info("Extracting created_at and updated_at")
        created_at_updated_at = created_at_updated_at.replace("Atualizado", "").strip()
        created_at_updated_at = created_at_updated_at.split("|")

        if len(created_at_updated_at) == 1:
            return created_at_updated_at[0], None

        created_at = created_at_updated_at[0].strip()
        updated_at = created_at_updated_at[1].strip()

        return created_at, updated_at
