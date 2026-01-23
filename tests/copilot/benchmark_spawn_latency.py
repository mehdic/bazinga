#!/usr/bin/env python3
"""
Phase 0 Tech Spike: Benchmark Spawn Latency

Measures and compares agent spawn latency between Claude Code and GitHub Copilot.

IMPORTANT: Run this script in BOTH environments and compare results.
"""

import time
import json
from datetime import datetime
from typing import Dict, List

class SpawnLatencyBenchmark:
    """Benchmark agent spawn latency."""

    def __init__(self, platform: str):
        """
        Initialize benchmark.

        Args:
            platform: 'claude' or 'copilot'
        """
        self.platform = platform
        self.results: List[Dict] = []

    def measure_single_spawn(self, agent_name: str, task: str) -> float:
        """
        Measure time to spawn a single agent and get first response.

        Args:
            agent_name: Name of agent to spawn
            task: Task description

        Returns:
            Latency in seconds (spawn call to first response)

        Note: This is a MANUAL MEASUREMENT. The actual spawning must be done
        by the user in the respective environment (Claude Code or Copilot).
        """
        print(f"\n{'=' * 60}")
        print(f"MANUAL MEASUREMENT REQUIRED")
        print(f"{'=' * 60}")
        print(f"Platform: {self.platform}")
        print(f"Agent: {agent_name}")
        print(f"Task: {task}")
        print()

        if self.platform == 'claude':
            print("In Claude Code, use:")
            print(f"  Task(subagent_type='{agent_name}', prompt='{task}')")
        else:  # copilot
            print("In Copilot, use:")
            print(f"  #runSubagent @{agent_name} \"{task}\"")

        print()
        print("Steps:")
        print("1. Note the current time")
        print("2. Execute the spawn command")
        print("3. Note when you receive the FIRST response from the agent")
        print("4. Calculate latency = (response time - spawn time)")
        print()

        latency_str = input("Enter measured latency in seconds (e.g., 1.5): ")
        try:
            latency = float(latency_str)
            self.results.append({
                'agent': agent_name,
                'task': task,
                'latency': latency,
                'timestamp': datetime.now().isoformat()
            })
            return latency
        except ValueError:
            print("❌ Invalid input. Using 0.0")
            return 0.0

    def measure_parallel_spawn(self, count: int, agent_name: str, task: str) -> Dict:
        """
        Measure latency when spawning multiple agents in parallel.

        Args:
            count: Number of agents to spawn simultaneously
            agent_name: Name of agent to spawn
            task: Task description

        Returns:
            Dict with timing measurements
        """
        print(f"\n{'=' * 60}")
        print(f"PARALLEL SPAWN MEASUREMENT")
        print(f"{'=' * 60}")
        print(f"Platform: {self.platform}")
        print(f"Agent: {agent_name}")
        print(f"Count: {count}")
        print(f"Task: {task}")
        print()

        if self.platform == 'claude':
            print("In Claude Code, spawn multiple Task() calls in one message:")
            for i in range(count):
                print(f"  Task(subagent_type='{agent_name}', prompt='{task} #{i+1}')")
        else:  # copilot
            print("In Copilot, use multiple #runSubagent calls:")
            for i in range(count):
                print(f"  #runSubagent @{agent_name} \"{task} #{i+1}\"")

        print()
        print("Measurements needed:")
        print("1. Time from spawn command to FIRST agent response")
        print("2. Time from spawn command to LAST agent response")
        print()

        first_str = input("Latency to FIRST response (seconds): ")
        last_str = input("Latency to LAST response (seconds): ")

        try:
            first_latency = float(first_str)
            last_latency = float(last_str)

            result = {
                'type': 'parallel',
                'count': count,
                'agent': agent_name,
                'first_response_latency': first_latency,
                'last_response_latency': last_latency,
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result
        except ValueError:
            print("❌ Invalid input")
            return {}

    def run_benchmark_suite(self):
        """Run complete benchmark suite."""
        print(f"\n{'=' * 60}")
        print(f"SPAWN LATENCY BENCHMARK - {self.platform.upper()}")
        print(f"{'=' * 60}")
        print()

        # Test 1: Single agent spawn
        print("Test 1: Single Agent Spawn")
        self.measure_single_spawn('test-worker', 'Count to 3 with 1s delay')

        # Test 2: Parallel spawn (2 agents)
        print("\nTest 2: Parallel Spawn (2 agents)")
        self.measure_parallel_spawn(2, 'test-worker', 'Count to 3 with 1s delay')

        # Test 3: Parallel spawn (4 agents)
        print("\nTest 3: Parallel Spawn (4 agents)")
        self.measure_parallel_spawn(4, 'test-worker', 'Count to 3 with 1s delay')

    def save_results(self, filename: str):
        """Save benchmark results to JSON file."""
        data = {
            'platform': self.platform,
            'timestamp': datetime.now().isoformat(),
            'results': self.results
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✅ Results saved to {filename}")

    def compare_with(self, other_results_file: str):
        """
        Compare current results with results from another platform.

        Args:
            other_results_file: Path to JSON file with other platform's results
        """
        with open(other_results_file, 'r') as f:
            other_data = json.load(f)

        print(f"\n{'=' * 60}")
        print(f"COMPARISON: {self.platform.upper()} vs {other_data['platform'].upper()}")
        print(f"{'=' * 60}")

        # Compare single spawn latency
        my_single = [r for r in self.results if r.get('type') != 'parallel']
        other_single = [r for r in other_data['results'] if r.get('type') != 'parallel']

        if my_single and other_single:
            my_avg = sum(r['latency'] for r in my_single) / len(my_single)
            other_avg = sum(r['latency'] for r in other_single) / len(other_single)
            overhead = my_avg - other_avg

            print(f"\nSingle Agent Spawn:")
            print(f"  {self.platform}: {my_avg:.2f}s")
            print(f"  {other_data['platform']}: {other_avg:.2f}s")
            print(f"  Overhead: {overhead:+.2f}s")

            # GO/NO-GO criterion: <2s overhead
            if abs(overhead) < 2.0:
                print(f"  ✅ PASS - Overhead within acceptable range (<2s)")
            else:
                print(f"  ❌ FAIL - Overhead exceeds 2s threshold")

        # Compare parallel spawn latency
        my_parallel = [r for r in self.results if r.get('type') == 'parallel']
        other_parallel = [r for r in other_data['results'] if r.get('type') == 'parallel']

        if my_parallel and other_parallel:
            print(f"\nParallel Spawn (First Response):")
            for my_r in my_parallel:
                count = my_r['count']
                other_r = next((r for r in other_parallel if r['count'] == count), None)
                if other_r:
                    my_lat = my_r['first_response_latency']
                    other_lat = other_r['first_response_latency']
                    overhead = my_lat - other_lat

                    print(f"  {count} agents:")
                    print(f"    {self.platform}: {my_lat:.2f}s")
                    print(f"    {other_data['platform']}: {other_lat:.2f}s")
                    print(f"    Overhead: {overhead:+.2f}s")


def main():
    """Main benchmark entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python benchmark_spawn_latency.py <platform>")
        print()
        print("Platforms: claude, copilot")
        print()
        print("Example:")
        print("  python benchmark_spawn_latency.py claude")
        print("  python benchmark_spawn_latency.py copilot")
        print()
        print("After running on both platforms, compare with:")
        print("  benchmark.compare_with('results_other_platform.json')")
        sys.exit(1)

    platform = sys.argv[1].lower()
    if platform not in ('claude', 'copilot'):
        print(f"❌ Invalid platform: {platform}")
        print("Must be 'claude' or 'copilot'")
        sys.exit(1)

    benchmark = SpawnLatencyBenchmark(platform)
    benchmark.run_benchmark_suite()

    # Save results
    output_file = f"benchmark_results_{platform}.json"
    benchmark.save_results(output_file)

    # If other platform's results exist, compare
    other_platform = 'copilot' if platform == 'claude' else 'claude'
    other_file = f"benchmark_results_{other_platform}.json"

    try:
        benchmark.compare_with(other_file)
    except FileNotFoundError:
        print(f"\nℹ️  To compare results, run this benchmark on {other_platform} platform")
        print(f"   and it will automatically compare with {platform} results.")


if __name__ == '__main__':
    main()
