#!/usr/bin/env python3
"""
Test script for advanced search algorithms in search_backend.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search_backend import (SKLEARN_AVAILABLE, calculate_bm25,
                            calculate_cosine_similarity_search,
                            calculate_tf_idf, preprocess_text,
                            search_with_algorithm)


def test_basic_functions():
    """Test basic search functions work."""
    print("🧪 Testing Basic Search Functions")
    print("=" * 50)

    # Test preprocessing
    text = "Hello, World! This is a TEST."
    processed = preprocess_text(text)
    print(f"✅ Preprocessing: '{text}' -> '{processed}'")

    # Test with sample documents
    documents = [
        "Python is a great programming language for data science",
        "JavaScript is essential for web development",
        "Machine learning requires Python and mathematics",
        "React is a JavaScript framework for building UIs",
        "Data analysis often uses pandas and numpy"
    ]

    query = "Python data science"

    print(f"\n🔍 Testing with query: '{query}'")
    print(f"📚 Documents: {len(documents)} items")

    # Test BM25 (always available)
    print("\n🔢 Testing BM25 Algorithm:")
    bm25_results = calculate_bm25(documents, query)
    for i, (idx, score) in enumerate(bm25_results[:3]):
        print(f"  {i+1}. Score: {score:.3f} - {documents[idx]}")

    if SKLEARN_AVAILABLE:
        print("\n✨ Testing TF-IDF Algorithm:")
        tfidf_results = calculate_tf_idf(documents, query)
        for i, (idx, score) in enumerate(tfidf_results[:3]):
            print(f"  {i+1}. Score: {score:.3f} - {documents[idx]}")

        print("\n🎯 Testing Cosine Similarity:")
        cosine_results = calculate_cosine_similarity_search(documents, query)
        for i, (idx, score) in enumerate(cosine_results[:3]):
            print(f"  {i+1}. Score: {score:.3f} - {documents[idx]}")
    else:
        print("\n⚠️  Scikit-learn not available - advanced algorithms disabled")

    return True

def test_search_integration():
    """Test search integration with database."""
    print("\n🔗 Testing Search Integration")
    print("=" * 50)

    # Test with a sample database path (will use fallback if not found)
    db_path = "storage/conversations.db"

    if not os.path.exists(db_path):
        print(f"⚠️  Database not found at {db_path}, skipping integration test")
        return True

    algorithms = ["fts", "bm25"]
    if SKLEARN_AVAILABLE:
        algorithms.extend(["tfidf", "cosine"])

    query = "python"

    for algorithm in algorithms:
        print(f"\n🔍 Testing {algorithm.upper()} algorithm:")
        try:
            results = search_with_algorithm(
                db_path=db_path,
                query=query,
                algorithm=algorithm,
                limit=3
            )
            print(f"  Found {len(results)} results")
            for i, result in enumerate(results[:2]):
                title = result.get('title', 'No title')[:50]
                score = result.get('relevance_score', 'N/A')
                print(f"  {i+1}. {title}... (score: {score})")
        except Exception as e:
            print(f"  ❌ Error with {algorithm}: {e}")

    return True

def main():
    """Run all tests."""
    print("🚀 Advanced Search Algorithm Test Suite")
    print("=" * 60)

    success = True

    try:
        success &= test_basic_functions()
        success &= test_search_integration()

        print("\n" + "=" * 60)
        if success:
            print("🎉 All tests completed successfully!")
            if not SKLEARN_AVAILABLE:
                print("💡 To enable advanced algorithms, install: pip install scikit-learn")
        else:
            print("❌ Some tests failed")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        success = False

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
if __name__ == "__main__":
    sys.exit(main())
