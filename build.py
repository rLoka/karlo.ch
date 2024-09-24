import os
import shutil
import pathlib
import markdown
import yaml
import jinja2
import datetime
import logging
from dataclasses import dataclass, field
from typing import Any, List, Dict
from glob import glob

# Constants
CONFIG_PATH = './config.yaml'
DEFAULT_TEMPLATE = 'pear'
DEFAULT_STATIC_PAGES_DIR = './pages'
DEFAULT_POSTS_DIR = './posts'
DEFAULT_POST_TEMPLATE_FILE = 'post.html'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Post:
    author: str = ''
    content: str = ''
    date: str = ''
    description: str = ''
    id: int = 0
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    title: str = ''
    url: str = ''
    next: 'Post' = None
    previous: 'Post' = None

class Paula:
    def __init__(self, config_path: str = CONFIG_PATH):
        self._config: Dict[str, Any] = self._load_config(config_path)
        self._theme_path: str = os.path.join(
            self._config.get("templates_directory", "./templates"), 
            self._config.get("template", DEFAULT_TEMPLATE)
        )
        self._pages_path: str = self._config.get("static_pages_directory", DEFAULT_STATIC_PAGES_DIR)
        self._posts_path: str = self._config.get("posts_directory", DEFAULT_POSTS_DIR)
        self._post_template_file_path: str = os.path.join(
            self._theme_path, 
            self._config.get("post_template_file", DEFAULT_POST_TEMPLATE_FILE)
        )
        self._posts: List[Post] = []
        if self._config.get('render_posts', True):
            self._posts = self._load_posts()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}")
            raise

    def _load_post(self, post_path: str) -> Post:
        try:
            with open(post_path, 'r') as file:
                content = file.read()
        except FileNotFoundError:
            logging.error(f"Post file not found: {post_path}")
            raise

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

    def _load_posts(self) -> List[Post]:
        posts: List[Post] = sorted(
            map(self._load_post, glob(os.path.join(self._posts_path, '*', '*.md'))),
            key=lambda post: post.date
        )
        
        for i, post in enumerate(posts):
            post.id = i
            post.next = posts[i+1] if i < len(posts) - 1 else None
            post.previous = posts[i-1] if i > 0 else None

        return posts

    def _extract_post_metadata(self, post_path: str) -> Dict[str, Any]:
        try:
            with open(post_path, 'r') as file:
                content = file.read().split('---', 2)    
            return yaml.safe_load(content[1].strip()) if len(content) >= 2 else {}
        except FileNotFoundError:
            logging.error(f"Post file not found: {post_path}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing post metadata: {e}")
            raise

    def _render_post_page(self, post: Post) -> None:
        try:
            with open(self._post_template_file_path, 'r') as template_file:
                post_template_html: str = template_file.read()
        except FileNotFoundError:
            logging.error(f"Post template file not found: {self._post_template_file_path}")
            raise

        post_template_html = jinja2.Template(post_template_html).render(
            post=post,
            **self._config['context']
        )

        post_output_path = os.path.join(self._pages_path, post.url, 'index.html')
        os.makedirs(os.path.dirname(post_output_path), exist_ok=True)

        with open(post_output_path, 'w') as post_page_file:
            post_page_file.write(post_template_html)

    def _render_posts(self):        
        for post in self._posts:
            self._render_post_page(post=post)

    def _render_pages(self):
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
        try:
            shutil.copytree(src=self._theme_path, dst=self._pages_path)
        except FileExistsError:
            logging.warning(f"Pages directory already exists: {self._pages_path}")
        except Exception as e:
            logging.error(f"Error creating pages directory: {e}")
            raise

    def clean(self) -> None:
        try:
            shutil.rmtree(self._pages_path)
        except FileNotFoundError:
            logging.warning(f"Pages directory not found: {self._pages_path}")
        except Exception as e:
            logging.error(f"Error cleaning pages directory: {e}")
            raise

    def build(self) -> None:
        self.clean()
        self._create_pages_directory()
        self._render_pages()

        if self._config.get('render_posts', True):
            self._render_posts()

if __name__ == "__main__":
    paula: Paula = Paula()
    paula.build()
