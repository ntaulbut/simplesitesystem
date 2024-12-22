# Simple Site System
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Create a website just like you would in plain HTML, but using [Jinja](https://jinja.palletsprojects.com/) templates. For example:
```
blog/
├─ base.html.jinja
├─ ramen-recipe.html.jinja
img/
├─ catpicture.jpg
index.html.jinja
```

## Usage
To build the website: `simple build [Source Dir] [Output Dir]`.

To start a dev server: `simple dev [Source Dir] [Output Dir]`.


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

## Localisation
`simple build -s strings.toml src dist`

```toml
[en]
ramen_recipe_title = "My Ramen Recipe"

[jp]
ramen_recipe_title = "私のラーメンレシピ"
```
```jinja
<head>
    <title>{{ locale }}: {{ strings.ramen_recipe_title }}</title>
</head>
```

## Code highlighting
```jinja
<head>
    <style>
    {{ code_style("one-dark") }}
    </style>
</head>
```
```jinja
<p>
{% code "python" %}
def main():
    print("Hello, world")
{% endcode %}
</p>
```

