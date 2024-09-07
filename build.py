import os
import bs4
import markdown
import yaml
from typing import Any

GENERATED_PAGES_DIR = './pages'
MD_POSTS_DIR = './posts'
INDEX_TEMPLATE_PAGE_PATH = './templates/index.html'
POST_TEMPLATE_PAGE_PATH = './templates/post.html'
POST_NAVIGATION_TEMPLATE_PATH = './templates/post-navigation.html'
POST_ENTRY_TEMPLATE_PATH = './templates/post-entry.html'
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

    with open(POST_ENTRY_TEMPLATE_PATH, 'r') as template_file:
        post_entry_html: str = template_file.read()

    post_entries_html: str = ''

    for post in posts:
        post_entry_html_copy: str = post_entry_html
        post_entry_html_copy = post_entry_html_copy.replace('{{ post_id }}', f'post-{post["id"]}')
        post_entry_html_copy = post_entry_html_copy.replace('{{ post_title }}', post['title'])
        post_entry_html_copy = post_entry_html_copy.replace('{{ post_description }}', post['description'])
        post_entry_html_copy = post_entry_html_copy.replace('{{ post_date }}', post['date'].strftime("%B %d, %Y"))
        post_entry_html_copy = post_entry_html_copy.replace('{{ post_url }}', post['url'])
        post_entries_html += post_entry_html_copy + '\n'


    # replace {{ post_entry_list }} with the post_entry_html
    index_template_html = index_template_html.replace('{{ post_entry_list }}', post_entries_html)

    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(index_template_html, 'html.parser')

    # format the soup and write it back to the file
    formatter = bs4.formatter.HTMLFormatter(indent=4)
    soup = soup.prettify(formatter=formatter)

    with open(INDEX_PAGE_PATH, 'w') as index_page_file:
        index_page_file.write(str(soup))

def generate_post_page(
        previous_post: dict[str, str | int] | None,
        post: dict[str, str | int],
        next_post: dict[str, str | int] | None
    ) -> None:
    with open(POST_TEMPLATE_PAGE_PATH, 'r') as template_file:
        soup = bs4.BeautifulSoup(template_file, 'html.parser')

    # make a template html instead of this
    post_div = soup.new_tag('article')
    post_div['class'] = 'post'
    post_div['id'] = f"post-{post['id']}"

    post_header = soup.new_tag('header')

    post_title:bs4.Tag = soup.new_tag('h1')
    post_title['class'] = 'post-title'
    post_title.string = post['title']
    post_header.append(post_title)

    post_date:bs4.Tag = soup.new_tag('time')
    post_date['datetime'] = post['date'].strftime("%Y-%m-%d")
    post_date.string = post['date'].strftime("%B %d, %Y")
    post_date['class'] = 'post-date'
    post_header.append(post_date)

    post_div.append(post_header)
    post_div.append(soup.new_tag('hr'))

    with open(post['path'], 'r') as post_markdown_file:
        post_markdown_content: str = post_markdown_file.read()
        post_html_content: str = markdown.markdown(
            post_markdown_content, 
            extensions=['fenced_code', 'tables', 'meta']
        )

    post_div.append(bs4.BeautifulSoup(post_html_content, 'html.parser'))
    soup.find('div', id="post-content").append(post_div)

    # Inject the post navigation
    with open(POST_NAVIGATION_TEMPLATE_PATH, 'r') as template_file:
        post_navigation_html = template_file.read()

    if previous_post:
        post_navigation_html = post_navigation_html.replace('{{ previous_post_title }}', previous_post['title'])
        post_navigation_html = post_navigation_html.replace('{{ previous_post_url }}', f'/{previous_post["url"]}')
        post_navigation_html = post_navigation_html.replace('{{ previous_post_date }}', previous_post['date'].strftime("%B %d, %Y"))
    else:
        post_navigation_html = post_navigation_html.replace('{{ previous_post_title }}', '')
        post_navigation_html = post_navigation_html.replace('{{ previous_post_url }}', '')
        post_navigation_html = post_navigation_html.replace('{{ previous_post_date }}', '')

    if next_post:
        post_navigation_html = post_navigation_html.replace('{{ next_post_title }}', next_post['title'])
        post_navigation_html = post_navigation_html.replace('{{ next_post_url }}', f'/{next_post["url"]}')
        post_navigation_html = post_navigation_html.replace('{{ next_post_date }}', next_post['date'].strftime("%B %d, %Y"))
    else:
        post_navigation_html = post_navigation_html.replace('{{ next_post_title }}', '')
        post_navigation_html = post_navigation_html.replace('{{ next_post_url }}', '')
        post_navigation_html = post_navigation_html.replace('{{ next_post_date }}', '')

    soup.find('div', id="post-navigation").append(bs4.BeautifulSoup(post_navigation_html, 'html.parser'))

    # format the soup and write it back to the file
    formatter = bs4.formatter.HTMLFormatter(indent=4)
    soup = soup.prettify(formatter=formatter)

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(f'./pages/{post["url"]}/index.html'), exist_ok=True)

    with open(f'./pages/{post["url"]}/index.html', 'w') as post_page_file:
        post_page_file.write(str(soup))

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
    post_id: int = 0

    for metadata in post_metas:
        metadata['id'] = post_id

        # Generate the HTML page for the post
        generate_post_page(
            previous_post=post_metas[post_id + 1 ] if post_id + 1 < len(post_metas) else None,
            post=metadata,
            next_post=post_metas[post_id - 1] if post_id - 1 >= 0 else None
        )

        post_id += 1

    # Insert posts list into the index.html
    generate_index_page(post_metas)