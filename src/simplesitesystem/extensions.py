from jinja2 import nodes
from jinja2.ext import Extension
from markupsafe import Markup
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


class CodeBlockExtension(Extension):
    tags = {"code"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        arg = parser.parse_expression()
        body = parser.parse_statements(("name:endcode",), drop_needle=True)
        return nodes.CallBlock(self.call_method("_highlight", [arg]), [], [], body).set_lineno(
            lineno
        )

    # noinspection PyMethodMayBeStatic
    def _highlight(self, lexer_alias, caller):
        body = caller()
        markup = Markup(body)
        return highlight(markup, get_lexer_by_name(lexer_alias), HtmlFormatter())
