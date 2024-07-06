import os
import shutil
from typing import Callable

import click
import tomli
from jinja2 import Environment, FileSystemLoader, Template
from pyquery import PyQuery
from pygments.formatters import HtmlFormatter
from simplesitesystem.code_extension import CodeExtension

IGNORE = ".simpleignore"

type Localizations = dict[str, dict[str, str]]
type Links = list[tuple[str, str]]
type AutolinkFunction = Callable[[str], Links]


def extension(filename: str) -> str:
    """
    :param filename: index.html.jinja
    :return: .jinja
    """
    return os.path.splitext(filename)[1]


def strip_exts(filename: str) -> str:
    """
    :param filename: index.html.jinja
    :return: index
    """
    return filename.split(os.extsep)[0]


def read_localizations(path: str) -> Localizations:
    try:
        with open(path, "rb") as f:
            try:
                return tomli.load(f)
            except tomli.TOMLDecodeError:
                exit(f"{path} is not a valid TOML file.")
    except FileNotFoundError:
        exit(f"{path} does not exist.")


def assets(source_dir: str) -> list[str]:
    for directory, subdirectories, filenames in os.walk(source_dir):
        for filename in filenames:
            if extension(filename) != ".jinja":
                yield os.path.join(directory, filename)


def symlink(asset_filepath: str, locale_dir: str, first_locale_dir: str) -> None:
    """
    Creates a relative symlink from `output/jp/img/catpicture.jpg` to `output/en/img/catpicture.jpg`.
    e.g. ../../en/img/catpicture.jpg.

    :param asset_filepath: img/catpicture.jpg
    :param locale_dir: output/jp/
    :param first_locale_dir: output/en/
    """
    # output/jp/img/catpicture.jpg
    new_filepath = os.path.join(locale_dir, asset_filepath)
    # output/en/img/catpicture.jpg
    existing_filepath = os.path.join(first_locale_dir, asset_filepath)
    # output/jp/img/
    new_file_dir = os.path.dirname(new_filepath)
    # output/en/img/
    existing_file_dir = os.path.dirname(existing_filepath)

    os.makedirs(new_file_dir, exist_ok=True)
    os.symlink(
        os.path.join(
            os.path.relpath(existing_file_dir, new_file_dir),
            os.path.basename(asset_filepath),
        ),
        new_filepath,
    )


def get_autolink(
    in_template_dir: str,
    in_page_path: str,
    locale: str,
    templates: list[Template],
    render: Callable,
) -> AutolinkFunction:
    """
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
        qualified_path: str = os.path.join(in_template_dir, path)

        for target in templates:
            target_dirname = os.path.dirname(target.name)
            if target_dirname == qualified_path:
                target_page: str = render(target, locale)

                url: str = os.path.join(
                    os.path.relpath(
                        os.path.dirname(target_page),
                        os.path.dirname(in_page_path),
                    ),
                    os.path.basename(target_page),
                )

                document: PyQuery = PyQuery(filename=target_page)
                title: str = document("head title").text()
                description: str = document("meta[name='description']").attr("content")

                yield url, title, description

    return autolink


def code_style(style: str):
    return HtmlFormatter(style=style).get_style_defs(".highlight")


def get_renderer(templates: list[Template], output_dir: str, localizations=None) -> Callable:
    """
    :param localizations: Localizations
    :param templates: List of all Templates
    :param output_dir: output/
    :return: RenderLocale function
    """
    if localizations is None:
        localizations = {}
    pages: list[str] = []

    def render(template: Template, locale: str = "") -> str:
        """
        :param locale: Locale to render template with, e.g. en
        :param template: Template to render
        :return: Path the template was written to
        """
        page_path: str = (
            strip_exts(os.path.join(output_dir, locale, template.name)) + ".html"
        )
        page_dir: str = os.path.dirname(page_path)
        os.makedirs(page_dir, exist_ok=True)
        if page_path not in pages:
            with open(page_path, "w") as f:
                f.write(
                    template.render(
                        autolink=get_autolink(
                            os.path.dirname(template.name),
                            page_path,
                            locale,
                            templates,
                            render,
                        ),
                        strings=localizations[locale] if locale else None,
                        locale=locale,
                        code_style=code_style,
                    )
                )
            pages.append(page_path)
        return page_path

    return render


@click.group()
def simplesitesystem():
    pass


@simplesitesystem.command()
@click.argument(
    "source_dir", type=click.Path(file_okay=False, dir_okay=True, exists=True)
)
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True, writable=True)
)
@click.option(
    "-s",
    "--strings",
    "strings_file",
    default="strings.toml",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="Translations file.",
)
@click.option("--no-symlink-assets", default=False, is_flag=True)
def build(
    source_dir: str,
    output_dir: str,
    strings_file: str,
    no_symlink_assets: bool,
) -> None:
    env: Environment = Environment(
        loader=FileSystemLoader(source_dir),
        extensions=[CodeExtension],
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Look for file containing newline-separated template names to exclude
    ignore: list[str] = []
    try:
        with open(IGNORE, "r") as f:
            ignore = [p.strip() for p in f.readlines()]
            print("Excluding:", ", ".join(ignore))
    except FileNotFoundError:
        print(f"{IGNORE} not found.")

    # Delete contents of output directory, if it exists
    shutil.rmtree(os.path.join(output_dir, "."), ignore_errors=True)

    print("Loading templates...")
    templates: list[Template] = [
        env.get_template(path)
        for path in env.list_templates(extensions="jinja")
        if path not in ignore
    ]

    if strings_file is None:
        print("Rendering...")
        render: Callable = get_renderer(templates, output_dir)
        shutil.copytree(
            source_dir,
            output_dir,
            ignore=shutil.ignore_patterns("*.jinja"),
            dirs_exist_ok=True,
        )
        for template in templates:
            render(template)
        return

    localizations: Localizations = read_localizations(strings_file)
    if len(localizations) == 0:
        print("No localizations in strings file.")
        return
    render: Callable = get_renderer(templates, output_dir, localizations)
    first_locale: str = next(iter(localizations))  # en
    first_locale_dir: str = os.path.join(output_dir, first_locale)  # output/en

    for locale in localizations:
        print(f"Rendering locale {locale}...")
        locale_dir: str = os.path.join(output_dir, locale)  # output/jp

        if locale == first_locale or no_symlink_assets:
            shutil.copytree(
                source_dir,
                locale_dir,
                ignore=shutil.ignore_patterns("*.jinja"),
                dirs_exist_ok=True,
            )
        else:
            for filepath in assets(source_dir):
                symlink(
                    os.path.relpath(filepath, source_dir),
                    locale_dir,
                    first_locale_dir,
                )

        for template in templates:
            render(template, locale)


# A rendered template is a page
# Non-template files in the source directory are assets

if __name__ == "__main__":
    simplesitesystem()
