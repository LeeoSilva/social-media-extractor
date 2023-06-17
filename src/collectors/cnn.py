from bs4 import BeautifulSoup
from src.schemas import Headline
import json
import time
import typing
import pathlib
import requests
import datetime
import sys
from src.utils import get_logger
from pydantic.json import pydantic_encoder

# CNNs site has 30 articles per page
ARTICLES_PER_PAGE: int = 30

# Default rate limit per second for requests (each page is 1 request).
DEFAULT_RATE_LIMIT: int = 1

MAX_FILE_SIZE_BYTES: int = 5 * 1024**3  # 5GB

logger = get_logger(__name__)


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

    def get_categories(self) -> typing.List[str]:
        categories_path = self.target_path.joinpath("categories.txt")

        if not categories_path.exists():
            categories_path.write_text("")

        return categories_path.read_text().splitlines()

    def get_articles(
        self,
        category: str,
        limit: int = ARTICLES_PER_PAGE,
        rate_limit_per_second: int = DEFAULT_RATE_LIMIT,
        max_file_size: int = MAX_FILE_SIZE_BYTES,
    ) -> None:
        articles_url: str = f"{self.base_url}/{category}/ultimas-noticias"
        headlines: typing.Dict[str, typing.Any] = {
            "headlines": [],
            "next_page_url": None,
        }

        total_size: int = sys.getsizeof(headlines)

        while True:
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
                self.save_headlines_in_json(headlines["headlines"])
                headlines["headlines"] = []
                total_size = sys.getsizeof(headlines)

            time.sleep(rate_limit_per_second)
            logger.info(f"Current size of headlines: {total_size / 1024**2}MB")

        self.save_headlines_in_json(headlines["headlines"])

    def extract_headlines_from_page(self, url) -> typing.Dict[str, typing.Any]:
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
            headline.created_at = self.treat_datetime(
                tag_info.select_one(".home__title__date").text
            )
            headline.tag = tag_info.select_one(".latest__news__category").text
            headlines.append(headline)

        return {"headlines": headlines, "next_page_url": self.find_next_button(soup)}

    def find_next_button(self, soup: BeautifulSoup) -> str:
        page_container = soup.select_one(".latest__news__pagination")
        items = page_container.find_all("li", class_="latest__news__page__item")

        # TODO: There MUST be a better way to find the next button. o_0
        for item in items:
            next_button = item.find(text="Avançar")
            if next_button is not None:
                return next_button.parent.parent.attrs["href"]

        return None

    def treat_datetime(self, datetime_str: str) -> datetime.datetime:
        """Treats the CNN datetime string into a datetime object.

        Args:
            datetime_str (str): a "%d/%m/%Y às %Hh%M" formated string

        Returns:
            datetime.datetime: a Datetime formated string
        """
        datetime_str = datetime_str.replace("às", "").strip()
        return datetime.datetime.strptime(datetime_str, "%d/%m/%Y %H:%M")

    def save_headlines_in_json(self, headlines: typing.List[Headline]) -> None:
        timestr = time.strftime("%Y%m%d%H%M%S")

        headlines_path = self.target_path.joinpath(f"headlines-{timestr}.json")
        logger.info(f"Saving headlines {len(headlines)} to {headlines_path}")

        if headlines_path.exists():
            headlines_path.unlink()

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
