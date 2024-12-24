from typing import Callable

from jinja2 import Template

type Localizations = dict[str, dict[str, str]]
type Links = list[tuple[str, str]]

type RenderFunction = Callable[[Template, str], str]

type AutolinkFunction = Callable[[str], Links]
type UidGenerator = Callable[[], str]
