import json
from datetime import UTC, datetime
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, exce: str, func_name: str | None = None, block_time: datetime | None = None):
        super().__init__(exce)
        if func_name is not None:
            self.func_name = func_name
        if block_time is not None:
            self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        validation_errors: list[ValueError] = []
        if critical_count <= 0:
            validation_errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if time_to_recover <= 0:
            validation_errors.append(ValueError(INVALID_RECOVERY_TIME))
        if validation_errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, validation_errors)

        self._critical_count = critical_count
        self._time_to_rec = time_to_recover
        self._cnt = 0
        self._triggers_on = triggers_on
        self._block_time: datetime | None = None
        self._func_name: str | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        self._func_name = f"{func.__module__}.{func.__name__}"

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            if self._block_time is not None:
                if (datetime.now(UTC) - self._block_time).total_seconds() < self._time_to_rec:
                    raise BreakerError(TOO_MUCH, self._func_name, self._block_time)
                self._block_time = None
                self._cnt = 0
            return self._handle_func(func, *args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__module__ = func.__module__
        wrapper.__doc__ = func.__doc__
        return wrapper

    def _handle_func(self, func: CallableWithMeta[P, R_co], *args: P.args, **kwargs: P.kwargs) -> R_co:
        res: R_co
        try:
            res = func(*args, **kwargs)
        except self._triggers_on as err:
            self._cnt += 1
            if self._cnt >= self._critical_count:
                self._block_time = datetime.now(UTC)
                raise BreakerError(TOO_MUCH, self._func_name, self._block_time) from err
            raise
        except Exception:
            raise
        self._cnt = 0
        self._block_time = None
        return res


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
