import functools


def with_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"LOG: Running job {func.__name__}", flush=True)
        result = func(*args, **kwargs)
        print(f"LOG: Job {func.__name__} completed", flush=True)
        return result

    return wrapper
