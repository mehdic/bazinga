#!/usr/bin/env python3
"""
Phase 0 Tech Spike: Test #runSubagent Parallel Execution

This test validates that GitHub Copilot's #runSubagent feature can spawn
multiple agents concurrently (not sequentially).

IMPORTANT: This test must be run in GitHub Copilot environment, not Claude Code.
"""

import re
from datetime import datetime
from typing import List, Tuple

def parse_timestamp(line: str) -> datetime | None:
    """Extract timestamp from worker output line."""
    match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
    if match:
        return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
    return None

def analyze_parallel_execution(output1: str, output2: str) -> dict:
    """
    Analyze worker outputs to determine if execution was parallel.

    Args:
        output1: Output from first worker agent
        output2: Output from second worker agent

    Returns:
        dict with analysis results:
            - parallel: bool, whether execution was parallel
            - total_time: float, seconds from first start to last completion
            - overlap: float, seconds of overlapping execution
            - worker1_times: tuple of (start, end) timestamps
            - worker2_times: tuple of (start, end) timestamps
    """
    lines1 = output1.strip().split('\n')
    lines2 = output2.strip().split('\n')

    # Extract timestamps
    timestamps1 = [parse_timestamp(line) for line in lines1 if parse_timestamp(line)]
    timestamps2 = [parse_timestamp(line) for line in lines2 if parse_timestamp(line)]

    if not timestamps1 or not timestamps2:
        return {
            'error': 'Could not parse timestamps from worker outputs',
            'parallel': False
        }

    # Get start and end times for each worker
    worker1_start = min(timestamps1)
    worker1_end = max(timestamps1)
    worker2_start = min(timestamps2)
    worker2_end = max(timestamps2)

    # Calculate total time from first start to last completion
    first_start = min(worker1_start, worker2_start)
    last_end = max(worker1_end, worker2_end)
    total_time = (last_end - first_start).total_seconds()

    # Calculate overlap (time when both workers were running)
    overlap_start = max(worker1_start, worker2_start)
    overlap_end = min(worker1_end, worker2_end)
    overlap = max(0, (overlap_end - overlap_start).total_seconds())

    # Determine if execution was parallel
    # Parallel: significant overlap (>80% of shorter task duration)
    # Sequential: minimal overlap (<20%)
    worker1_duration = (worker1_end - worker1_start).total_seconds()
    worker2_duration = (worker2_end - worker2_start).total_seconds()
    shorter_duration = min(worker1_duration, worker2_duration)

    parallel = overlap > (shorter_duration * 0.8)

    return {
        'parallel': parallel,
        'total_time': total_time,
        'overlap': overlap,
        'worker1_times': (worker1_start, worker1_end),
        'worker2_times': (worker2_start, worker2_end),
        'worker1_duration': worker1_duration,
        'worker2_duration': worker2_duration,
        'overlap_percentage': (overlap / shorter_duration * 100) if shorter_duration > 0 else 0
    }

def test_parallel_execution_manual():
    """
    Manual test for Copilot environment.

    To run this test:
    1. Open this file in VS Code with Copilot
    2. Invoke @test-parallel with: "Spawn 2 worker agents in parallel"
    3. Capture the output from both workers
    4. Paste outputs into output1 and output2 variables below
    5. Run this function
    """
    print("=" * 60)
    print("PHASE 0 TECH SPIKE: #runSubagent Parallel Execution Test")
    print("=" * 60)
    print()
    print("INSTRUCTIONS:")
    print("1. In Copilot chat, invoke: @test-parallel Spawn 2 workers")
    print("2. Copy the output from Worker 1 and Worker 2")
    print("3. Update this script with the outputs")
    print("4. Run this function again to analyze results")
    print()

    # PLACEHOLDER: Replace with actual worker outputs
    output1 = """
[2026-01-23 10:00:00] Worker starting
[2026-01-23 10:00:00] 1
[2026-01-23 10:00:01] 2
[2026-01-23 10:00:02] 3
[2026-01-23 10:00:03] 4
[2026-01-23 10:00:04] 5
[2026-01-23 10:00:05] Worker complete
"""

    output2 = """
[2026-01-23 10:00:00] Worker starting
[2026-01-23 10:00:00] 1
[2026-01-23 10:00:01] 2
[2026-01-23 10:00:02] 3
[2026-01-23 10:00:03] 4
[2026-01-23 10:00:04] 5
[2026-01-23 10:00:05] Worker complete
"""

    print("Analyzing worker outputs...")
    result = analyze_parallel_execution(output1, output2)

    if 'error' in result:
        print(f"\n❌ ERROR: {result['error']}")
        return False

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Time: {result['total_time']:.2f}s")
    print(f"Worker 1 Duration: {result['worker1_duration']:.2f}s")
    print(f"Worker 2 Duration: {result['worker2_duration']:.2f}s")
    print(f"Overlap: {result['overlap']:.2f}s ({result['overlap_percentage']:.1f}%)")
    print()
    print(f"Execution Mode: {'✅ PARALLEL' if result['parallel'] else '❌ SEQUENTIAL'}")
    print()

    # GO/NO-GO Decision
    print("=" * 60)
    print("GO/NO-GO DECISION")
    print("=" * 60)

    criteria = {
        'Parallel Execution': result['parallel'],
        'Spawn Latency <2s': result['total_time'] < (result['worker1_duration'] + 2),
        'No Critical Errors': not result.get('error')
    }

    for criterion, passed in criteria.items():
        status = '✅ PASS' if passed else '❌ FAIL'
        print(f"{status} - {criterion}")

    all_passed = all(criteria.values())
    print()
    print(f"OVERALL: {'🟢 GO' if all_passed else '🔴 NO-GO'}")
    print()

    return all_passed

def test_analysis_algorithm():
    """Test the analysis algorithm with known scenarios."""
    print("Testing analysis algorithm...")

    # Scenario 1: Perfect parallel execution
    parallel_output1 = """
[2026-01-23 10:00:00] Worker starting
[2026-01-23 10:00:05] Worker complete
"""
    parallel_output2 = """
[2026-01-23 10:00:00] Worker starting
[2026-01-23 10:00:05] Worker complete
"""

    result = analyze_parallel_execution(parallel_output1, parallel_output2)
    assert result['parallel'] == True, "Failed to detect parallel execution"
    assert abs(result['total_time'] - 5.0) < 0.1, "Incorrect total time"
    print("✅ Parallel execution detection works")

    # Scenario 2: Sequential execution
    sequential_output1 = """
[2026-01-23 10:00:00] Worker starting
[2026-01-23 10:00:05] Worker complete
"""
    sequential_output2 = """
[2026-01-23 10:00:05] Worker starting
[2026-01-23 10:00:10] Worker complete
"""

    result = analyze_parallel_execution(sequential_output1, sequential_output2)
    assert result['parallel'] == False, "Failed to detect sequential execution"
    assert abs(result['total_time'] - 10.0) < 0.1, "Incorrect total time"
    print("✅ Sequential execution detection works")

    print("\nAll algorithm tests passed!")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test-algorithm':
        test_analysis_algorithm()
    else:
        test_parallel_execution_manual()
