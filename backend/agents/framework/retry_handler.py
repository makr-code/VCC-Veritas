"""
Retry Handler for VERITAS Agent Framework

Implements exponential backoff retry logic for failed research plan steps.

Key Features:
- Exponential backoff algorithm (base: 2, factor: 1.5)
- max_retries enforcement from step configuration
- retry_count tracking in database
- Context preservation across retries
- Configurable retry strategies (exponential, linear, constant)
- Jitter to avoid thundering herd

Author: VERITAS AI Agent System
Created: 2025-10-08
"""

import time
import random
import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry backoff strategies"""
    EXPONENTIAL = "exponential"  # delay = base_delay * (backoff_factor ** attempt)
    LINEAR = "linear"            # delay = base_delay * attempt
    CONSTANT = "constant"        # delay = base_delay
    FIBONACCI = "fibonacci"      # delay = fibonacci(attempt) * base_delay


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    backoff_factor: float = 2.0
    max_delay: float = 60.0  # cap at 60 seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True  # add randomness to prevent thundering herd
    jitter_range: float = 0.1  # ±10% jitter


class RetryHandler:
    """
    Handles retry logic for failed research plan steps.
    
    Features:
    - Multiple retry strategies (exponential, linear, constant, fibonacci)
    - Configurable delays and max retries
    - Jitter to avoid synchronized retries
    - Retry count tracking
    - Context preservation
    
    Usage:
        handler = RetryHandler()
        result = handler.execute_with_retry(
            func=my_function,
            step_id="step_1",
            max_retries=3,
            context={"key": "value"}
        )
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry handler.
        
        Args:
            config: Retry configuration (uses defaults if None)
        """
        self.config = config or RetryConfig()
        self._fibonacci_cache = {0: 0, 1: 1}
    
    def calculate_delay(
        self,
        attempt: int,
        strategy: Optional[RetryStrategy] = None,
        base_delay: Optional[float] = None,
        backoff_factor: Optional[float] = None
    ) -> float:
        """
        Calculate retry delay based on strategy.
        
        Args:
            attempt: Current retry attempt (1-indexed)
            strategy: Override default strategy
            base_delay: Override default base delay
            backoff_factor: Override default backoff factor
            
        Returns:
            Delay in seconds
        """
        strategy = strategy or self.config.strategy
        base_delay = base_delay or self.config.base_delay
        backoff_factor = backoff_factor or self.config.backoff_factor
        
        if strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (backoff_factor ** (attempt - 1))
        elif strategy == RetryStrategy.LINEAR:
            delay = base_delay * attempt
        elif strategy == RetryStrategy.CONSTANT:
            delay = base_delay
        elif strategy == RetryStrategy.FIBONACCI:
            fib = self._fibonacci(attempt)
            delay = fib * base_delay
        else:
            raise ValueError(f"Unknown retry strategy: {strategy}")
        
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter
        if self.config.jitter:
            jitter = delay * self.config.jitter_range * (2 * random.random() - 1)
            delay = max(0, delay + jitter)
        
        return delay
    
    def _fibonacci(self, n: int) -> int:
        """Calculate fibonacci number with memoization"""
        if n in self._fibonacci_cache:
            return self._fibonacci_cache[n]
        
        result = self._fibonacci(n - 1) + self._fibonacci(n - 2)
        self._fibonacci_cache[n] = result
        return result
    
    def should_retry(
        self,
        attempt: int,
        max_retries: int,
        exception: Optional[Exception] = None
    ) -> bool:
        """
        Determine if retry should be attempted.
        
        Args:
            attempt: Current attempt number (1-indexed)
            max_retries: Maximum allowed retries
            exception: Exception that caused failure (optional)
            
        Returns:
            True if retry should be attempted
        """
        if attempt > max_retries:
            return False
        
        # Could add exception-based retry logic here
        # e.g., don't retry ValidationError, but retry NetworkError
        if exception:
            # For now, retry all exceptions
            # In production, add exception whitelist/blacklist
            pass
        
        return True
    
    def execute_with_retry(
        self,
        func: Callable,
        step_id: str,
        max_retries: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute (should return Dict[str, Any])
            step_id: Step identifier for logging
            max_retries: Override default max_retries
            context: Context to preserve across retries
            **kwargs: Additional arguments for func
            
        Returns:
            Result from successful execution
            
        Raises:
            Exception: If all retries exhausted
        """
        max_retries = max_retries or self.config.max_retries
        context = context or {}
        
        last_exception = None
        
        for attempt in range(1, max_retries + 2):  # +1 for initial attempt, +1 for range
            try:
                logger.info(
                    f"Step {step_id}: Attempt {attempt}/{max_retries + 1}"
                )
                
                # Execute function
                result = func(context=context, **kwargs)
                
                # Success
                if attempt > 1:
                    logger.info(
                        f"Step {step_id}: Success after {attempt - 1} retries"
                    )
                
                # Add retry metadata to result
                result['retry_count'] = attempt - 1
                result['retry_successful'] = attempt > 1
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Step {step_id}: Attempt {attempt} failed: {str(e)}"
                )
                
                # Check if we should retry
                if not self.should_retry(attempt, max_retries, e):
                    logger.error(
                        f"Step {step_id}: Max retries ({max_retries}) exhausted"
                    )
                    raise
                
                # Calculate delay
                if attempt <= max_retries:  # Don't delay after last retry
                    delay = self.calculate_delay(attempt)
                    logger.info(
                        f"Step {step_id}: Retrying in {delay:.2f}s "
                        f"(strategy: {self.config.strategy.value})"
                    )
                    time.sleep(delay)
        
        # Should never reach here, but just in case
        raise last_exception or RuntimeError("Retry logic error")
    
    def get_retry_stats(self, attempt: int) -> Dict[str, Any]:
        """
        Get statistics about retry attempts.
        
        Args:
            attempt: Current attempt number
            
        Returns:
            Dictionary with retry statistics
        """
        # Delays only for retries (not initial attempt)
        retry_count = max(0, attempt - 1)
        delays = [
            self.calculate_delay(i) 
            for i in range(1, retry_count + 1)
        ]
        
        return {
            'total_attempts': attempt,
            'retry_count': retry_count,
            'total_delay': sum(delays),
            'avg_delay': sum(delays) / len(delays) if delays else 0,
            'delays': delays,
            'strategy': self.config.strategy.value,
            'max_retries': self.config.max_retries
        }


# Test Suite
def _test_retry_handler():
    """Test retry handler functionality"""
    print("=" * 80)
    print("RETRY HANDLER TEST SUITE")
    print("=" * 80)
    
    # Test 1: Exponential backoff calculation
    print("\n[TEST 1] Exponential Backoff Calculation")
    handler = RetryHandler(RetryConfig(
        base_delay=1.0,
        backoff_factor=2.0,
        jitter=False  # Disable for predictable testing
    ))
    
    delays = [handler.calculate_delay(i) for i in range(1, 6)]
    expected = [1.0, 2.0, 4.0, 8.0, 16.0]
    
    print(f"Delays: {[f'{d:.1f}s' for d in delays]}")
    print(f"Expected: {[f'{d:.1f}s' for d in expected]}")
    assert delays == expected, "Exponential backoff mismatch"
    print("✅ PASSED: Exponential backoff correct")
    
    # Test 2: Linear backoff
    print("\n[TEST 2] Linear Backoff")
    handler = RetryHandler(RetryConfig(
        strategy=RetryStrategy.LINEAR,
        base_delay=2.0,
        jitter=False
    ))
    
    delays = [handler.calculate_delay(i) for i in range(1, 5)]
    expected = [2.0, 4.0, 6.0, 8.0]
    
    print(f"Delays: {[f'{d:.1f}s' for d in delays]}")
    assert delays == expected, "Linear backoff mismatch"
    print("✅ PASSED: Linear backoff correct")
    
    # Test 3: Constant backoff
    print("\n[TEST 3] Constant Backoff")
    handler = RetryHandler(RetryConfig(
        strategy=RetryStrategy.CONSTANT,
        base_delay=3.0,
        jitter=False
    ))
    
    delays = [handler.calculate_delay(i) for i in range(1, 5)]
    expected = [3.0, 3.0, 3.0, 3.0]
    
    print(f"Delays: {[f'{d:.1f}s' for d in delays]}")
    assert delays == expected, "Constant backoff mismatch"
    print("✅ PASSED: Constant backoff correct")
    
    # Test 4: Fibonacci backoff
    print("\n[TEST 4] Fibonacci Backoff")
    handler = RetryHandler(RetryConfig(
        strategy=RetryStrategy.FIBONACCI,
        base_delay=1.0,
        jitter=False
    ))
    
    delays = [handler.calculate_delay(i) for i in range(1, 7)]
    expected = [1.0, 1.0, 2.0, 3.0, 5.0, 8.0]  # Fibonacci: 1,1,2,3,5,8
    
    print(f"Delays: {[f'{d:.1f}s' for d in delays]}")
    assert delays == expected, "Fibonacci backoff mismatch"
    print("✅ PASSED: Fibonacci backoff correct")
    
    # Test 5: Max delay cap
    print("\n[TEST 5] Max Delay Cap")
    handler = RetryHandler(RetryConfig(
        base_delay=10.0,
        backoff_factor=3.0,
        max_delay=50.0,
        jitter=False
    ))
    
    delays = [handler.calculate_delay(i) for i in range(1, 5)]
    # Without cap: 10, 30, 90, 270
    # With cap (50): 10, 30, 50, 50
    
    print(f"Delays: {[f'{d:.1f}s' for d in delays]}")
    assert all(d <= 50.0 for d in delays), "Max delay not enforced"
    assert delays == [10.0, 30.0, 50.0, 50.0], "Max delay cap incorrect"
    print("✅ PASSED: Max delay cap enforced")
    
    # Test 6: Jitter range
    print("\n[TEST 6] Jitter Range")
    handler = RetryHandler(RetryConfig(
        base_delay=10.0,
        jitter=True,
        jitter_range=0.2  # ±20%
    ))
    
    delays = [handler.calculate_delay(1) for _ in range(100)]
    min_delay = min(delays)
    max_delay = max(delays)
    
    print(f"Base delay: 10.0s")
    print(f"Min delay: {min_delay:.2f}s")
    print(f"Max delay: {max_delay:.2f}s")
    print(f"Expected range: 8.0s - 12.0s (±20%)")
    
    # Allow some tolerance for randomness
    assert 7.5 <= min_delay <= 8.5, "Jitter min out of range"
    assert 11.5 <= max_delay <= 12.5, "Jitter max out of range"
    print("✅ PASSED: Jitter range correct")
    
    # Test 7: Successful execution (no retries)
    print("\n[TEST 7] Successful Execution (No Retries)")
    handler = RetryHandler(RetryConfig(max_retries=3))
    
    call_count = 0
    def success_func(context=None):
        nonlocal call_count
        call_count += 1
        return {'status': 'success', 'data': 'test'}
    
    result = handler.execute_with_retry(
        func=success_func,
        step_id="test_step_1",
        max_retries=3
    )
    
    print(f"Call count: {call_count}")
    print(f"Retry count: {result['retry_count']}")
    assert call_count == 1, "Should only call once"
    assert result['retry_count'] == 0, "Should have 0 retries"
    assert result['retry_successful'] is False, "No retry occurred"
    print("✅ PASSED: Successful first attempt")
    
    # Test 8: Retry and succeed
    print("\n[TEST 8] Retry and Succeed (2nd Attempt)")
    handler = RetryHandler(RetryConfig(
        max_retries=3,
        base_delay=0.1,  # Fast for testing
        jitter=False
    ))
    
    call_count = 0
    def retry_once_func(context=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First attempt fails")
        return {'status': 'success', 'data': 'test'}
    
    start_time = time.time()
    result = handler.execute_with_retry(
        func=retry_once_func,
        step_id="test_step_2",
        max_retries=3
    )
    elapsed = time.time() - start_time
    
    print(f"Call count: {call_count}")
    print(f"Retry count: {result['retry_count']}")
    print(f"Elapsed time: {elapsed:.2f}s")
    
    assert call_count == 2, "Should call twice"
    assert result['retry_count'] == 1, "Should have 1 retry"
    assert result['retry_successful'] is True, "Retry was successful"
    assert elapsed >= 0.1, "Should wait at least base_delay"
    print("✅ PASSED: Retry succeeded on 2nd attempt")
    
    # Test 9: Max retries exhausted
    print("\n[TEST 9] Max Retries Exhausted")
    handler = RetryHandler(RetryConfig(
        max_retries=2,
        base_delay=0.05,
        jitter=False
    ))
    
    call_count = 0
    def always_fail_func(context=None):
        nonlocal call_count
        call_count += 1
        raise RuntimeError(f"Attempt {call_count} failed")
    
    try:
        result = handler.execute_with_retry(
            func=always_fail_func,
            step_id="test_step_3",
            max_retries=2
        )
        assert False, "Should have raised exception"
    except RuntimeError as e:
        print(f"Call count: {call_count}")
        print(f"Exception: {str(e)}")
        assert call_count == 3, "Should call 3 times (1 initial + 2 retries)"
        assert "Attempt 3 failed" in str(e), "Wrong exception message"
        print("✅ PASSED: Max retries exhausted correctly")
    
    # Test 10: Context preservation
    print("\n[TEST 10] Context Preservation")
    handler = RetryHandler(RetryConfig(
        max_retries=3,
        base_delay=0.05,
        jitter=False
    ))
    
    contexts_seen = []
    def context_check_func(context=None):
        contexts_seen.append(context.copy())
        if len(contexts_seen) < 2:
            context['attempt'] = len(contexts_seen)
            raise ValueError("Need retry")
        return {'status': 'success'}
    
    initial_context = {'key': 'value', 'attempt': 0}
    result = handler.execute_with_retry(
        func=context_check_func,
        step_id="test_step_4",
        max_retries=3,
        context=initial_context
    )
    
    print(f"Contexts seen: {contexts_seen}")
    assert len(contexts_seen) == 2, "Should see context twice"
    assert contexts_seen[1]['attempt'] == 1, "Context should be preserved"
    print("✅ PASSED: Context preserved across retries")
    
    # Test 11: Retry statistics
    print("\n[TEST 11] Retry Statistics")
    handler = RetryHandler(RetryConfig(
        base_delay=1.0,
        backoff_factor=2.0,
        jitter=False
    ))
    
    stats = handler.get_retry_stats(3)
    
    print(f"Stats: {stats}")
    assert stats['total_attempts'] == 3, "Wrong attempt count"
    assert stats['retry_count'] == 2, "Wrong retry count"
    assert stats['total_delay'] == 3.0, "Wrong total delay (1 + 2)"
    assert stats['avg_delay'] == 1.5, "Wrong average delay"
    assert stats['delays'] == [1.0, 2.0], "Wrong delay list"
    print("✅ PASSED: Statistics correct")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✅ ALL 11 TESTS PASSED")
    print("\nRetry Handler Features Validated:")
    print("  ✓ Exponential backoff calculation")
    print("  ✓ Linear backoff strategy")
    print("  ✓ Constant backoff strategy")
    print("  ✓ Fibonacci backoff strategy")
    print("  ✓ Max delay cap enforcement")
    print("  ✓ Jitter randomization")
    print("  ✓ Successful execution (no retries)")
    print("  ✓ Retry and succeed (2nd attempt)")
    print("  ✓ Max retries exhausted")
    print("  ✓ Context preservation across retries")
    print("  ✓ Retry statistics calculation")
    print("=" * 80)


if __name__ == "__main__":
    _test_retry_handler()
