#!/usr/bin/env python3
"""
Build static Facebook archive for Deemable Tech
Converts Facebook data export to a static HTML site
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import html
import re

# Paths
ARCHIVE_DIR = Path("archive/this_profile's_activity_across_facebook")
OUTPUT_DIR = Path(".")
MEDIA_OUTPUT = OUTPUT_DIR / "media"

def decode_facebook_text(text):
    """Facebook exports text in latin-1 encoded as UTF-8, decode it properly"""
    if text is None:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text

def format_timestamp(ts):
    """Convert Unix timestamp to readable date"""
    if not ts:
        return ""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%B %d, %Y at %I:%M %p")

def format_date_short(ts):
    """Convert Unix timestamp to short date"""
    if not ts:
        return ""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%b %d, %Y")

def linkify(text):
    """Convert URLs in text to clickable links"""
    if not text:
        return ""
    url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)

def load_json(filepath):
    """Load and parse JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def get_media_path(uri):
    """Convert archive URI to output media path"""
    if not uri:
        return None
    # Extract just the filename and put in media folder
    filename = Path(uri).name
    return f"media/{filename}"

def copy_media_files():
    """Copy all media files to output directory"""
    MEDIA_OUTPUT.mkdir(exist_ok=True)

    media_source = ARCHIVE_DIR / "posts" / "media"
    if media_source.exists():
        for root, dirs, files in os.walk(media_source):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webp')):
                    src = Path(root) / file
                    dst = MEDIA_OUTPUT / file
                    if not dst.exists():
                        shutil.copy2(src, dst)
                        print(f"Copied: {file}")

def load_posts():
    """Load all posts from profile_posts JSON"""
    posts_file = ARCHIVE_DIR / "posts" / "profile_posts_1.json"
    data = load_json(posts_file)
    if not data:
        return []

    posts = []
    for item in data:
        post = {
            'timestamp': item.get('timestamp', 0),
            'title': decode_facebook_text(item.get('title', '')),
            'text': '',
            'media': [],
            'external_url': None
        }

        # Extract post text
        for d in item.get('data', []):
            if 'post' in d:
                post['text'] = decode_facebook_text(d['post'])
                break

        # Extract media and external links
        for attachment in item.get('attachments', []):
            for d in attachment.get('data', []):
                if 'media' in d:
                    media = d['media']
                    post['media'].append({
                        'uri': media.get('uri'),
                        'description': decode_facebook_text(media.get('description', ''))
                    })
                if 'external_context' in d:
                    post['external_url'] = d['external_context'].get('url')

        posts.append(post)

    # Sort by timestamp descending (newest first)
    posts.sort(key=lambda x: x['timestamp'], reverse=True)
    return posts

def load_albums():
    """Load all photo albums"""
    albums = []
    album_dir = ARCHIVE_DIR / "posts" / "album"

    if not album_dir.exists():
        return albums

    for album_file in sorted(album_dir.glob("*.json")):
        data = load_json(album_file)
        if not data:
            continue

        album = {
            'name': decode_facebook_text(data.get('name', 'Untitled Album')),
            'description': decode_facebook_text(data.get('description', '')),
            'photos': [],
            'cover': None
        }

        for photo in data.get('photos', []):
            album['photos'].append({
                'uri': photo.get('uri'),
                'description': decode_facebook_text(photo.get('description', '')),
                'timestamp': photo.get('creation_timestamp', 0)
            })

        if data.get('cover_photo'):
            album['cover'] = data['cover_photo'].get('uri')
        elif album['photos']:
            album['cover'] = album['photos'][0]['uri']

        if album['photos']:
            albums.append(album)

    return albums

def generate_css():
    """Generate Facebook-inspired CSS"""
    return '''
:root {
    --fb-blue: #1877f2;
    --fb-blue-dark: #166fe5;
    --bg-primary: #f0f2f5;
    --bg-card: #ffffff;
    --text-primary: #050505;
    --text-secondary: #65676b;
    --border-color: #dddfe2;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.34;
    font-size: 15px;
}

.archive-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    padding: 12px 20px;
    font-size: 14px;
}

.archive-banner a {
    color: white;
    text-decoration: underline;
}

header {
    background: var(--fb-blue);
    padding: 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-content {
    max-width: 900px;
    margin: 0 auto;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.header-content h1 {
    color: white;
    font-size: 20px;
    font-weight: 700;
}

.header-content h1 a {
    color: white;
    text-decoration: none;
}

nav {
    background: var(--bg-card);
    border-bottom: 1px solid var(--border-color);
}

nav ul {
    max-width: 900px;
    margin: 0 auto;
    list-style: none;
    display: flex;
    gap: 0;
}

nav a {
    display: block;
    padding: 16px 20px;
    color: var(--text-secondary);
    text-decoration: none;
    font-weight: 600;
    font-size: 15px;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
}

nav a:hover, nav a.active {
    color: var(--fb-blue);
    border-bottom-color: var(--fb-blue);
}

main {
    max-width: 680px;
    margin: 0 auto;
    padding: 20px 16px;
}

.cover-section {
    position: relative;
    margin-bottom: 20px;
    background: var(--bg-card);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
}

.cover-photo {
    width: 100%;
    height: 250px;
    object-fit: cover;
}

.profile-section {
    display: flex;
    align-items: flex-end;
    padding: 0 20px 20px;
    margin-top: -60px;
    position: relative;
}

.profile-pic {
    width: 168px;
    height: 168px;
    border-radius: 50%;
    border: 4px solid white;
    object-fit: cover;
    box-shadow: var(--shadow);
}

.profile-info {
    margin-left: 20px;
    padding-bottom: 10px;
}

.profile-info h2 {
    font-size: 32px;
    font-weight: 700;
}

.profile-info p {
    color: var(--text-secondary);
    margin-top: 4px;
}

.post {
    background: var(--bg-card);
    border-radius: 8px;
    margin-bottom: 16px;
    box-shadow: var(--shadow);
}

.post-header {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    gap: 12px;
}

.post-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
}

.post-meta h3 {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
}

.post-meta .date {
    font-size: 13px;
    color: var(--text-secondary);
}

.post-content {
    padding: 0 16px 12px;
}

.post-content p {
    white-space: pre-wrap;
    word-wrap: break-word;
}

.post-content a {
    color: var(--fb-blue);
    text-decoration: none;
}

.post-content a:hover {
    text-decoration: underline;
}

.post-media {
    width: 100%;
}

.post-media img {
    width: 100%;
    display: block;
}

.post-link {
    margin: 0 16px 12px;
    padding: 12px;
    background: var(--bg-primary);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.post-link a {
    color: var(--text-primary);
    text-decoration: none;
    font-size: 14px;
    word-break: break-all;
}

.post-link a:hover {
    text-decoration: underline;
}

/* Albums page */
.albums-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
}

.album-card {
    background: var(--bg-card);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
    text-decoration: none;
    color: inherit;
    transition: transform 0.2s;
}

.album-card:hover {
    transform: translateY(-2px);
}

.album-cover {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.album-info {
    padding: 12px;
}

.album-info h3 {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 4px;
}

.album-info p {
    font-size: 13px;
    color: var(--text-secondary);
}

/* Album detail page */
.album-header {
    background: var(--bg-card);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: var(--shadow);
}

.album-header h2 {
    font-size: 24px;
    margin-bottom: 8px;
}

.photos-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 4px;
}

.photo-item {
    position: relative;
    aspect-ratio: 1;
    overflow: hidden;
}

.photo-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    cursor: pointer;
    transition: transform 0.2s;
}

.photo-item:hover img {
    transform: scale(1.05);
}

/* Lightbox */
.lightbox {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.95);
    z-index: 1000;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

.lightbox.active {
    display: flex;
}

.lightbox img {
    max-width: 90%;
    max-height: 80%;
    object-fit: contain;
}

.lightbox-caption {
    color: white;
    text-align: center;
    padding: 20px;
    max-width: 600px;
}

.lightbox-close {
    position: absolute;
    top: 20px;
    right: 20px;
    color: white;
    font-size: 30px;
    cursor: pointer;
    background: none;
    border: none;
    padding: 10px;
}

/* Footer */
footer {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-secondary);
    font-size: 13px;
}

footer a {
    color: var(--text-secondary);
}

/* Responsive */
@media (max-width: 600px) {
    .profile-section {
        flex-direction: column;
        align-items: center;
        text-align: center;
        margin-top: -40px;
    }

    .profile-pic {
        width: 120px;
        height: 120px;
    }

    .profile-info {
        margin-left: 0;
        margin-top: 12px;
    }

    .profile-info h2 {
        font-size: 24px;
    }

    nav ul {
        justify-content: center;
    }

    nav a {
        padding: 12px 16px;
        font-size: 14px;
    }
}
'''

def generate_header(active_page="posts"):
    """Generate page header HTML"""
    return f'''
    <div class="archive-banner">
        This is an archived copy of the Deemable Tech Facebook Page.
        <a href="/">Visit Deemable Tech</a>
    </div>
    <header>
        <div class="header-content">
            <h1><a href="/facebook/">Deemable Tech Archive</a></h1>
        </div>
    </header>
    <nav>
        <ul>
            <li><a href="/facebook/" class="{'active' if active_page == 'posts' else ''}">Posts</a></li>
            <li><a href="/facebook/photos.html" class="{'active' if active_page == 'photos' else ''}">Photos</a></li>
            <li><a href="/facebook/about.html" class="{'active' if active_page == 'about' else ''}">About</a></li>
        </ul>
    </nav>
'''

def generate_footer():
    """Generate page footer HTML"""
    return '''
    <footer>
        <p>This archive was created from a Facebook data export.</p>
        <p>Original content &copy; Deemable Tech. Archive generated January 2026.</p>
    </footer>
'''

def generate_post_html(post, profile_pic_path):
    """Generate HTML for a single post"""
    media_html = ""
    for m in post['media']:
        media_path = get_media_path(m['uri'])
        if media_path:
            media_html += f'''
            <div class="post-media">
                <img src="{media_path}" alt="{html.escape(m['description'])}" loading="lazy">
            </div>
            '''

    link_html = ""
    if post['external_url']:
        link_html = f'''
        <div class="post-link">
            <a href="{html.escape(post['external_url'])}" target="_blank" rel="noopener">
                {html.escape(post['external_url'])}
            </a>
        </div>
        '''

    text_html = ""
    if post['text']:
        text_html = f'<p>{linkify(html.escape(post["text"]))}</p>'

    return f'''
    <article class="post">
        <div class="post-header">
            <img src="{profile_pic_path}" alt="Deemable Tech" class="post-avatar">
            <div class="post-meta">
                <h3>Deemable Tech</h3>
                <span class="date">{format_timestamp(post['timestamp'])}</span>
            </div>
        </div>
        <div class="post-content">
            {text_html}
        </div>
        {media_html}
        {link_html}
    </article>
    '''

def generate_index_page(posts, albums, profile_pic_path, cover_photo_path):
    """Generate main index page with posts"""
    posts_html = ""
    for post in posts:
        posts_html += generate_post_html(post, profile_pic_path)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deemable Tech - Facebook Archive</title>
    <style>{generate_css()}</style>
</head>
<body>
    {generate_header('posts')}

    <main>
        <div class="cover-section">
            <img src="{cover_photo_path}" alt="Cover photo" class="cover-photo">
            <div class="profile-section">
                <img src="{profile_pic_path}" alt="Deemable Tech" class="profile-pic">
                <div class="profile-info">
                    <h2>Deemable Tech</h2>
                    <p>Tech Tips &amp; Podcast</p>
                </div>
            </div>
        </div>

        {posts_html}
    </main>

    {generate_footer()}
</body>
</html>
'''

def generate_photos_page(albums, profile_pic_path):
    """Generate photos/albums listing page"""
    albums_html = ""
    for i, album in enumerate(albums):
        cover_path = get_media_path(album['cover']) if album['cover'] else "media/placeholder.jpg"
        albums_html += f'''
        <a href="album-{i}.html" class="album-card">
            <img src="{cover_path}" alt="{html.escape(album['name'])}" class="album-cover" loading="lazy">
            <div class="album-info">
                <h3>{html.escape(album['name'])}</h3>
                <p>{len(album['photos'])} photos</p>
            </div>
        </a>
        '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photos - Deemable Tech Facebook Archive</title>
    <style>{generate_css()}</style>
</head>
<body>
    {generate_header('photos')}

    <main>
        <div class="album-header">
            <h2>Photo Albums</h2>
        </div>
        <div class="albums-grid">
            {albums_html}
        </div>
    </main>

    {generate_footer()}
</body>
</html>
'''

def generate_album_page(album, index, profile_pic_path):
    """Generate individual album page"""
    photos_html = ""
    for photo in album['photos']:
        photo_path = get_media_path(photo['uri'])
        if photo_path:
            caption = html.escape(photo['description']) if photo['description'] else ''
            escaped_caption = caption.replace("'", "\\'")
            photos_html += f'''
            <div class="photo-item" onclick="openLightbox('{photo_path}', '{escaped_caption}')">
                <img src="{photo_path}" alt="{caption}" loading="lazy">
            </div>
            '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(album['name'])} - Deemable Tech Facebook Archive</title>
    <style>{generate_css()}</style>
</head>
<body>
    {generate_header('photos')}

    <main>
        <div class="album-header">
            <h2>{html.escape(album['name'])}</h2>
            <p>{len(album['photos'])} photos</p>
        </div>
        <div class="photos-grid">
            {photos_html}
        </div>
    </main>

    <div class="lightbox" id="lightbox">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <img src="" alt="" id="lightbox-img">
        <div class="lightbox-caption" id="lightbox-caption"></div>
    </div>

    {generate_footer()}

    <script>
    function openLightbox(src, caption) {{
        document.getElementById('lightbox-img').src = src;
        document.getElementById('lightbox-caption').textContent = caption;
        document.getElementById('lightbox').classList.add('active');
        document.body.style.overflow = 'hidden';
    }}

    function closeLightbox() {{
        document.getElementById('lightbox').classList.remove('active');
        document.body.style.overflow = '';
    }}

    document.getElementById('lightbox').addEventListener('click', function(e) {{
        if (e.target === this) closeLightbox();
    }});

    document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape') closeLightbox();
    }});
    </script>
</body>
</html>
'''

def generate_about_page(profile_pic_path):
    """Generate about page"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About - Deemable Tech Facebook Archive</title>
    <style>{generate_css()}</style>
</head>
<body>
    {generate_header('about')}

    <main>
        <article class="post">
            <div class="post-header">
                <img src="{profile_pic_path}" alt="Deemable Tech" class="post-avatar">
                <div class="post-meta">
                    <h3>About This Archive</h3>
                </div>
            </div>
            <div class="post-content">
                <p>This is an archived copy of the Deemable Tech Facebook Page.</p>
                <p>Deemable Tech was a technology podcast and news site that ran from 2011-2016, providing tech tips, reviews, and discussions about the latest in consumer technology.</p>
                <p>This archive preserves the posts, photos, and content that was shared on the Facebook Page during that time.</p>
                <p>Visit <a href="/">deemable.rayhollister.com</a> for the main Deemable Tech archive.</p>
            </div>
        </article>
    </main>

    {generate_footer()}
</body>
</html>
'''

def main():
    print("Building Deemable Tech Facebook Archive...")

    # Copy media files
    print("\nCopying media files...")
    copy_media_files()

    # Load data
    print("\nLoading posts...")
    posts = load_posts()
    print(f"Found {len(posts)} posts")

    print("\nLoading albums...")
    albums = load_albums()
    print(f"Found {len(albums)} albums")

    # Find profile pic and cover photo
    profile_pic_path = "media/186683038016677.jpg"  # Default profile pic
    cover_photo_path = "media/459089629564822.jpg"  # Default cover photo

    # Check for profile pictures album
    for album in albums:
        if 'profile' in album['name'].lower() and album['photos']:
            profile_pic_path = get_media_path(album['photos'][0]['uri'])
            break

    # Check for cover photos album
    for album in albums:
        if 'cover' in album['name'].lower() and album['photos']:
            cover_photo_path = get_media_path(album['photos'][0]['uri'])
            break

    print(f"\nUsing profile pic: {profile_pic_path}")
    print(f"Using cover photo: {cover_photo_path}")

    # Generate pages
    print("\nGenerating index page...")
    with open(OUTPUT_DIR / "index.html", 'w', encoding='utf-8') as f:
        f.write(generate_index_page(posts, albums, profile_pic_path, cover_photo_path))

    print("Generating photos page...")
    with open(OUTPUT_DIR / "photos.html", 'w', encoding='utf-8') as f:
        f.write(generate_photos_page(albums, profile_pic_path))

    print("Generating album pages...")
    for i, album in enumerate(albums):
        with open(OUTPUT_DIR / f"album-{i}.html", 'w', encoding='utf-8') as f:
            f.write(generate_album_page(album, i, profile_pic_path))

    print("Generating about page...")
    with open(OUTPUT_DIR / "about.html", 'w', encoding='utf-8') as f:
        f.write(generate_about_page(profile_pic_path))

    print("\n✓ Archive built successfully!")
    print(f"  - {len(posts)} posts")
    print(f"  - {len(albums)} albums")
    print(f"  - Files written to: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    main()
