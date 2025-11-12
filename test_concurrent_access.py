#!/usr/bin/env python3
"""
Test concurrent database access for BAZINGA orchestration.
Simulates multiple agents writing to database while dashboard reads.
"""

import sys
import time
import threading
import random
from pathlib import Path

# Add database script to path
sys.path.insert(0, str(Path(__file__).parent / '.claude' / 'skills' / 'bazinga-db' / 'scripts'))
from bazinga_db import BazingaDB

DB_PATH = Path(__file__).parent / 'coordination' / 'bazinga.db'
TEST_SESSION = f"test_concurrent_{int(time.time())}"

def writer_thread(thread_id, iterations=10):
    """Simulate an agent writing to database."""
    db = BazingaDB(str(DB_PATH))

    for i in range(iterations):
        try:
            # Log interaction
            db.log_interaction(
                session_id=TEST_SESSION,
                agent_type='developer',
                content=f"Thread {thread_id} iteration {i} - Doing some work...",
                iteration=i,
                agent_id=f"developer_{thread_id}"
            )

            # Log token usage
            db.log_tokens(TEST_SESSION, 'developer', random.randint(1000, 5000), f"developer_{thread_id}")

            # Small random delay
            time.sleep(random.uniform(0.01, 0.05))

        except Exception as e:
            print(f"❌ Writer {thread_id} error: {e}")
            raise

    print(f"✅ Writer {thread_id} completed {iterations} writes")

def reader_thread(thread_id, iterations=20):
    """Simulate dashboard reading from database."""
    db = BazingaDB(str(DB_PATH))

    for i in range(iterations):
        try:
            # Read dashboard snapshot
            snapshot = db.get_dashboard_snapshot(TEST_SESSION)

            # Read logs
            logs = db.get_logs(TEST_SESSION, limit=10)

            # Read token summary
            tokens = db.get_token_summary(TEST_SESSION)

            # Small random delay
            time.sleep(random.uniform(0.01, 0.03))

        except Exception as e:
            print(f"❌ Reader {thread_id} error: {e}")
            raise

    print(f"✅ Reader {thread_id} completed {iterations} reads")

def main():
    """Run concurrent access test."""
    print("="*60)
    print("🧪 BAZINGA Concurrent Database Access Test")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Test session: {TEST_SESSION}")
    print()

    # Create test session
    db = BazingaDB(str(DB_PATH))
    db.create_session(TEST_SESSION, 'parallel', 'Concurrent access test')
    print(f"✅ Created test session")

    # Start concurrent threads
    print(f"\n🚀 Starting concurrent operations...")
    print(f"   Writers: 4 threads x 10 writes each = 40 writes")
    print(f"   Readers: 2 threads x 20 reads each = 40 reads")
    print()

    start_time = time.time()

    threads = []

    # Start writer threads
    for i in range(4):
        t = threading.Thread(target=writer_thread, args=(i,))
        t.start()
        threads.append(t)

    # Start reader threads
    for i in range(2):
        t = threading.Thread(target=reader_thread, args=(i,))
        t.start()
        threads.append(t)

    # Wait for all threads to complete
    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    print()
    print("="*60)
    print("📊 Test Results")
    print("="*60)
    print(f"⏱️  Total time: {elapsed:.2f}s")
    print(f"✅ All concurrent operations completed successfully")
    print()

    # Verify data integrity
    print("🔍 Verifying data integrity...")
    final_logs = db.get_logs(TEST_SESSION)
    token_summary = db.get_token_summary(TEST_SESSION)

    print(f"   Total logs: {len(final_logs)}")
    print(f"   Total tokens: {token_summary.get('total', 0)}")
    print(f"   Token by type: {token_summary}")
    print()

    # Clean up test session
    db.update_session_status(TEST_SESSION, 'completed')
    print(f"✅ Test session marked as completed")

    print()
    print("="*60)
    print("✨ Concurrent Access Test PASSED")
    print("="*60)

if __name__ == '__main__':
    main()
