"""기사 본문 추출 유틸리티."""
import requests
from bs4 import BeautifulSoup
from newspaper import Article

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def extract_with_newspaper(url):
    """newspaper3k로 본문 추출."""
    article = Article(url, language="ko")
    article.download()
    article.parse()
    return {
        "title": article.title,
        "text": article.text,
        "authors": article.authors,
        "publish_date": (
            article.publish_date.isoformat() if article.publish_date else None
        ),
    }


def extract_with_bs4(url, headers=None):
    """BeautifulSoup 폴백 추출."""
    resp = requests.get(url, headers=headers or DEFAULT_HEADERS, timeout=15)
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()

    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title:
        title = og_title.get("content", "")
    elif soup.title:
        title = soup.title.string or ""

    article_tag = soup.find("article")
    if article_tag:
        text = article_tag.get_text(separator="\n", strip=True)
    else:
        paragraphs = soup.find_all("p")
        text = "\n".join(
            p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20
        )

    return {"title": title, "text": text, "authors": [], "publish_date": None}


def extract_article(url, min_length=50):
    """본문 추출 (newspaper → bs4 폴백). 실패 시 None."""
    for extractor in (extract_with_newspaper, extract_with_bs4):
        try:
            content = extractor(url)
            if len(content.get("text", "")) >= min_length:
                return content
        except Exception:
            continue
    return None
