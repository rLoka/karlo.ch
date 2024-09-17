import os
import bs4
import markdown
import yaml
import jinja2
from typing import Any

GENERATED_PAGES_DIR = './pages'
MD_POSTS_DIR = './posts'
INDEX_TEMPLATE_PAGE_PATH = './templates/index.html'
POST_TEMPLATE_PAGE_PATH = './templates/post.html'
INDEX_PAGE_PATH = './pages/index.html'

def load_posts() -> list[str]:
    posts: list[str] = []
    for post in os.listdir(MD_POSTS_DIR):
        if post.endswith('.md'):
            posts.append(f"{MD_POSTS_DIR}/{post}")

    return posts

def extract_metadata(post_path: str) -> dict[str, Any]:
    with open(post_path, 'r') as file:
        lines = file.readlines()

    yaml_content = []
    inside_yaml = False

    for line in lines:
        if line.strip() == '---':
            if inside_yaml:
                break
            else:
                inside_yaml = True
        elif inside_yaml:
            yaml_content.append(line)

    yaml_content.append(f'path: {post_path}\n')

    yaml_string = ''.join(yaml_content)
    return yaml.safe_load(yaml_string)

def generate_index_page(posts: list[dict[str, Any]]) -> None:

    with open(INDEX_TEMPLATE_PAGE_PATH, 'r') as template_file:
        index_template_html: str = template_file.read()

    index_template_html = jinja2.Template(index_template_html).render(posts=posts)

    with open(INDEX_PAGE_PATH, 'w') as index_page_file:
        index_page_file.write(index_template_html)

def generate_post_page(
        post: dict[str, str | int],
    ) -> None:

    with open(POST_TEMPLATE_PAGE_PATH, 'r') as template_file:
        post_template_html: str = template_file.read()

    # Use jinja2 to render the post template
    post_template_html = jinja2.Template(post_template_html).render(post=post)

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(f'./pages/{post["url"]}/index.html'), exist_ok=True)

    with open(f'./pages/{post["url"]}/index.html', 'w') as post_page_file:
        post_page_file.write(post_template_html)

if __name__ == "__main__":
    # Make a copy of templates directory and rename it to pages
    os.system('rm -rf ./pages')
    os.system('cp -r ./templates ./pages')

    post_metas: list[dict[str, Any]] = []
    for post_path in load_posts():
        post_metadata: dict[str, Any] = extract_metadata(
            post_path=post_path
        )
        post_metas.append(post_metadata)
        print(post_metadata)

    # sort post_metas by date
    post_metas.sort(key=lambda x: x['date'], reverse=True)

    for id, metadata in enumerate(post_metas):
        metadata['id'] = id
        metadata['previous'] = post_metas[id + 1] if id + 1 < len(post_metas) else None
        metadata['next'] = post_metas[id - 1] if id - 1 >= 0 else None

        with open(metadata['path'], 'r') as post_markdown_file:
            metadata['content'] = markdown.markdown(
                post_markdown_file.read(), 
                extensions=['fenced_code', 'tables', 'meta']
            )     

        # Generate the HTML page for the post
        generate_post_page(post=metadata)

    # Insert posts list into the index.html
    generate_index_page(post_metas)