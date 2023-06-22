import pydantic
import datetime
import functools
import typing


class Headline(pydantic.BaseModel):
    title: typing.Optional[str] = None
    link: typing.Optional[str] = None
    tag: typing.Optional[str] = None
    created_at: typing.Optional[datetime.datetime] = None


class Topic(pydantic.BaseModel):
    topic: typing.Optional[str] = None
    link: typing.Optional[str] = None


class News(pydantic.BaseModel):
    headline: typing.Optional[Headline] = None
    subtitle: typing.Optional[str] = None
    updated_at: typing.Optional[datetime.datetime] = None
    content: typing.Optional[str] = None
    topics: typing.Optional[typing.List[Topic]] = None


class EnvSettings(pydantic.BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(EnvSettings):
    CNN_BASE_URL: str = pydantic.Field(env="CNN_BASE_URL")
    LOG_FILE_PATH: str = pydantic.Field(
        env="LOG_FILE_PATH", default="data/logs/data.log"
    )
    LOG_LEVEL: str = pydantic.Field(env="LOG_LEVEL", default="INFO")


@functools.lru_cache()
def settings() -> Settings:
    return Settings()
