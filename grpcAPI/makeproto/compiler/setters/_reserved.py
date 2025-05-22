from functools import singledispatchmethod
from typing import List, NoReturn, Optional, Set, Union


class Indexer:
    def __init__(
        self, start: int = 1, idxs: Optional[List[Union[int, range]]] = None
    ) -> None:
        self._start = start
        self._counter = start
        self._reserveds: List[Union[int, range]] = []
        for idx in idxs or []:
            self.reserve(idx)

    def __contains__(self, item: int) -> bool:
        if not isinstance(item, int):  # type: ignore
            return False
        return item in self._flatten_reserveds()

    @property
    def current(self) -> int:
        return self._counter

    @property
    def reserved(self) -> List[Union[int, range]]:
        return self._reserveds

    @property
    def flat_reserved(self) -> List[int]:
        return list(self._flatten_reserveds())

    @singledispatchmethod
    def reserve(self, idx: Union[int, range]) -> NoReturn:
        raise TypeError(f"Unsupported type for reserve: {type(idx)}")

    @reserve.register
    def _(self, idx: int) -> None:
        if idx >= self._start:
            self._reserveds.append(idx)

    @reserve.register
    def _(self, idx: range) -> None:
        if idx.stop >= self._start:
            start = max(self._start, idx.start)
            stop = idx.stop + 1  # Tornar o range inclusivo
            if stop > start:
                self._reserveds.append(range(start, stop))

    @property
    def next(self) -> int:
        flat = self._flatten_reserveds()
        i = self._counter
        while i in flat:
            i += 1
        self._counter = i + 1
        return i

    def _flatten_reserveds(self) -> Set[int]:
        return {
            i
            for x in self._reserveds
            for i in (x if isinstance(x, range) else [x])
            if i >= self._start
        }

    def _merge_ranges(self, items: List[Union[int, range]]) -> List[Union[int, range]]:
        ints = sorted(
            {
                i
                for x in items
                for i in (x if isinstance(x, range) else [x])
                if i >= self._start
            }
        )
        if not ints:
            return []

        result: List[Union[int, range]] = []
        start = prev = ints[0]
        for i in ints[1:]:
            if i == prev + 1:
                prev = i
            else:
                if start == prev:
                    result.append(start)
                else:
                    result.append(range(start, prev + 1))
                start = prev = i
        if start == prev:
            result.append(start)
        else:
            result.append(range(start, prev + 1))
        return result

    def _overlaps(self, a: Union[int, range], b: Union[int, range]) -> bool:
        a_range = range(a, a + 1) if isinstance(a, int) else a
        b_range = range(b, b + 1) if isinstance(b, int) else b
        return a_range.stop > b_range.start and b_range.stop > a_range.start

    def __str__(self) -> str:
        merged = self._merge_ranges(self._reserveds)
        parts: List[str] = []
        for item in merged:
            if isinstance(item, int):
                parts.append(str(item))
            elif item.stop - item.start == 2:
                parts.append(f"{item.start}")
                parts.append(f"{item.start + 1}")
            else:
                parts.append(f"{item.start} to {item.stop - 1}")
        return ",".join(parts)


def reserved_keys_str(keys: List[str]) -> str:
    return ", ".join(f'"{name}"' for name in keys)
