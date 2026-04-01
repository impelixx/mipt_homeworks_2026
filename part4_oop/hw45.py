from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from part4_oop.interfaces import Cache, HasCache, Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class DictStorage(Storage[K, V]):
    _data: dict[K, V] = field(default_factory=dict, init=False)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def exists(self, key: K) -> bool:
        return key in self._data

    def remove(self, key: K) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


@dataclass
class BasePolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def get_key_to_evict(self) -> K | None:
        if self._size() >= self.capacity:
            return self._eviction_candidate()
        return None

    @property
    def has_keys(self) -> bool:
        return self._size() > 0

    def _size(self) -> int:
        raise NotImplementedError

    def _eviction_candidate(self) -> K | None:
        raise NotImplementedError


@dataclass
class FIFOPolicy(BasePolicy[K]):
    def register_access(self, key: K) -> None:
        if key in self._order:
            return
        if len(self._order) < self.capacity:
            self._order.append(key)

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    def _size(self) -> int:
        return len(self._order)

    def _eviction_candidate(self) -> K | None:
        if self._order:
            return self._order[0]
        return None


@dataclass
class LRUPolicy(BasePolicy[K]):
    def register_access(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)
            self._order.append(key)
            return
        if len(self._order) < self.capacity:
            self._order.append(key)

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    def _size(self) -> int:
        return len(self._order)

    def _eviction_candidate(self) -> K | None:
        if self._order:
            return self._order[0]
        return None


@dataclass
class LFUPolicy(BasePolicy[K]):
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)
    _last: K | None = field(default=None, init=False)

    def register_access(self, key: K) -> None:
        count = self._key_counter.get(key)
        if count is not None:
            self._key_counter[key] = count + 1
            self._last = None
            return
        if len(self._key_counter) < self.capacity:
            self._key_counter[key] = 1
            self._last = key
            return
        self._last = None

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)
        if self._last == key:
            self._last = None

    def clear(self) -> None:
        self._key_counter.clear()
        self._last = None

    def _size(self) -> int:
        return len(self._key_counter)

    def _eviction_candidate(self) -> K | None:
        if self._last in self._key_counter:
            candidates = [k for k in self._key_counter if k != self._last]
            if candidates:
                return min(candidates, key=lambda candidate: self._key_counter[candidate])
        if self._key_counter:
            return min(self._key_counter, key=lambda candidate: self._key_counter[candidate])
        return None


class MIPTCache(Cache[K, V]):
    def __init__(self, storage: Storage[K, V], policy: Policy[K]) -> None:
        self.storage = storage
        self.policy = policy

    def set(self, key: K, value: V) -> None:
        if not self.storage.exists(key):
            key_to_evict = self.policy.get_key_to_evict()
            if key_to_evict is not None:
                self.storage.remove(key_to_evict)
                self.policy.remove_key(key_to_evict)
        self.storage.set(key, value)
        self.policy.register_access(key)

    def get(self, key: K) -> V | None:
        value = self.storage.get(key)
        if value is not None:
            self.policy.register_access(key)
        return value

    def exists(self, key: K) -> bool:
        return self.storage.exists(key)

    def remove(self, key: K) -> None:
        self.storage.remove(key)
        self.policy.remove_key(key)

    def clear(self) -> None:
        self.storage.clear()
        self.policy.clear()


class CachedProperty[V]:
    def __init__(self, func: Callable[[Any], V]) -> None:
        self._func = func
        self._name = func.__name__

    def __get__(self, instance: HasCache[Any, V] | None, owner: type) -> V:
        if instance is None:
            return self  # type: ignore[return-value]
        value = instance.cache.get(self._name)
        if value is not None:
            return value
        res = self._func(instance)
        instance.cache.set(self._name, res)

        return res
