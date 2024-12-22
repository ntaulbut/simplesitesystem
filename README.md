# Simple Site System
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Link all templates in a folder
Use `autolink("[Directory Name]")` to get a tuple with the url, the title (`<title>`), and the description (`<meta name="description">`), of each page in the directory.
```jinja
<ul>
{% for url, title, description in autolink("blog") %}
    <li>
        <a href="{{ url }}">{{ title }}</a>: {{ description }}
    </li>
{% endfor %}
</ul>
```

## Code highlighting
```jinja
<p>
{% code "python" %}
def main():
    print("Hello, world")
{% endcode %}
</p>
```
### Setup
```jinja
<head>
    <style>
    {{ code_style("one-dark") }}
    </style>
</head>
```
