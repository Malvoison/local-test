"""News provider isolated from tool orchestration."""

from __future__ import annotations

from dataclasses import dataclass

import requests

from ..config import load_settings


DEFAULT_TIMEOUT = 10.0
DEFAULT_LIMIT = 5
NEWSAPI_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
NEWSAPI_EVERYTHING_URL = "https://newsapi.org/v2/everything"


class NewsProviderError(Exception):
    """Base error raised for news provider failures."""


class MissingNewsApiKeyError(NewsProviderError):
    """Raised when the news API key is not configured."""


class NewsRateLimitError(NewsProviderError):
    """Raised when the news provider rate limit is exceeded."""


class EmptyNewsResultError(NewsProviderError):
    """Raised when the provider returns no articles."""


class NewsProviderDataError(NewsProviderError):
    """Raised when the provider returns malformed data."""


@dataclass(frozen=True)
class NewsHeadline:
    """Normalized headline returned by the provider."""

    title: str
    source: str | None
    url: str | None
    published_at: str | None
    description: str | None


def get_current_news(topic: str | None = None, *, limit: int = DEFAULT_LIMIT, timeout: float | None = None) -> list[NewsHeadline]:
    """Fetch normalized news headlines using the configured NewsAPI key."""
    settings = load_settings()
    api_key = settings.news_api_key
    if api_key is None or not api_key.strip():
        raise MissingNewsApiKeyError("NEWS_API_KEY is not set. Add it to your environment or .env file.")

    request_timeout = timeout if timeout is not None else settings.request_timeout
    if topic:
        return _search_topic_headlines(topic=topic, api_key=api_key, limit=limit, timeout=request_timeout)
    return _fetch_top_headlines(api_key=api_key, limit=limit, timeout=request_timeout)


def _fetch_top_headlines(*, api_key: str, limit: int, timeout: float) -> list[NewsHeadline]:
    """Fetch top general headlines."""
    payload = _get_json(
        NEWSAPI_TOP_HEADLINES_URL,
        params={"country": "us", "pageSize": limit},
        api_key=api_key,
        timeout=timeout,
    )
    return _parse_articles(payload, context="top headlines")


def _search_topic_headlines(*, topic: str, api_key: str, limit: int, timeout: float) -> list[NewsHeadline]:
    """Fetch headlines for a specific topic."""
    payload = _get_json(
        NEWSAPI_EVERYTHING_URL,
        params={
            "q": topic,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit,
        },
        api_key=api_key,
        timeout=timeout,
    )
    return _parse_articles(payload, context=f"topic '{topic}'")


def _get_json(url: str, *, params: dict[str, object], api_key: str, timeout: float) -> dict[str, object]:
    """Execute an HTTP GET and return a decoded JSON object."""
    headers = {"X-Api-Key": api_key}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
    except requests.Timeout as exc:
        raise NewsProviderError("News provider timed out.") from exc
    except requests.RequestException as exc:
        raise NewsProviderError("News provider request failed.") from exc

    if response.status_code == 429:
        raise NewsRateLimitError("News provider rate limit exceeded.")
    if response.status_code >= 400:
        raise NewsProviderError("News provider returned an HTTP error.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise NewsProviderDataError("News provider returned malformed JSON.") from exc

    if not isinstance(payload, dict):
        raise NewsProviderDataError("News provider returned an unexpected response.")

    status = payload.get("status")
    if status != "ok":
        code = payload.get("code")
        message = payload.get("message")
        if code == "rateLimited":
            raise NewsRateLimitError("News provider rate limit exceeded.")
        if isinstance(message, str) and message:
            raise NewsProviderError(f"News provider error: {message}")
        raise NewsProviderError("News provider returned an unsuccessful response.")

    return payload


def _parse_articles(payload: dict[str, object], *, context: str) -> list[NewsHeadline]:
    """Normalize provider article entries."""
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise NewsProviderDataError("News provider response did not include articles.")
    if not articles:
        raise EmptyNewsResultError(f"No news articles were found for {context}.")

    normalized: list[NewsHeadline] = []
    for article in articles:
        normalized.append(_parse_article(article))
    return normalized


def _parse_article(article: object) -> NewsHeadline:
    """Normalize a single provider article."""
    if not isinstance(article, dict):
        raise NewsProviderDataError("News provider returned an invalid article entry.")

    title = article.get("title")
    source_data = article.get("source")
    url = article.get("url")
    published_at = article.get("publishedAt")
    description = article.get("description")

    if not isinstance(title, str) or not title.strip():
        raise NewsProviderDataError("News provider returned an article without a valid title.")

    source_name: str | None = None
    if isinstance(source_data, dict):
        raw_source_name = source_data.get("name")
        if isinstance(raw_source_name, str) and raw_source_name.strip():
            source_name = raw_source_name.strip()

    return NewsHeadline(
        title=title.strip(),
        source=source_name,
        url=url if isinstance(url, str) and url else None,
        published_at=published_at if isinstance(published_at, str) and published_at else None,
        description=description if isinstance(description, str) and description else None,
    )
