from typing import Annotated

from pydantic import AfterValidator


def _reject_nul(value: str) -> str:
    # Postgres text cannot store NUL; without this the insert fails with a 500.
    if "\x00" in value:
        raise ValueError("must not contain a NUL character")
    return value


NoNulStr = Annotated[str, AfterValidator(_reject_nul)]
