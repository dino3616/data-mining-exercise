"""Module for crawling topics from girlschannel.net."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Self

import anyio
from playwright.async_api import BrowserContext, Locator, Playwright

GIRLS_CHANNEL_URL = "https://girlschannel.net"
MAX_CLAWL_TOPICS = 1


class Comment:
    """Class representing a comment on girlschannel.net."""

    def __init__(self, body: str, reply: list[Self] | None) -> None:
        """Initialize the Comment object."""
        self.body = body
        self.reply = reply

    def json(self) -> dict[str, Any]:
        """Return the Comment object as a JSON-serializable dictionary."""
        return {
            "body": self.body,
            "reply": [comment.json() for comment in self.reply] if self.reply is not None else None,
        }


class Topic:
    """Class representing a topic on girlschannel.net."""

    def __init__(self, title: str, url: str, comments: list[Comment]) -> None:
        """Initialize the Topic object."""
        self.title = title
        self.url = url
        self.comments = comments

    def json(self) -> dict[str, Any]:
        """Return the Topic object as a JSON-serializable dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "comments": [comment.json() for comment in self.comments],
        }


async def clawl_girls_channel(
    playwright: Playwright,
    logger: logging.Logger | None = None,
) -> list[Topic]:
    """Clawl topics from girlschannel.net."""
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()

    # async with asyncio.TaskGroup() as tg:
    #     clawl_topic_tasks = [tg.create_task(_clawl_topic(context, i + 1, logger)) for i in range(MAX_CLAWL_TOPICS)]  # noqa: E501, ERA001

    # topics = [task.result() for task in clawl_topic_tasks]  # noqa: ERA001

    # NOTE: Process in series considering machine spec.
    topics = [await _clawl_topic(context, i, logger) for i in range(MAX_CLAWL_TOPICS)]

    await context.close()
    await browser.close()

    return topics


async def dump_topics(
    output_path: Path,
    topics: list[Topic],
) -> None:
    """Dump topics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async with await anyio.open_file(output_path, mode="w") as file:
        await file.write(
            json.dumps(
                [topic.json() for topic in topics],
                indent=2,
                ensure_ascii=False,
            ),
        )


async def _clawl_topic(
    context: BrowserContext,
    topic_population: int,
    logger: logging.Logger | None = None,
) -> Topic:
    """Clawl a topic from girlschannel.net."""
    if logger is None:
        logger = logging.getLogger(__name__)

    page = await context.new_page()
    await page.goto(GIRLS_CHANNEL_URL)
    await page.locator(f"ul.topic-list > li.flc:nth-child({topic_population + 1}) > a[href^='/topics/']").click()

    topic_title = await page.locator("div.head-area > h1").inner_text()
    if topic_title.__len__() == 0:
        raise Exception("topic_title is empty")

    topic_url = page.url

    logger.info("Clawling topic: %s (%s)", topic_title, topic_url)

    topic_comments = await _clawl_comment(context, topic_url, logger)

    topic = Topic(topic_title, topic_url, topic_comments)

    await page.close()

    logger.info("Clawled topic: %s (%s)", topic_title, topic_url)

    return topic


async def _clawl_comment(
    context: BrowserContext,
    url: str,
    logger: logging.Logger | None = None,
) -> list[Comment]:
    """Clawl a comment from girlschannel.net."""
    if logger is None:
        logger = logging.getLogger(__name__)

    page = await context.new_page()
    await page.goto(url)

    logger.info("Clawling comment: %s", url)

    comments_locator = (
        await page.locator(".body-area > ul > li.comment-item > div.body").all_inner_texts()
        if "topic" in url
        else await page.locator(":not(.body-area) > ul > li.comment-item > div.body").all_inner_texts()
    )
    async with asyncio.TaskGroup() as tg:
        clawl_comments_tasks = [
            tg.create_task(_clawl_comments(context, comment, logger)) for comment in comments_locator
        ]

    comments = [task.result() for task in clawl_comments_tasks]

    await page.close()

    logger.info("Clawled comment: %s", url)

    return comments


async def _clawl_comments(
    context: BrowserContext,
    comment_locator: Locator,
    logger: logging.Logger | None = None,
) -> Comment:
    """Clawl a comment from girlschannel.net."""
    if logger is None:
        logger = logging.getLogger(__name__)

    comment_body = await comment_locator.locator("div.body").inner_text()
    if comment_body is None:
        raise Exception("comment_body is empty")

    try:
        comment_url = await comment_locator.locator("div.res-count > a[href^='/comment/']").get_attribute(
            "href",
        )
    except:  # noqa: E722
        comment_url = None

    reply_comments = (
        None if comment_url is None else await _clawl_comment(context, GIRLS_CHANNEL_URL + comment_url, logger)
    )

    return Comment(comment_body, reply_comments)
