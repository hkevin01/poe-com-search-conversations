#!/usr/bin/env python3
import math
import re
import sqlite3
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Try to import ML dependencies, but gracefully handle if they're not available
try:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import (CountVectorizer,
                                                 TfidfVectorizer)
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print(
        "Warning: scikit-learn not available. "
        "Advanced search algorithms disabled."
    )
    # Create dummy classes to prevent import errors

    class TfidfVectorizer:
        def __init__(self, *args, **kwargs):
            pass

    class CountVectorizer:
        def __init__(self, *args, **kwargs):
            pass

FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
  content,                      -- full message text
  title,                        -- message title if any
  author,                       -- author username or bot
  role,                         -- user/assistant/system
  conversation_slug,            -- convenience field for joining
  content='messages',           -- contentless table linked to messages
  content_rowid='rowid',
  tokenize='unicode61'
);
"""

TRIGGERS = [
# Insert
"""
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content, title, author, role, conversation_slug)
  VALUES (
    new.rowid,
    coalesce(new.excerpt, ''),            -- or full text if available
    coalesce(new.title, ''),
    coalesce(new.author, ''),
    coalesce(new.role, ''),
    coalesce(new.slug, '')
  );
END;
""",
# Delete
"""
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content, title, author, role, conversation_slug)
  VALUES('delete', old.rowid, '', '', '', '', '');
END;
""",
# Update
"""
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content, title, author, role, conversation_slug)
  VALUES('delete', old.rowid, '', '', '', '', '');
  INSERT INTO messages_fts(rowid, content, title, author, role, conversation_slug)
  VALUES (
    new.rowid,
    coalesce(new.excerpt, ''),
    coalesce(new.title, ''),
    coalesce(new.author, ''),
    coalesce(new.role, ''),
    coalesce(new.slug, '')
  );
END;
"""
]

def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable FTS if available
    conn.execute("PRAGMA case_sensitive_like=OFF;")
    return conn

def ensure_fts(conn: sqlite3.Connection) -> None:
    conn.executescript(FTS_DDL)
    for trg in TRIGGERS:
        conn.executescript(trg)
    # If table is empty but messages has content, rebuild
    cnt = conn.execute("SELECT count(*) FROM messages_fts").fetchone()[0]
    if cnt == 0:
        # Populate from existing messages
        conn.execute("INSERT INTO messages_fts(rowid, content, title, author, role, conversation_slug) "
                     "SELECT rowid, coalesce(excerpt,''), coalesce(title,''), coalesce(author,''), coalesce(role,''), coalesce(slug,'') "
                     "FROM messages;")
    conn.commit()

def build_where(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
    where: List[str] = []
    params: List[Any] = []
    if filters.get("bot"):
        where.append("c.title LIKE ?")
        params.append(f"%{filters['bot']}%")
    if filters.get("start"):
        where.append("datetime(m.updated_at) >= datetime(?)")
        params.append(filters["start"])
    if filters.get("end"):
        where.append("datetime(m.updated_at) <= datetime(?)")
        params.append(filters["end"])
    return (" AND ".join(where), params)

def search_messages(
    db_path: str,
    query: str,
    bot: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    conn = connect(db_path)
    try:
        # Ensure FTS exists
        try:
            ensure_fts(conn)
            use_fts = True
        except sqlite3.DatabaseError:
            use_fts = False

        filters = {"bot": bot, "start": start, "end": end}
        where_extra, params_extra = build_where(filters)

        if use_fts and query.strip():
            sql = f"""
            SELECT
              m.*, c.title AS conversation_title, c.url AS conversation_url
            FROM messages m
            JOIN conversations c ON c.graph_id = m.conversation_graph_id
            JOIN messages_fts f ON f.rowid = m.rowid
            WHERE f MATCH ?
            {"AND " + where_extra if where_extra else ""}
            ORDER BY m.updated_at DESC
            LIMIT ? OFFSET ?;
            """
            params = [query] + params_extra + [limit, offset]
        else:
            # Fallback: LIKE search across a few columns
            like = f"%{query.strip()}%" if query.strip() else "%"
            sql = f"""
            SELECT
              m.*, c.title AS conversation_title, c.url AS conversation_url
            FROM messages m
            JOIN conversations c ON c.graph_id = m.conversation_graph_id
            WHERE (coalesce(m.excerpt,'') LIKE ? OR coalesce(m.title,'') LIKE ?)
            {"AND " + where_extra if where_extra else ""}
            ORDER BY m.updated_at DESC
            LIMIT ? OFFSET ?;
            """
            params = [like, like] + params_extra + [limit, offset]

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def search_conversations_fallback(
    db_path: str,
    query: str,
    bot: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Fallback for legacy conversations table search"""
    conn = connect(db_path)
    try:
        where_parts = []
        params = []

        if query.strip():
            where_parts.append("(title LIKE ? OR content LIKE ?)")
            like_query = f"%{query.strip()}%"
            params.extend([like_query, like_query])

        if bot:
            where_parts.append("bot_name LIKE ?")
            params.append(f"%{bot}%")

        if start:
            where_parts.append("datetime(created_at) >= datetime(?)")
            params.append(start)

        if end:
            where_parts.append("datetime(created_at) <= datetime(?)")
            params.append(end)

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        sql = f"""
        SELECT * FROM conversations
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ================================
# ADVANCED SEARCH ALGORITHMS
# ================================

def preprocess_text(text: str) -> str:
    """Clean and normalize text for search algorithms."""
    if not text:
        return ""
    # Convert to lowercase and remove extra whitespace
    text = re.sub(r'\s+', ' ', text.lower().strip())
    # Remove non-alphanumeric characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    return text


def calculate_tf_idf(
    documents: List[str], query: str
) -> List[Tuple[int, float]]:
    """
    Calculate TF-IDF scores for documents against a query.
    Returns list of (doc_index, score) tuples sorted by relevance.
    """
    if not SKLEARN_AVAILABLE:
        print("TF-IDF requires scikit-learn. Falling back to basic search.")
        return []

    if not documents or not query:
        return []

    try:
        # Preprocess documents and query
        processed_docs = [preprocess_text(doc) for doc in documents]
        processed_query = preprocess_text(query)

        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )

        # Fit and transform documents
        tfidf_matrix = vectorizer.fit_transform(processed_docs)

        # Transform query
        query_vector = vectorizer.transform([processed_query])

        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

        # Return sorted results
        results = [
            (i, score) for i, score in enumerate(similarities) if score > 0
        ]
        return sorted(results, key=lambda x: x[1], reverse=True)

    except Exception as e:
        print(f"TF-IDF calculation error: {e}")
        return []

def calculate_bm25(
    documents: List[str],
    query: str,
    k1: float = 1.5,
    b: float = 0.75
) -> List[Tuple[int, float]]:
    """
    Calculate BM25 scores for documents against a query.
    BM25 is a ranking function used by search engines.
    """
    if not documents or not query:
        return []

    try:
        # Preprocess documents and query
        processed_docs = [preprocess_text(doc).split() for doc in documents]
        query_terms = preprocess_text(query).split()

        # Calculate document frequencies
        doc_freq: Dict[str, int] = defaultdict(int)
        for doc in processed_docs:
            unique_terms = set(doc)
            for term in unique_terms:
                doc_freq[term] += 1

        # Calculate average document length
        avg_doc_len = (
            sum(len(doc) for doc in processed_docs) / len(processed_docs)
        )

        # Calculate BM25 scores
        scores = []
        for i, doc in enumerate(processed_docs):
            score = 0.0
            doc_len = len(doc)
            term_freq = Counter(doc)

            for term in query_terms:
                if term in term_freq:
                    tf = term_freq[term]
                    df = doc_freq[term]
                    idf = math.log(
                        (len(processed_docs) - df + 0.5) / (df + 0.5)
                    )

                    # BM25 formula
                    score += (
                        idf * (tf * (k1 + 1)) /
                        (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
                    )

            if score > 0:
                scores.append((i, score))

        return sorted(scores, key=lambda x: x[1], reverse=True)

    except Exception as e:
        print(f"BM25 calculation error: {e}")
        return []


def calculate_cosine_similarity_search(
    documents: List[str], query: str
) -> List[Tuple[int, float]]:
    """
    Calculate cosine similarity between query and documents using TF-IDF
    vectors.
    """
    if not SKLEARN_AVAILABLE:
        print("Cosine similarity requires scikit-learn. Falling back to BM25.")
        return calculate_bm25(documents, query)

    if not documents or not query:
        return []

    try:
        # Combine documents and query for consistent vocabulary
        all_texts = documents + [query]
        processed_texts = [preprocess_text(text) for text in all_texts]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(processed_texts)

        # Query vector is the last one
        query_vector = tfidf_matrix[-1]
        doc_vectors = tfidf_matrix[:-1]

        # Calculate cosine similarities
        similarities = cosine_similarity(query_vector, doc_vectors).flatten()

        # Return sorted results
        results = [
            (i, score) for i, score in enumerate(similarities)
            if score > 0.1
        ]
        return sorted(results, key=lambda x: x[1], reverse=True)

    except Exception as e:
        print(f"Cosine similarity calculation error: {e}")
        return []


def find_similar_conversations(
    documents: List[str],
    conversation_index: int,
    top_k: int = 5
) -> List[Tuple[int, float]]:
    """
    Find conversations similar to a given conversation using cosine similarity.
    """
    if not SKLEARN_AVAILABLE:
        print("Similar conversations requires scikit-learn.")
        return []

    if not documents or conversation_index >= len(documents):
        return []

    try:
        processed_docs = [preprocess_text(doc) for doc in documents]

        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(processed_docs)

        # Get similarity scores for the target conversation
        target_vector = tfidf_matrix[conversation_index]
        similarities = cosine_similarity(target_vector, tfidf_matrix).flatten()

        # Exclude the target conversation itself
        results = []
        for i, score in enumerate(similarities):
            if i != conversation_index and score > 0.1:
                results.append((i, score))

        return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]

    except Exception as e:
        print(f"Similar conversations calculation error: {e}")
        return []


def perform_topic_modeling(
    documents: List[str], n_topics: int = 5
) -> Tuple[List[List[Tuple[str, float]]], List[int]]:
    """
    Perform topic modeling using Latent Dirichlet Allocation (LDA).
    Returns (topics, document_topic_assignments).
    """
    if not SKLEARN_AVAILABLE:
        print("Topic modeling requires scikit-learn.")
        return [], []

    if not documents:
        return [], []

    try:
        processed_docs = [
            preprocess_text(doc) for doc in documents if doc.strip()
        ]

        if len(processed_docs) < n_topics:
            return [], []

        # Create count vectorizer for LDA
        vectorizer = CountVectorizer(
            stop_words='english',
            max_features=1000,
            min_df=2,
            max_df=0.8
        )

        doc_term_matrix = vectorizer.fit_transform(processed_docs)

        # Perform LDA
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=100
        )

        lda.fit(doc_term_matrix)

        # Extract topics
        feature_names = vectorizer.get_feature_names_out()
        topics = []

        for topic in lda.components_:
            top_words = [feature_names[i] for i in topic.argsort()[-10:]]
            word_scores = [
                (word, topic[vectorizer.vocabulary_[word]])
                for word in top_words
            ]
            topics.append(
                sorted(word_scores, key=lambda x: x[1], reverse=True)
            )

        # Get document topic assignments
        doc_topic_probs = lda.transform(doc_term_matrix)
        doc_topics = [int(np.argmax(probs)) for probs in doc_topic_probs]

        return topics, doc_topics

    except Exception as e:
        print(f"Topic modeling error: {e}")
        return [], []


def cluster_conversations(
    documents: List[str], n_clusters: int = 5
) -> List[int]:
    """
    Cluster conversations using K-means on TF-IDF vectors.
    Returns cluster assignments for each document.
    """
    if not SKLEARN_AVAILABLE:
        print("Clustering requires scikit-learn.")
        return []

    if not documents or len(documents) < n_clusters:
        return []

    try:
        processed_docs = [preprocess_text(doc) for doc in documents]

        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            min_df=2,
            max_df=0.8
        )

        tfidf_matrix = vectorizer.fit_transform(processed_docs)

        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)

        return cluster_labels.tolist()

    except Exception as e:
        print(f"Clustering error: {e}")
        return []


def search_with_algorithm(
    db_path: str,
    query: str,
    algorithm: str = "fts",
    bot: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Enhanced search function that supports multiple algorithms.

    Algorithms:
    - "fts": Full-text search (default)
    - "tfidf": TF-IDF scoring (requires scikit-learn)
    - "bm25": BM25 ranking
    - "cosine": Cosine similarity (requires scikit-learn)
    - "combined": Combined scoring from multiple algorithms
    """
    # First get candidate documents using basic search
    candidates = search_messages(
        db_path, query, bot, start, end, limit * 3, offset
    )

    if not candidates or algorithm == "fts":
        return candidates[:limit]

    # Extract text content for advanced algorithms
    documents = []
    for conv in candidates:
        text = (
            f"{conv.get('title', '')} {conv.get('content', '')} "
            f"{conv.get('conversation_title', '')}"
        )
        documents.append(text)

    # Apply advanced algorithm
    if algorithm == "tfidf":
        scores = calculate_tf_idf(documents, query)
    elif algorithm == "bm25":
        scores = calculate_bm25(documents, query)
    elif algorithm == "cosine":
        scores = calculate_cosine_similarity_search(documents, query)
    elif algorithm == "combined":
        # Combine multiple algorithms
        tfidf_scores = calculate_tf_idf(documents, query)
        bm25_scores = calculate_bm25(documents, query)
        cosine_scores = calculate_cosine_similarity_search(documents, query)

        # Normalize and combine scores
        score_dict: Dict[int, float] = defaultdict(float)
        algorithm_weights = [
            (tfidf_scores, 0.4),
            (bm25_scores, 0.4),
            (cosine_scores, 0.2)
        ]
        for scores_list, weight in algorithm_weights:
            max_score = max([s[1] for s in scores_list], default=1.0)
            for idx, score in scores_list:
                score_dict[idx] += (score / max_score) * weight

        scores = [(idx, score) for idx, score in score_dict.items()]
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
    else:
        return candidates[:limit]

    # Reorder results based on scores
    reordered_results = []
    for idx, score in scores[:limit]:
        if idx < len(candidates):
            result = candidates[idx].copy()
            result['relevance_score'] = score
            result['algorithm'] = algorithm
            reordered_results.append(result)

    return reordered_results
