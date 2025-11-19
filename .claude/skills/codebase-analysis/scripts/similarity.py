#!/usr/bin/env python3
"""Find similar code to a given task."""

import os
import re
from typing import List, Dict, Any
from difflib import SequenceMatcher


class SimilarityFinder:
    def find_similar(self, task: str) -> List[Dict[str, Any]]:
        """Find files similar to the given task."""
        # Extract keywords from task
        keywords = self.extract_keywords(task)
        similar_files = []

        # Search for files containing keywords
        for root, dirs, files in os.walk("."):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', 'dist', 'build', '__pycache__', 'vendor', 
                'coverage', 'target', 'out', '.git'
            ]]

            for file in files:
                # Only check source code files
                if self._is_source_file(file):
                    file_path = os.path.join(root, file)
                    similarity_score = self.calculate_similarity(file_path, keywords)
                    
                    if similarity_score > 0.3:  # 30% similarity threshold
                        matched_keywords = self.get_matched_keywords(file_path, keywords)
                        patterns = self.extract_patterns(file_path)
                        
                        similar_files.append({
                            "file": file_path,
                            "similarity": similarity_score,
                            "matched_keywords": matched_keywords,
                            "patterns": patterns
                        })

        # Sort by similarity score
        similar_files.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_files[:5]  # Return top 5

    def extract_keywords(self, task: str) -> List[str]:
        """Extract meaningful keywords from task description."""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 
            'implement', 'add', 'create', 'make', 'build', 'write', 'update',
            'fix', 'change', 'modify', 'new', 'should', 'must', 'need', 'want'
        }

        # Extract words
        words = re.findall(r'\b[a-zA-Z]+\b', task.lower())
        
        # Filter keywords
        keywords = []
        for word in words:
            if word not in stop_words and len(word) > 2:
                keywords.append(word)
                # Also add variations
                if word.endswith('ing'):
                    base = word[:-3]
                    if len(base) > 2:
                        keywords.append(base)
                elif word.endswith('ed'):
                    base = word[:-2]
                    if len(base) > 2:
                        keywords.append(base)

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords

    def calculate_similarity(self, file_path: str, keywords: List[str]) -> float:
        """Calculate similarity score between file and keywords."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                
            # Calculate based on multiple factors
            scores = []
            
            # 1. Keyword presence score
            if keywords:
                matched = sum(1 for keyword in keywords if keyword in content)
                keyword_score = matched / len(keywords)
                scores.append(keyword_score)
            
            # 2. Filename similarity
            filename = os.path.basename(file_path).lower()
            filename_words = re.findall(r'\b[a-zA-Z]+\b', filename)
            if keywords and filename_words:
                filename_matches = sum(1 for keyword in keywords if any(
                    keyword in word or word in keyword 
                    for word in filename_words
                ))
                filename_score = filename_matches / len(keywords)
                scores.append(filename_score * 1.5)  # Boost filename matches
            
            # 3. Path similarity (e.g., auth/login.py for "authentication" task)
            path_parts = file_path.lower().split(os.sep)
            if keywords and path_parts:
                path_matches = sum(1 for keyword in keywords if any(
                    keyword in part for part in path_parts
                ))
                path_score = path_matches / len(keywords)
                scores.append(path_score * 1.2)  # Slightly boost path matches
            
            # Return weighted average
            if scores:
                return min(sum(scores) / len(scores), 1.0)  # Cap at 1.0
            return 0.0

        except Exception:
            return 0.0

    def get_matched_keywords(self, file_path: str, keywords: List[str]) -> List[str]:
        """Get list of keywords that matched in the file."""
        matched = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()

            for keyword in keywords:
                if keyword in content:
                    matched.append(keyword)

        except Exception:
            pass

        return matched

    def extract_patterns(self, file_path: str) -> List[str]:
        """Extract notable patterns from a file."""
        patterns = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Look for common patterns
            patterns_found = set()
            
            # Service/class definitions
            for line in lines:
                if re.match(r'^class\s+\w+Service', line):
                    patterns_found.add("service layer pattern")
                elif re.match(r'^class\s+\w+Repository', line):
                    patterns_found.add("repository pattern")
                elif re.match(r'^class\s+\w+Factory', line):
                    patterns_found.add("factory pattern")
                elif re.match(r'^class\s+\w+Controller', line):
                    patterns_found.add("controller pattern")
                elif '@' in line and ('route' in line.lower() or 'app.' in line):
                    patterns_found.add("decorator-based routing")
                elif 'async def' in line or 'async function' in line:
                    patterns_found.add("async/await pattern")
                elif 'try:' in line or 'try {' in line:
                    patterns_found.add("error handling")
                elif 'jwt' in line.lower() or 'token' in line.lower():
                    patterns_found.add("token-based auth")
                elif 'validate' in line.lower() or 'validator' in line.lower():
                    patterns_found.add("validation logic")
                elif 'transaction' in line.lower() or 'commit' in line.lower():
                    patterns_found.add("database transactions")

            patterns = list(patterns_found)

        except Exception:
            pass

        return patterns[:5]  # Limit to top 5 patterns

    def _is_source_file(self, filename: str) -> bool:
        """Check if file is a source code file."""
        source_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs',
            '.rb', '.php', '.cs', '.cpp', '.cc', '.c', '.h', '.hpp',
            '.swift', '.kt', '.scala', '.ex', '.exs'
        }
        
        for ext in source_extensions:
            if filename.endswith(ext):
                return True
        return False
