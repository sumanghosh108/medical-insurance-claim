"""Decorators Module - Function Decorators for Cross-cutting Concerns."""

import time
import functools
import logging
from typing import Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay_seconds: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        delay_seconds: Initial delay between retries.
        backoff: Backoff multiplier for each retry.
        
    Returns:
        Decorated function.
        
    Examples:
        >>> @retry(max_attempts=3, delay_seconds=1.0)
        ... def risky_operation():
        ...     # may fail
        ...     return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay_seconds
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    logger.debug(f"Attempt {attempt + 1}/{max_attempts} for {func.__name__}")
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying in {current_delay}s: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


def timeout(seconds: float):
    """
    Timeout decorator (requires signal module).
    
    Args:
        seconds: Timeout in seconds.
        
    Returns:
        Decorated function.
    """
    import signal
    
    class TimeoutException(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Function execution timed out after {seconds}s")
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        
        return wrapper
    return decorator


def measure_performance(func: Callable) -> Callable:
    """
    Measure function execution time.
    
    Args:
        func: Function to measure.
        
    Returns:
        Decorated function.
        
    Examples:
        >>> @measure_performance
        ... def process_data(data):
        ...     # processing
        ...     return result
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            if duration > 1.0:
                logger.warning(
                    f"{func.__name__} took {duration:.2f}s (slow)"
                )
            else:
                logger.debug(f"{func.__name__} took {duration:.3f}s")
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper


def log_calls(logger_instance: logging.Logger):
    """
    Log function calls with arguments and return values.
    
    Args:
        logger_instance: Logger to use.
        
    Returns:
        Decorator function.
        
    Examples:
        >>> @log_calls(logger)
        ... def validate_claim(claim_id):
        ...     return is_valid
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger_instance.debug(
                f"Calling {func.__name__} with args={args}, kwargs={kwargs}"
            )
            try:
                result = func(*args, **kwargs)
                logger_instance.debug(f"{func.__name__} returned {result}")
                return result
            except Exception as e:
                logger_instance.error(
                    f"{func.__name__} raised {type(e).__name__}: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def validate_input(**validators):
    """
    Validate function arguments.
    
    Args:
        **validators: Keyword arguments mapping parameter names to validator functions.
        
    Returns:
        Decorator function.
        
    Examples:
        >>> from validators import validate_email
        >>> @validate_input(email=validate_email)
        ... def send_notification(email):
        ...     return send_email(email)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    if not validator(kwargs[param_name]):
                        raise ValueError(f"Invalid value for {param_name}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 3600):
    """
    Cache function result for specified time.
    
    Args:
        ttl_seconds: Time to live in seconds.
        
    Returns:
        Decorator function.
        
    Examples:
        >>> @cache_result(ttl_seconds=300)
        ... def get_user_config(user_id):
        ...     return fetch_from_db(user_id)
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = (args, tuple(sorted(kwargs.items())))
            
            now = time.time()
            if cache_key in cache:
                if now - cache_times[cache_key] < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[cache_key]
                else:
                    del cache[cache_key]
                    del cache_times[cache_key]
            
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = now
            
            logger.debug(f"Cached result for {func.__name__}")
            return result
        
        def clear_cache():
            cache.clear()
            cache_times.clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator


def synchronized(lock):
    """
    Synchronize access to function using a lock.
    
    Args:
        lock: Threading lock object.
        
    Returns:
        Decorator function.
        
    Examples:
        >>> import threading
        >>> lock = threading.Lock()
        >>> @synchronized(lock)
        ... def update_counter():
        ...     global counter
        ...     counter += 1
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def deprecated(message: str = "This function is deprecated"):
    """
    Mark function as deprecated.
    
    Args:
        message: Deprecation message.
        
    Returns:
        Decorator function.
        
    Examples:
        >>> @deprecated("Use new_function() instead")
        ... def old_function():
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(
                f"{func.__name__} is deprecated: {message}"
            )
            return func(*args, **kwargs)
        
        return wrapper
    return decorator