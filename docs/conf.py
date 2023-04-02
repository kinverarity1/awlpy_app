project_name = "awlpy_app"


from pkg_resources import get_distribution

release = get_distribution(project_name).version
version = ".".join(release.split(".")[:2])

project = f"{project_name} documentation v{version}"
copyright = "2023"
author = "Kent Inverarity"


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "nbsphinx",
]

templates_path = ["_templates"]

source_suffix = ".rst"
master_doc = "index"
language = None

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = None

html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": f"https://github.com/kinverarity1/{project_name}",
            "icon": "fab fa-github",
        },
    ],
    "show_nav_level": 2,
    "show_toc_level": 2,
    "use_edit_page_button": True,
    "navbar_start": ["navbar-logo"],
    # "navbar_center": ["navbar-nav"],
    "navbar_center": [],
    "navbar_end": ["navbar-icon-links"],
}

html_context = {
    "github_user": "kinverarity1",
    "github_repo": project_name,
    "github_version": "main",
    "doc_path": "docs",
}

html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]


html_sidebars = {
    # "**": ["search-field", "sidebar-nav-bs", "sidebar-ethical-ads"]
    # "**": ["search-field", "sidebar-nav-bs",]
    "**": [
        "search-field",
        "navbar-nav",
        "parent_links",
    ]
}


intersphinx_mapping = {
    "python": ("http://docs.python.org/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "sa_gwdata": ("https://python-sa-gwdata.readthedocs.io/en/latest/", None),
    "sageodata_db": (
        "http://gitlab.io/dew-waterscience/sageodata_db",
        "sageodata_db.objects.inv",
    ),
    "dew_gwdata": (
        "http://gitlab.io/dew-waterscience/dew_gwdata",
        "dew_gwdata.objects.inv",
    ),
    "wrap_technote": (
        "http://gitlab.io/dew-waterscience/wrap_technote",
        "wrap_technote.objects.inv",
    ),
    "waterkennect": (
        "http://gitlab.io/dew-waterscience/waterkennect",
        "waterkennect.objects.inv",
    ),
}
intersphinx_cache_limit = 1

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


def setup(app):
    app.add_css_file("custom.css")
