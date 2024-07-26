from jinja2 import nodes
from jinja2.ext import Extension, Markup
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.formatters import HtmlFormatter


class CodeBlockExtension(Extension):
    tags = {"code"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        # now we parse a single expression that is used as cache key.
        # args = [parser.parse_expression()]

        # if there is a comma, the user provided a timeout.  If not use
        # None as second parameter.
        # if parser.stream.skip_if("comma"):
        #     args.append(parser.parse_expression())
        # else:
        #     args.append(nodes.Const(None))

        body = parser.parse_statements(("name:endcode",), drop_needle=True)

        return nodes.CallBlock(self.call_method("_highlight"), [], [], body).set_lineno(
            lineno
        )

    # noinspection PyMethodMayBeStatic
    def _highlight(self, caller):
        body = caller()
        markup = Markup(body)

        return highlight(markup, guess_lexer(markup), HtmlFormatter())
