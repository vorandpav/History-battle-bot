import os
from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("MISTRAL_API_KEY")
embeddings = MistralAIEmbeddings(mistral_api_key=api_key)

print("Загружаем базу...")

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "../..", "vector_db")
vectorstore = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)

# ТЕСТОВЫЕ ВОПРОСЫ
questions = [
    ("Что Сталин думал об открытии второго фронта?", "stalin"),
    ("Как Черчилль оценивал поставки по ленд-лизу?", "churchill"),
    ("Варшавское восстание", "stalin")
]

for q, persona in questions:
    print(f"\n==================================================")
    print(f"ВОПРОС: {q} (Ищем ответы от: {persona.upper()})")
    print(f"==================================================")

    # Ищем топ-3 релевантных куска с фильтром по персоне
    docs = vectorstore.similarity_search(q, k=3, filter={"persona": persona})

    for i, doc in enumerate(docs):
        print(f"\n--- Чанк {i + 1} (Источник: {doc.metadata['source']}) ---")
        print(doc.page_content)
        print("-" * 50)