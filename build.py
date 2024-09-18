import os
import markdown
import yaml
import jinja2
import datetime
from dataclasses import dataclass, field
from typing import Any
from glob import glob

GENERATED_PAGES_DIR = './pages'
MD_POSTS_DIR = './posts'
INDEX_TEMPLATE_PAGE_PATH = './templates/index.html'
POST_TEMPLATE_PAGE_PATH = './templates/post.html'
INDEX_PAGE_PATH = './pages/index.html'

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

def load_post(post_path: str) -> Post:
    with open(post_path, 'r') as file:
        content = file.read()
    
    metadata = extract_post_metadata(post_path)
    
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

def load_posts(posts_dir: str = MD_POSTS_DIR) -> list[Post]:
    # Load all posts from the posts directory and sort them by date
    posts: list[Post] = sorted(
        map(load_post, glob(os.path.join(posts_dir, '*', '*.md'))),
        key=lambda post: post.date
    )
    
    for i, post in enumerate(posts):
        post.id = i
        post.next = posts[i+1] if i < len(posts) - 1 else None
        post.previous = posts[i-1] if i > 0 else None

    return posts

def extract_post_metadata(post_path: str) -> dict[str, Any]:
    with open(post_path, 'r') as file:
        content = file.read().split('---', 2)    
    
    return yaml.safe_load(content[1].strip()) if len(content) >= 2 else {}

def render_index_page(posts: list[Post]) -> None:
    with open(INDEX_TEMPLATE_PAGE_PATH, 'r') as template_file:
        index_template_html: str = template_file.read()

    index_template_html = jinja2.Template(index_template_html).render(posts=posts)

    with open(INDEX_PAGE_PATH, 'w') as index_page_file:
        index_page_file.write(index_template_html)

def render_post_page(post: Post) -> None:
    with open(POST_TEMPLATE_PAGE_PATH, 'r') as template_file:
        post_template_html: str = template_file.read()

    # Use jinja2 to render the post template
    post_template_html = jinja2.Template(post_template_html).render(post=post)

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(f'./pages/{post.url}/index.html'), exist_ok=True)

    with open(f'./pages/{post.url}/index.html', 'w') as post_page_file:
        post_page_file.write(post_template_html)

if __name__ == "__main__":
    # Make a copy of templates directory and rename it to pages
    os.system('rm -rf ./pages')
    os.system('cp -r ./templates ./pages')

    posts: list[Post] = load_posts()

    # Insert posts list into the index.html
    render_index_page(posts=posts)

    for post in posts:
        # Generate the HTML page for the post
        render_post_page(post=post)