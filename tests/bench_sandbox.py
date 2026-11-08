import time
from agents.validator_agent import validate

def bench_sandbox():
    print("Starting sandbox benchmark (3 cycles)...")
    
    # We use the demo repo. 
    # For a realistic cycle, we can just validate a non-patch to trigger the full suite.
    state = {
        "repo_full_name": "aryanketkar-15/arcane-demo-repo",
        "commit_sha": "main",
        "patch_diff": None,
    }
    
    times = []
    
    for i in range(3):
        print(f"\n--- Cycle {i+1} ---")
        start = time.perf_counter()
        validate(state.copy())
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"Cycle {i+1} completed in {elapsed:.2f}s")
        
        # Give a short breather to allow background thread to finish warming the container
        time.sleep(2)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print("\n==============================")
    print("BENCHMARK RESULTS")
    print(f"Cycles: 3")
    print(f"Min: {min_time:.2f}s")
    print(f"Max: {max_time:.2f}s")
    print(f"Avg: {avg_time:.2f}s")
    print("==============================")
    
    assert avg_time < 60, f"Average time too slow! Expected < 60s, got {avg_time:.2f}s"
    print("BENCHMARK PASSED!")

if __name__ == "__main__":
    bench_sandbox()
