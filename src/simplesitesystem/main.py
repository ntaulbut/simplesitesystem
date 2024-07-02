import os

import shutil
from typing import Callable

from pyquery import PyQuery
import click

import tomli
from jinja2 import Environment, FileSystemLoader, Template

STRINGS_PATH = "strings.toml"

# Return types
type Localizations = dict[str, dict[str, str]]
type Links = list[tuple[str, str]]

# Callable types
type RenderTemplate = Callable[[Template, str], str]
type Autolink = Callable[[str], Links]


def extension(filename: str) -> str:
    """
    :param filename: index.html.jinja
    :return: .jinja
    """
    return os.path.splitext(filename)[1]


def strip_extension(filename: str) -> str:
    """
    :param filename: index.html.jinja
    :return: index.html
    """
    return os.path.splitext(filename)[0]


def localized_output_path(
    filepath: str, locale: str, source_dir: str, output_dir: str
) -> str:
    """
    :param filepath: src/blog/test.html.jinja
    :param locale: en
    :param source_dir: src/
    :param output_dir: output/
    :return: /output/en/blog/ramen-recipe.html
    """
    return strip_extension(
        os.path.join(output_dir, locale, os.path.relpath(filepath, source_dir))
    )


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
    for directory, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if extension(filename) != ".jinja":
                yield os.path.join(directory, filename)


def symlink(filepath: str, locale_dir: str, primary_locale_dir: str) -> None:
    """
    Creates a relative symlink from `output/jp/img/catpicture.jpg` to `output/en/img/catpicture.jpg`.
    e.g. ../../en/img/catpicture.jpg.

    :param filepath: img/catpicture.jpg
    :param locale_dir: output/jp/
    :param primary_locale_dir: output/en/
    """
    # output/jp/img/catpicture.jpg
    output_filepath = os.path.join(locale_dir, filepath)
    # output/en/img/catpicture.jpg
    primary_filepath = os.path.join(primary_locale_dir, filepath)
    # output/jp/img/
    output_file_dir = os.path.dirname(output_filepath)
    # output/en/img/
    primary_file_dir = os.path.dirname(primary_filepath)

    os.makedirs(output_file_dir, exist_ok=True)
    os.symlink(
        os.path.join(
            os.path.relpath(primary_file_dir, output_file_dir),
            os.path.basename(filepath),
        ),
        output_filepath,
    )


def configure_autolink(
    origin_template_dir: str,
    locale: str,
    templates: list[Template],
    render_locale: RenderTemplate,
    output_dir: str,
) -> Autolink:
    """
    :param origin_template_dir: Directory of the template the configured function will be called in
    :param locale: Locale the template is being rendered with
    :param templates: List of all Templates
    :param render_locale: This function needs to request a template be rendered,
    so it can extract info from the result, like the page title
    :param output_dir: output/
    :return: Autolink function
    """

    def autolink(requested_directory: str) -> Links:
        """
        :param requested_directory: This is relative to the directory of the template this function is called in
        :return: Links to and other information about templates in the requested directory.
        """
        # output/en/blog
        output_directory = os.path.join(origin_template_dir, requested_directory)
        # output/en
        locale_directory = os.path.join(output_dir, locale)
        # blog
        relative_directory = os.path.relpath(output_directory, locale_directory)

        for template in templates:
            template_dirname = os.path.dirname(template.name)
            if template_dirname == relative_directory:
                rendered_template: str = render_locale(template, locale)
                url: str = os.path.relpath(rendered_template, origin_template_dir)

                document: PyQuery = PyQuery(filename=rendered_template)
                title: str = document("head title").text()
                description: str = document("meta[name='description']").attr("content")

                yield url, title, description

    return autolink


def configure_renderer(
    localizations: Localizations,
    templates: list[Template],
    source_dir: str,
    output_dir: str,
) -> RenderTemplate:
    """
    :param localizations: Localizations
    :param templates: List of all Templates
    :param source_dir: src/
    :param output_dir: output/
    :return: RenderLocale function
    """
    rendered: list[str] = []

    def render_template(template: Template, locale: str) -> str:
        """
        :param locale: Locale to render template with, e.g. en
        :param template: Template to render
        :return: Path the template was written to
        """
        rendered_path: str = localized_output_path(
            template.filename, locale, source_dir, output_dir
        )
        rendered_dir: str = os.path.dirname(rendered_path)
        os.makedirs(rendered_dir, exist_ok=True)
        if rendered_path in rendered:
            return rendered_path  # Don't render twice
        with open(rendered_path, "w") as f:
            f.write(
                template.render(
                    autolink=configure_autolink(
                        rendered_dir,
                        locale,
                        templates,
                        render_template,
                        rendered_dir,
                    ),
                    strings=localizations[locale],
                )
            )
            rendered.append(rendered_path)
            return rendered_path

    return render_template


@click.group()
def simplesitesystem():
    pass


@simplesitesystem.command()
@click.argument("source_dir")
@click.argument("output_dir")
def build(source_dir: str, output_dir: str) -> None:
    env: Environment = Environment(
        loader=FileSystemLoader(source_dir), trim_blocks=True, lstrip_blocks=True
    )

    # Delete contents of output directory, if it exists
    shutil.rmtree(os.path.join(output_dir, "."), ignore_errors=True)

    templates: list[Template] = [
        env.get_template(path) for path in env.list_templates(extensions="jinja")
    ]

    if os.path.isfile(STRINGS_PATH):
        localizations: Localizations = read_localizations(STRINGS_PATH)

        primary_locale: str = next(iter(localizations.keys()))  # en
        primary_locale_dir: str = os.path.join(
            output_dir, primary_locale
        )  # output/en

        render_template: RenderTemplate = configure_renderer(
            localizations, templates, source_dir, output_dir
        )

        for locale in localizations:
            locale_dir: str = os.path.join(output_dir, locale)  # output/jp

            if locale == primary_locale:
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
                        primary_locale_dir,
                    )

            for template in templates:
                render_template(template, locale)


if __name__ == '__main__':
    simplesitesystem()
