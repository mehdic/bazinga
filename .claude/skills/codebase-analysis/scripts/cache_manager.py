#!/usr/bin/env python3
"""Cache management for analysis results."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import hashlib


class CacheManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_index_file = os.path.join(cache_dir, "cache_index.json")
        self._load_index()

    def _load_index(self):
        """Load cache index."""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r') as f:
                    self.cache_index = json.load(f)
            except:
                self.cache_index = {}
        else:
            self.cache_index = {}

    def _save_index(self):
        """Save cache index."""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except:
            pass

    def get(self, key: str, max_age_hours: Optional[int] = None) -> Optional[Any]:
        """Get cached value if it exists and is not stale."""
        cache_file = os.path.join(self.cache_dir, f"{self._hash_key(key)}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check age if specified
            if max_age_hours:
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cached_time > timedelta(hours=max_age_hours):
                    # Cache is stale, remove it
                    self._remove_cache_file(key)
                    return None

            # Update access time in index
            self.cache_index[key] = {
                'file': f"{self._hash_key(key)}.json",
                'last_accessed': datetime.now().isoformat(),
                'created': cache_data.get('timestamp', datetime.now().isoformat())
            }
            self._save_index()

            return cache_data['value']

        except Exception:
            return None

    def set(self, key: str, value: Any):
        """Set cached value."""
        cache_file = os.path.join(self.cache_dir, f"{self._hash_key(key)}.json")

        cache_data = {
            'key': key,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }

        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            # Update index
            self.cache_index[key] = {
                'file': f"{self._hash_key(key)}.json",
                'last_accessed': datetime.now().isoformat(),
                'created': datetime.now().isoformat()
            }
            self._save_index()

        except Exception:
            pass

    def clear_old_cache(self, max_age_days: int = 7):
        """Clear cache entries older than specified days."""
        now = datetime.now()
        keys_to_remove = []

        for key, info in self.cache_index.items():
            try:
                created = datetime.fromisoformat(info['created'])
                if now - created > timedelta(days=max_age_days):
                    keys_to_remove.append(key)
            except:
                # Invalid entry, remove it
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self._remove_cache_file(key)

    def _remove_cache_file(self, key: str):
        """Remove a cache file and its index entry."""
        if key in self.cache_index:
            cache_file = os.path.join(self.cache_dir, self.cache_index[key]['file'])
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            except:
                pass
            del self.cache_index[key]
            self._save_index()

    def _hash_key(self, key: str) -> str:
        """Hash key for filename."""
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'total_entries': len(self.cache_index),
            'cache_size_bytes': 0,
            'oldest_entry': None,
            'newest_entry': None
        }

        # Calculate cache size
        for info in self.cache_index.values():
            cache_file = os.path.join(self.cache_dir, info['file'])
            if os.path.exists(cache_file):
                stats['cache_size_bytes'] += os.path.getsize(cache_file)

        # Find oldest and newest
        if self.cache_index:
            entries_by_date = sorted(
                self.cache_index.items(),
                key=lambda x: x[1].get('created', ''),
            )
            if entries_by_date:
                stats['oldest_entry'] = entries_by_date[0][1].get('created')
                stats['newest_entry'] = entries_by_date[-1][1].get('created')

        return stats
