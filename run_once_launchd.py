import os
from pathlib import Path
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from src.config import load_settings
from src.pipeline import run_once
from src.store import PostStore

settings = load_settings()
store = PostStore(Path("data/posted_news.db"))
run_once(settings, store)
