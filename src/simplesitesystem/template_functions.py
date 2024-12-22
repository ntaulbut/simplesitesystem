from os.path import *
from typing import Callable

from jinja2 import Template
from pygments.formatters.html import HtmlFormatter
from pyquery import PyQuery

from simplesitesystem.tools import strip_exts

type Links = list[tuple[str, str]]
type AutolinkFunction = Callable[[str], Links]
type UidGenerator = Callable[[], str]


def get_uid_generator() -> UidGenerator:
    n: int = 0

    def get_uid() -> str:
        nonlocal n
        n += 1
        return f"uid-{n}"

    return get_uid


def get_autolink(
    in_template_dir: str,
    in_page_path: str,
    locale: str,
    templates: list[Template],
    render: Callable,
    dev_mode: bool,
) -> AutolinkFunction:
    """
    :param dev_mode:
    :param in_page_path:
    :param in_template_dir:
    :param locale: Locale the template is being rendered with
    :param templates: List of all Templates
    :param render: This function needs to request a template be rendered,
    so it can extract info from the result, like the page title
    :return: Autolink function
    """

    def autolink(path: str) -> Links:
        """
        :param path: Path to link pages from, relative to the calling template.
        :return: Links to and other information about pages in the requested path.
        """
        qualified_path: str = join(in_template_dir, path)

        for target in templates:
            target_dirname = dirname(target.name)
            if target_dirname == qualified_path:
                target_page: str = render(target, locale)
                print(target_page)
                filename: str = basename(target_page)

                url: str = join(
                    relpath(
                        dirname(target_page),
                        dirname(in_page_path),
                    ),
                    filename if dev_mode else strip_exts(filename),
                )

                document: PyQuery = PyQuery(filename=target_page)
                title: str = document("head title").text()
                description: str = document("meta[name='description']").attr("content")

                yield url, title, description

    return autolink


def code_style(style: str):
    return HtmlFormatter(style=style).get_style_defs(".highlight")
