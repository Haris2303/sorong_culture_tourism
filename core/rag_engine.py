"""Inisialisasi LangChain + ChromaDB + prompt template + query ke LLM Gemini (RAG Engine)."""
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

_embeddings = None
_vectorstore = None
_llm = None

FALLBACK_ANSWER = (
    "Maaf, informasi mengenai hal tersebut belum tersedia dalam basis pengetahuan "
    "budaya dan wisata Sorong Raya kami. Silakan ajukan pertanyaan lain seputar "
    "budaya Suku Moi atau destinasi wisata Kota/Kabupaten Sorong."
)

SYSTEM_PROMPT = """Anda adalah asisten virtual "Sorong Raya" yang ramah dan sopan.
Tugas Anda HANYA menjawab pertanyaan seputar budaya Suku Moi dan tempat wisata di
Kota Sorong maupun Kabupaten Sorong, murni berdasarkan KONTEKS yang diberikan di bawah ini.

ATURAN KETAT:
1. Jawab HANYA berdasarkan informasi pada KONTEKS. Jangan mengarang (berhalusinasi).
2. Jika KONTEKS tidak relevan atau tidak memuat jawaban, katakan dengan sopan bahwa
   informasi tersebut belum tersedia dalam basis pengetahuan.
3. Gunakan Bahasa Indonesia yang santun, ringkas, dan mudah dipahami wisatawan.
4. Jangan menjawab pertanyaan di luar topik budaya & wisata Sorong Raya.

KONTEKS:
{context}
"""


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from flask import current_app
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=current_app.config["GEMINI_EMBEDDING_MODEL"],
            google_api_key=current_app.config["GEMINI_API_KEY"],
        )
    return _embeddings


def get_vectorstore(fresh=False):
    """Kembalikan instance Chroma vectorstore (persisted lokal)."""
    global _vectorstore
    if fresh or _vectorstore is None:
        from flask import current_app
        _vectorstore = Chroma(
            collection_name=current_app.config["CHROMA_COLLECTION_NAME"],
            embedding_function=get_embeddings(),
            persist_directory=current_app.config["CHROMA_PERSIST_DIR"],
        )
    return _vectorstore


def get_llm():
    global _llm
    if _llm is None:
        from flask import current_app
        _llm = ChatGoogleGenerativeAI(
            model=current_app.config["GEMINI_CHAT_MODEL"],
            google_api_key=current_app.config["GEMINI_API_KEY"],
            temperature=0.3,
        )
    return _llm


def reset_engine_cache():
    """Dipanggil setelah re-sync agar vectorstore dimuat ulang dari disk."""
    global _vectorstore
    _vectorstore = None


def answer_query(question: str) -> dict:
    """Jalankan retrieval + generation. Return dict {answer, sources, grounded}."""
    from flask import current_app

    question = (question or "").strip()
    if not question:
        return {"answer": FALLBACK_ANSWER, "sources": [], "grounded": False}

    vectorstore = get_vectorstore()
    top_k = current_app.config["RAG_TOP_K"]
    threshold = current_app.config["RAG_SIMILARITY_THRESHOLD"]

    try:
        results = vectorstore.similarity_search_with_relevance_scores(question, k=top_k)
    except Exception:
        results = []

    relevant = [(doc, score) for doc, score in results if score >= threshold]

    if not relevant:
        return {"answer": FALLBACK_ANSWER, "sources": [], "grounded": False}

    context_text = "\n\n---\n\n".join(doc.page_content for doc, _ in relevant)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT.format(context=context_text)),
        ("human", "{question}"),
    ])

    chain = prompt | get_llm()
    try:
        response = chain.invoke({"question": question})
        answer_text = response.content.strip()
    except Exception:
        answer_text = FALLBACK_ANSWER

    sources = sorted({
        doc.metadata.get("source", "Dokumen tidak diketahui") for doc, _ in relevant
    })

    return {"answer": answer_text, "sources": sources, "grounded": True}
