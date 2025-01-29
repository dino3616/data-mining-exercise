import json
from pathlib import Path

from crawler.girls_channel.topic import Topic
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud


def tokenize(text: str) -> str:
    """Morhpological analysis with Janome and return tokenized text."""
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(text)

    words: list[str] = []
    for token in tokens:
        if isinstance(token, str):
            continue

        part_of_speech: str = token.part_of_speech.split(",")[0]

        if part_of_speech in ["動詞", "形容詞", "形容動詞", "名詞"]:
            if token.base_form != "*":
                words.append(token.base_form)
            else:
                words.append(token.surface)

    return " ".join(words)


def generate_wordcloud(topics: list[Topic], output_path: Path) -> None:
    """Generate wordcloud image from topics and save it."""
    text = tokenize(" ".join([" ".join(str(comment) for comment in topic.comments) for topic in topics]))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    WordCloud(
        font_path="./asset/NotoSansJP-Medium.ttf",
        width=800,
        height=400,
        background_color="white",
        stopwords=[
            "する",
            "ある",
            "こと",
            "ない",
            "それ",
            "れる",
            "それ",
            "いる",
            "なる",
            "てる",
            "やる",
            "この",
            "の",
            "ん",
        ],
    ).generate(text).to_file(output_path)


json_file = Path.open(Path("./data/girls_channel/topics.json"), "r")

topics = [Topic(topic["title"], topic["url"], topic["comments"]) for topic in json.load(json_file)]

generate_wordcloud(topics, Path("./data/girls_channel/wordcloud.png"))
