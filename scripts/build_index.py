import os
import time
import json
import requests
import trafilatura
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from mistralai.client import Mistral
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")

INDEX_SOURCES = [
    ("https://hrono.info/libris/stalin/stalin1941_1.php", "auto"),
    ("https://hrono.info/libris/stalin/stalin1942_1.php", "auto"),
    ("https://hrono.info/libris/stalin/stalin1943_1.php", "auto"),
    ("https://hrono.info/libris/stalin/stalin1944_1.php", "auto"),
    ("https://hrono.info/libris/stalin/stalin1945_1.php", "auto"),
    ("https://hrono.info/libris/stalin/vol-15.php", "stalin"),  # Тут всё Сталин
    ("https://hrono.info/biograf/bio_ch/churchill00.php", "churchill")  # Тут всё Черчилль
]

ALLOWED_DOMAINS = ["hrono.info", "www.hrono.info", "doc20vek.ru", "www.doc20vek.ru"]


class SmartHistoryCrawler:
    def __init__(self):
        self.visited = set()
        self.documents = []

        self.mistral_client = Mistral(api_key=mistral_api_key)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        if parsed.netloc not in ALLOWED_DOMAINS:
            return False

        if any(url.lower().endswith(ext) for ext in ['.jpg', '.pdf', '.zip', '.png', '.gif', '.js']):
            return False
        return True

    def process_indexes(self, index_sources):
        for index_url, rule in index_sources:
            print(f"\n=== Анализ оглавления: {index_url} (Правило: {rule.upper()}) ===")
            self.visited.add(index_url)

            try:
                resp = requests.get(index_url, timeout=10)
                soup = BeautifulSoup(resp.content, 'html.parser')

                links_to_visit = set()
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith(('#', 'mailto:', 'javascript:')):
                        continue

                    full_url = urljoin(index_url, href)
                    full_url = full_url.split('#')[0]

                    if self.is_valid_url(full_url) and full_url not in self.visited:
                        links_to_visit.add(full_url)

                print(f"Найдено {len(links_to_visit)} ссылок для извлечения текста.")

                for link in links_to_visit:
                    self.extract_and_classify(link, rule)

            except Exception as e:
                print(f"[!] Ошибка при чтении оглавления {index_url}: {e}")

    def extract_and_classify(self, url, rule):
        """Умный гибридный парсер: качает, ИИ находит границы и классифицирует текст"""
        self.visited.add(url)

        try:
            resp = requests.get(url, timeout=10)
            text = trafilatura.extract(resp.content)

            if not text or len(text) < 200:
                return

            if rule in ["stalin", "churchill"]:
                self.documents.append({
                    "url": url,
                    "persona": rule,
                    "text": text
                })
                print(f"[+] Успех (Целиком): {rule.upper()} <- {url}")
                return

            system_prompt = (
                "Ты — аналитик исторических текстов. На вход дан текст страницы, "
                "содержащий одно или несколько писем (переписку).\n"
                "Твоя задача — найти начало каждого письма и определить его автора.\n"
                "Верни JSON со списком 'documents'. Для каждого документа укажи:\n"
                "1. 'author': 'stalin', 'churchill' или 'none' (если это чужое письмо или мусор).\n"
                "2. 'start_marker': ТОЧНАЯ ЦИТАТА (первые 10-15 слов), с которых начинается письмо. "
                "Копируй символ в символ, без изменений!\n\n"
                "Пример ответа:\n"
                "{\n"
                '  "documents": [\n'
                '    {"author": "stalin", "start_marker": "ЛИЧНО И СЕКРЕТНО ОТ ПРЕМЬЕРА И. В. СТАЛИНА"}\n'
                "  ]\n"
                "}"
            )

            for attempt in range(3):
                try:
                    response = self.mistral_client.chat.complete(
                        model="mistral-small-latest",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": text[:15000]}
                        ],
                        temperature=0.0,
                        response_format={"type": "json_object"}
                    )

                    parsed_data = json.loads(response.choices[0].message.content)
                    markers = parsed_data.get("documents", [])

                    if not markers:
                        print(f"[-] Пропуск (ИИ не нашел писем Сталина/Черчилля): {url}")
                        return

                    found_docs = []
                    for doc in markers:
                        marker = doc.get("start_marker", "")
                        author = doc.get("author", "none").lower()

                        if author not in ["stalin", "churchill"] or not marker:
                            continue

                        start_idx = text.find(marker)

                        if start_idx == -1:
                            # Убираем знаки препинания из маркера LLM, разбиваем на слова
                            # Берем только первые 4-5 ключевых слов
                            clean_words = re.findall(r'\w+', marker)[:5]

                            if clean_words:
                                fuzzy_pattern = r'\s*'.join(re.escape(w) for w in clean_words)
                                match = re.search(fuzzy_pattern, text, re.IGNORECASE)

                                if match:
                                    start_idx = match.start()
                                    print(f"[~] Исправлена опечатка LLM: '{marker}' -> найдено на индексе {start_idx}")

                        if start_idx != -1:
                            found_docs.append({"author": author, "start_idx": start_idx})

                    if not found_docs:
                        print(f"[-] Пропуск (Маркеры ИИ не совпали с оригиналом): {url}")
                        return

                    found_docs.sort(key=lambda x: x["start_idx"])

                    added_count = 0
                    for i in range(len(found_docs)):
                        current_doc = found_docs[i]
                        start_idx = current_doc["start_idx"]

                        end_idx = found_docs[i + 1]["start_idx"] if i + 1 < len(found_docs) else len(text)

                        clean_content = text[start_idx:end_idx].strip()

                        if len(clean_content) > 100:
                            self.documents.append({
                                "url": f"{url}#part_{i + 1}",
                                "persona": current_doc["author"],
                                "text": clean_content
                            })
                            added_count += 1

                    print(f"[+] Успех: нарезано {added_count} оригинальных писем <- {url}")
                    return

                except Exception as e:
                    print(f"[!] Ошибка API/JSON (попытка {attempt + 1}): {e}")
                    time.sleep(2)

        except Exception as e:
            print(f"[x] Ошибка HTTP/Парсинга {url}: {e}")


def main():
    if not mistral_api_key:
        raise ValueError("Не найден MISTRAL_API_KEY! Задай переменную окружения.")

    print("Этап 1: Краулинг и извлечение текстов...")
    crawler = SmartHistoryCrawler()
    crawler.process_indexes(INDEX_SOURCES)

    if not crawler.documents:
        print("Не удалось собрать документы. Проверьте подключение к сайтам.")
        return

    print(f"\nЭтап 2: Нарезка текста (собрано {len(crawler.documents)} документов)")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    langchain_docs = []

    for doc in crawler.documents:
        chunks = splitter.split_text(doc["text"])
        for chunk in chunks:
            langchain_docs.append(Document(
                page_content=chunk,
                metadata={"persona": doc["persona"], "source": doc["url"]}
            ))

    print(f"Всего получилось {len(langchain_docs)} текстовых фрагментов (чанков).")

    print("\nЭтап 3: Генерация эмбеддингов Mistral и сохранение в FAISS...")
    embeddings = MistralAIEmbeddings(mistral_api_key=mistral_api_key)
    vectorstore = FAISS.from_documents(langchain_docs, embeddings)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "vector_db")
    vectorstore.save_local(db_path)

    print("Готово. База vector_db успешно создана. Теперь бот стал исторически точным!")


if __name__ == "__main__":
    main()