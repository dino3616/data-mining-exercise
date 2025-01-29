import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright

from .girls_channel import clawl_girls_channel, dump_topics


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    async with async_playwright() as playwright:
        topics = await clawl_girls_channel(playwright)

    await dump_topics(Path("./data/girls_channel/topics.json"), topics)


if __name__ == "__main__":
    asyncio.run(main())
