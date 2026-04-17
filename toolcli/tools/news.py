"""Current news lookup tool."""

from __future__ import annotations

from pydantic import BaseModel, field_validator

from ..providers.news import (
    EmptyNewsResultError,
    MissingNewsApiKeyError,
    NewsProviderDataError,
    NewsProviderError,
    NewsRateLimitError,
    get_current_news as get_current_news_from_provider,
)
from ..schemas import ToolDefinition


class NewsArguments(BaseModel):
    """Validated arguments for the news tool."""

    topic: str | None = None

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str | None) -> str | None:
        """Normalize optional topic strings."""
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


def get_current_news(topic: str | None = None) -> dict[str, object]:
    """Return current headline data with a friendly summary."""
    try:
        headlines = get_current_news_from_provider(topic)
    except MissingNewsApiKeyError as exc:
        raise RuntimeError(str(exc)) from exc
    except EmptyNewsResultError as exc:
        raise ValueError(str(exc)) from exc
    except NewsRateLimitError as exc:
        raise RuntimeError(f"News lookup failed: {exc}") from exc
    except NewsProviderDataError as exc:
        raise RuntimeError(f"News provider returned malformed data: {exc}") from exc
    except NewsProviderError as exc:
        raise RuntimeError(f"News lookup failed: {exc}") from exc

    result_headlines = [
        {
            "title": headline.title,
            "source": headline.source,
            "url": headline.url,
            "published_at": headline.published_at,
            "description": headline.description,
        }
        for headline in headlines
    ]
    label = f"about {topic}" if topic else "from the top headlines"
    preview_titles = "; ".join(headline["title"] for headline in result_headlines[:3])
    summary = f"Here are {len(result_headlines)} headlines {label}: {preview_titles}."

    return {
        "topic": topic,
        "headlines": result_headlines,
        "count": len(result_headlines),
        "summary": summary,
    }


def get_tool_definition() -> ToolDefinition:
    """Return the news tool definition."""
    return ToolDefinition(
        name="get_current_news",
        description="Fetch recent headlines, optionally filtered by topic.",
        parameters={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Optional news topic or query string.",
                }
            },
            "required": [],
        },
        implementation=get_current_news,
        argument_model=NewsArguments,
    )
