#!/usr/bin/env python3
"""
Text Similarity Functions

Provides functions for calculating text similarity between task descriptions
and code files using TF-IDF and cosine similarity.
"""

import re
from collections import Counter
from typing import List, Set
import math


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text.

    Args:
        text: Input text
        min_length: Minimum keyword length

    Returns:
        List of keywords
    """
    # Convert to lowercase
    text = text.lower()

    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # Split into words
    words = text.split()

    # Common stop words to filter out
    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
        'in', 'with', 'to', 'for', 'of', 'as', 'by', 'from', 'that', 'this',
        'it', 'be', 'are', 'was', 'were', 'been', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can',
        'may', 'might', 'must', 'shall'
    }

    # Filter out stop words and short words
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stop_words
    ]

    return keywords


def calculate_term_frequency(keywords: List[str]) -> Counter:
    """
    Calculate term frequency (TF).

    Args:
        keywords: List of keywords

    Returns:
        Counter with term frequencies
    """
    return Counter(keywords)


def calculate_cosine_similarity(vec1: Counter, vec2: Counter) -> float:
    """
    Calculate cosine similarity between two term frequency vectors.

    Args:
        vec1: First term frequency vector
        vec2: Second term frequency vector

    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    # Get all unique terms
    all_terms = set(vec1.keys()) | set(vec2.keys())

    if not all_terms:
        return 0.0

    # Calculate dot product
    dot_product = sum(vec1[term] * vec2[term] for term in all_terms)

    # Calculate magnitudes
    magnitude1 = math.sqrt(sum(vec1[term] ** 2 for term in vec1))
    magnitude2 = math.sqrt(sum(vec2[term] ** 2 for term in vec2))

    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    # Calculate cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)

    return similarity


def calculate_similarity(query: str, document: str) -> float:
    """
    Calculate similarity between query text and document.

    Uses keyword extraction and cosine similarity.

    Args:
        query: Query text (task description)
        document: Document text (code file content)

    Returns:
        Similarity score (0.0 to 1.0)
    """
    # Extract keywords
    query_keywords = extract_keywords(query)
    doc_keywords = extract_keywords(document)

    # Calculate term frequencies
    query_tf = calculate_term_frequency(query_keywords)
    doc_tf = calculate_term_frequency(doc_keywords)

    # Calculate cosine similarity
    similarity = calculate_cosine_similarity(query_tf, doc_tf)

    return similarity


def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Calculate Jaccard similarity between two sets.

    Args:
        set1: First set
        set2: Second set

    Returns:
        Jaccard similarity (0.0 to 1.0)
    """
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union


def find_matching_keywords(query: str, document: str) -> List[str]:
    """
    Find keywords that appear in both query and document.

    Args:
        query: Query text
        document: Document text

    Returns:
        List of matching keywords
    """
    query_keywords = set(extract_keywords(query))
    doc_keywords = set(extract_keywords(document))

    matching = list(query_keywords & doc_keywords)
    return matching


def calculate_keyword_density(keywords: List[str], text: str) -> float:
    """
    Calculate density of specific keywords in text.

    Args:
        keywords: Keywords to search for
        text: Text to search in

    Returns:
        Density score (0.0 to 1.0)
    """
    text_lower = text.lower()
    total_words = len(text.split())

    if total_words == 0:
        return 0.0

    # Count keyword occurrences
    keyword_count = sum(text_lower.count(keyword.lower()) for keyword in keywords)

    # Calculate density
    density = min(keyword_count / total_words, 1.0)

    return density


# Example usage
if __name__ == "__main__":
    # Test similarity calculation
    query = "Implement password reset endpoint with email token"
    document = """
    def reset_password(email, token):
        if not validate_email(email):
            return error_response('Invalid email')

        if not verify_token(token):
            return error_response('Invalid token')

        # Reset password logic
        user = User.query.filter_by(email=email).first()
        user.reset_password()

        # Send confirmation email
        send_email(email, 'Password reset successful')

        return success_response()
    """

    similarity = calculate_similarity(query, document)
    print(f"Similarity: {similarity:.2f}")

    keywords = extract_keywords(query)
    print(f"Keywords: {keywords}")

    matching = find_matching_keywords(query, document)
    print(f"Matching keywords: {matching}")
