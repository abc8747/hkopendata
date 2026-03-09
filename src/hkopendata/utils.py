import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Awaitable,
    Callable,
    Generic,
    Literal,
    NoReturn,
    ParamSpec,
    TypeAlias,
    TypeVar,
    Union,
    cast,
)

import httpx
import orjson
from typing_extensions import dataclass_transform

if TYPE_CHECKING:
    _D = TypeVar("_D")

    @dataclass_transform(frozen_default=True)
    def dataclass_frozen(cls: type[_D]) -> type[_D]: ...
else:
    dataclass_frozen = dataclass(slots=True)

T = TypeVar("T")
E = TypeVar("E")
P = ParamSpec("P")


@dataclass_frozen
class Ok(Generic[T]):
    _value: T

    def ok(self) -> T:
        return self._value

    def err(self) -> None:
        return None

    def is_ok(self) -> Literal[True]:
        return True

    def is_err(self) -> Literal[False]:
        return False

    def unwrap(self) -> T:
        return self._value


@dataclass_frozen
class Err(Generic[E]):
    _value: E

    def ok(self) -> None:
        return None

    def err(self) -> E:
        return self._value

    def is_ok(self) -> Literal[False]:
        return False

    def is_err(self) -> Literal[True]:
        return True

    def unwrap(self) -> NoReturn:
        raise UnwrapError(
            self, f"called `Result.unwrap()` on errored result: {self._value!r}"
        )


class UnwrapError(Exception):
    def __init__(self, err: Any, message: str) -> None:
        self._err = err
        super().__init__(message)

    @property
    def err(self) -> Any:
        return self._err


Result: TypeAlias = Union[Ok[T], Err[E]]
"""A type that represents either success (`Ok`) or failure (`Err`)."""

#
# json parse utils
#

_TypedDictT = TypeVar("_TypedDictT")
ParseError: TypeAlias = httpx.HTTPStatusError | orjson.JSONDecodeError
GetJsonError: TypeAlias = httpx.HTTPError | orjson.JSONDecodeError


class _Parser(Generic[_TypedDictT]):
    @staticmethod
    def parse_json(
        response: Annotated[httpx.Response, _TypedDictT],
    ) -> Result[_TypedDictT, ParseError]:
        try:
            response.raise_for_status()
            return Ok(cast(_TypedDictT, orjson.loads(response.content)))
        except (httpx.HTTPStatusError, orjson.JSONDecodeError) as exc:
            return Err(exc)


def is_retryable_http_exception(
    exc: object,
    *,
    status_codes: frozenset[int] = frozenset({429, 500, 502, 503, 504}),
) -> bool:
    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    return (
        isinstance(exc, httpx.HTTPStatusError)
        and exc.response.status_code in status_codes
    )


def with_retry(
    func: Callable[P, Awaitable[Result[T, E]]],
    *,
    retries: int = 3,
    base_delay_seconds: float = 0.5,
    should_retry: Callable[[object], bool] = lambda exc: is_retryable_http_exception(
        exc,
        status_codes=frozenset({403, 429, 500, 502, 503, 504}),
    ),
) -> Callable[P, Awaitable[Result[T, E]]]:
    @wraps(func)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> Result[T, E]:
        for attempt in range(retries):
            result = await func(*args, **kwargs)
            if result.is_ok():
                return result

            error = result.err()
            if error is None or attempt + 1 >= retries or not should_retry(error):
                return result

            await asyncio.sleep(base_delay_seconds * (attempt + 1))

        raise RuntimeError("unreachable")

    return wrapped
