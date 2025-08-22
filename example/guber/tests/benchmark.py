import asyncio
import statistics
import time
from typing import List


from example.guber.server.application.usecase.ride import (
    perfomance_test_parallel,
    perfomance_test_sequence,
)
from grpcAPI.protobuf import Empty
from grpcAPI.testclient.testclient import TestClient


async def _measure_execution_time(
    func, app_test_client: TestClient, runs: int = 10
) -> List[float]:
    """Measure execution time for multiple runs of a function."""
    times = []

    for i in range(runs):
        start_time = time.perf_counter()

        await app_test_client.run(
            func=func,
            request=Empty(),
        )

        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        times.append(execution_time)

        # Small delay between runs to avoid overwhelming the system
        await asyncio.sleep(0.01)

    return times


def _print_performance_stats(name: str, times: List[float]):
    """Print performance statistics."""
    print(f"\n=== {name} Performance Statistics ===")
    print(f"Runs: {len(times)}")
    print(f"Average: {statistics.mean(times):.3f} ms")
    print(f"Median: {statistics.median(times):.3f} ms")
    print(f"Min: {min(times):.3f} ms")
    print(f"Max: {max(times):.3f} ms")
    if len(times) > 1:
        print(f"Std Dev: {statistics.stdev(times):.3f} ms")
    print(f"Total: {sum(times):.3f} ms")


async def test_performance_comparison(
    app_test_client: TestClient,
):
    """Compare performance between parallel and sequence implementations."""
    runs = 20  # Number of times to run each function

    print(f"\nRunning performance comparison with {runs} runs each...")

    # Test parallel implementation
    print("Testing parallel implementation...")
    parallel_times = await _measure_execution_time(
        perfomance_test_parallel, app_test_client, runs
    )
    _print_performance_stats("Parallel Implementation", parallel_times)

    # Small delay between test batches
    await asyncio.sleep(0.1)

    # Test sequence implementation
    print("Testing sequence implementation...")
    sequence_times = await _measure_execution_time(
        perfomance_test_sequence, app_test_client, runs
    )
    _print_performance_stats("Sequence Implementation", sequence_times)

    # Performance comparison
    parallel_avg = statistics.mean(parallel_times)
    sequence_avg = statistics.mean(sequence_times)

    print("\n=== Performance Comparison ===")
    print(f"Parallel Average: {parallel_avg:.3f} ms")
    print(f"Sequence Average: {sequence_avg:.3f} ms")

    if parallel_avg < sequence_avg:
        speedup = sequence_avg / parallel_avg
        print(f"Parallel is {speedup:.2f}x faster than sequence")
    else:
        slowdown = parallel_avg / sequence_avg
        print(f"Sequence is {slowdown:.2f}x faster than parallel")

    print(f"Difference: {abs(parallel_avg - sequence_avg):.3f} ms")


n = 200


async def test_parallel_performance_only(
    app_test_client: TestClient,
):
    """Test only parallel performance with detailed metrics."""
    runs = n

    print(f"\nTesting parallel implementation with {runs} runs...")
    times = await _measure_execution_time(
        perfomance_test_parallel, app_test_client, runs
    )
    _print_performance_stats("Parallel Implementation (Detailed)", times)

    # Additional analysis
    if len(times) > 10:
        print(f"95th percentile: {statistics.quantiles(times, n=20)[18]:.3f} ms")
        print(f"99th percentile: {statistics.quantiles(times, n=100)[98]:.3f} ms")


async def test_sequence_performance_only(
    app_test_client: TestClient,
):
    """Test only sequence performance with detailed metrics."""
    runs = n

    print(f"\nTesting sequence implementation with {runs} runs...")
    times = await _measure_execution_time(
        perfomance_test_sequence, app_test_client, runs
    )
    _print_performance_stats("Sequence Implementation (Detailed)", times)

    # Additional analysis
    if len(times) > 10:
        print(f"95th percentile: {statistics.quantiles(times, n=20)[18]:.3f} ms")
        print(f"99th percentile: {statistics.quantiles(times, n=100)[98]:.3f} ms")


async def test_warmup_and_performance(
    app_test_client: TestClient,
):
    """Test with warmup runs to account for JIT/caching effects."""
    warmup_runs = 5
    test_runs = 30

    print(
        f"\nPerformance test with {warmup_runs} warmup runs and {test_runs} test runs..."
    )

    # Warmup parallel
    print("Warming up parallel...")
    await _measure_execution_time(
        perfomance_test_parallel, app_test_client, warmup_runs
    )

    # Test parallel
    print("Testing parallel (post-warmup)...")
    parallel_times = await _measure_execution_time(
        perfomance_test_parallel, app_test_client, test_runs
    )

    # Warmup sequence
    print("Warming up sequence...")
    await _measure_execution_time(
        perfomance_test_sequence, app_test_client, warmup_runs
    )

    # Test sequence
    print("Testing sequence (post-warmup)...")
    sequence_times = await _measure_execution_time(
        perfomance_test_sequence, app_test_client, test_runs
    )

    _print_performance_stats("Parallel (Warmed Up)", parallel_times)
    _print_performance_stats("Sequence (Warmed Up)", sequence_times)


# Simple individual tests for basic functionality
async def test_parallel_basic(
    app_test_client: TestClient,
):
    """Basic test for parallel function."""
    result = await app_test_client.run(
        func=perfomance_test_parallel,
        request=Empty(),
    )
    assert isinstance(result, Empty)


async def test_sequence_basic(
    app_test_client: TestClient,
):
    """Basic test for sequence function."""
    result = await app_test_client.run(
        func=perfomance_test_sequence,
        request=Empty(),
    )
    assert isinstance(result, Empty)
