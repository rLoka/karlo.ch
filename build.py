import os
import shutil
import pathlib
import markdown
import yaml
import jinja2
import datetime
from dataclasses import dataclass, field
from typing import Any
from glob import glob

@dataclass
class Post:
    author: str = ''
    content: str = ''
    date: str = ''
    description: str = ''
    id: int = 0
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    title: str = ''
    url: str = ''

class Paula:
    def __init__(self, config_path: str = './config.yaml'):
        self._config: dict[str, Any] = self._load_config(config_path)
        self._theme_path: str = os.path.join(
            self._config.get("templates_directory", "./templates"), 
            self._config.get("template", "pear")
        )
        self._pages_path: str = self._config.get("static_pages_directory", "./pages")
        self._posts_path: str = self._config.get("posts_directory", "./posts")
        self._post_template_file_path: str = os.path.join(
            self._theme_path, 
            self._config.get("post_template_file", "post.html")
        )
        self._posts: list[Post] = []
        if self._config.get('render_posts', True):
            self._posts = self._load_posts()

    def _load_config(self, config_path: str) -> dict[str, Any]:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _load_post(self, post_path: str) -> Post:
        with open(post_path, 'r') as file:
            content = file.read()
        
        metadata = self._extract_post_metadata(post_path)
        
        return Post(
            content=markdown.markdown(content, extensions=['fenced_code', 'tables', 'meta']),
            date=metadata.get('date', datetime.datetime.now().strftime('%Y-%m-%d')),
            title=metadata.get('title', 'Untitled'),
            description=metadata.get('description', 'No description'),
            url=metadata.get('url', ''),
            tags=metadata.get('tags', []),
            keywords=metadata.get('keywords', []),
            author=metadata.get('author', '')
        )

    def _load_posts(self) -> list[Post]:
        # Load all posts from the posts directory and sort them by date
        posts: list[Post] = sorted(
            map(self._load_post, glob(os.path.join(self._posts_path, '*', '*.md'))),
            key=lambda post: post.date
        )
        
        for i, post in enumerate(posts):
            post.id = i
            post.next = posts[i+1] if i < len(posts) - 1 else None
            post.previous = posts[i-1] if i > 0 else None

        return posts

    def _extract_post_metadata(self, post_path: str) -> dict[str, Any]:
        with open(post_path, 'r') as file:
            content = file.read().split('---', 2)    
        
        return yaml.safe_load(content[1].strip()) if len(content) >= 2 else {}

    def _render_post_page(self, post: Post) -> None:
        with open(self._post_template_file_path, 'r') as template_file:
            post_template_html: str = template_file.read()

        # Use jinja2 to render the post template
        post_template_html = jinja2.Template(post_template_html).render(
            post=post,
            **self._config['context']
        )

        # Create directories if they don't exist
        os.makedirs(
            os.path.dirname(f'{self._pages_path}/{post.url}/index.html'), 
            exist_ok=True
        )

        with open(f'{self._pages_path}/{post.url}/index.html', 'w') as post_page_file:
            post_page_file.write(post_template_html)

    def _render_posts(self):        
        for post in self._posts:
            self._render_post_page(post=post)

    def _render_pages(self):
        # traverse all html files in pages directory and render them using jinja, recursively
        for root, dirs, files in os.walk(self._pages_path):
            for file in files:
                if file.endswith('.html') and \
                    not self._config.get('post_template_file') in os.path.join(root, file):
                    with open(os.path.join(root, file), 'r') as template_file:
                        template_html: str = template_file.read()

                    template_html = jinja2.Template(template_html).render(
                        posts=self._posts,
                        **self._config['context']
                    )

                    with open(os.path.join(root, file), 'w') as rendered_file:
                        rendered_file.write(template_html)

    def _create_pages_directory(self):
        shutil.copytree(src=self._theme_path, dst=self._pages_path)

    def clean(self) -> None:
        shutil.rmtree(
            self._config.get("static_pages_directory", "./pages")
        )

    def build(self) -> None:
        self.clean()
        self._create_pages_directory()
        self._render_pages()

        if self._config.get('render_posts', True):
            self._render_posts()

if __name__ == "__main__":
    paula: Paula = Paula()
    paula.build()
