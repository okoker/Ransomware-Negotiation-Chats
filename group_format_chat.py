#!/usr/bin/env python3
"""
Bulk Ransomware Chat Formatter
Processes entire GitHub repository of ransomware negotiation chats
"""

import json
import sys
import os
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, quote

# ============================================================================
# CONFIGURATION
# ============================================================================
REQUEST_DELAY = 1.5  # Delay between requests in seconds (configurable)
MAX_RETRIES = 3      # Maximum number of retry attempts for network requests

# Folders/files to skip (not ransomware negotiation data)
SKIP_ITEMS = {
    '.github',
    'parsers',
    'LICENSE',
    'README.md',
    'chat_index.json',
    'make_index.py',
    '.gitignore'
}


# ============================================================================
# HTML PARSER FOR GITHUB DIRECTORY LISTINGS
# ============================================================================
class GitHubDirParser(HTMLParser):
    """Parse GitHub repository directory listings"""

    def __init__(self):
        super().__init__()
        self.items = []
        self.in_file_list = False

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '')
            title = attrs_dict.get('title', '')

            # Look for directory or file links in GitHub's structure
            # Example: /DarkWebInformer/Ransomchats/tree/main/BlackBasta
            # Example: /DarkWebInformer/Ransomchats/blob/main/BlackBasta/20221011.json
            if '/tree/main/' in href or '/blob/main/' in href:
                item_name = href.split('/')[-1]
                if item_name and item_name not in SKIP_ITEMS:
                    item_type = 'dir' if '/tree/main/' in href else 'file'
                    self.items.append({
                        'name': item_name,
                        'type': item_type,
                        'href': href
                    })


# ============================================================================
# NETWORK UTILITIES
# ============================================================================
def fetch_with_retry(url, max_retries=MAX_RETRIES):
    """Fetch URL with retry logic"""
    for attempt in range(max_retries):
        try:
            time.sleep(REQUEST_DELAY)
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠ Retry {attempt + 1}/{max_retries - 1} for {url}")
                time.sleep(REQUEST_DELAY * 2)  # Longer delay on retry
            else:
                raise Exception(f"Failed to fetch {url} after {max_retries} attempts: {e}")


def convert_github_url_to_raw(url):
    """Convert GitHub blob URL to raw content URL"""
    if "github.com" in url and "/blob/" in url:
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        # URL-encode spaces and special characters in the path
        raw_url = raw_url.replace(" ", "%20")
        return raw_url
    return url


# ============================================================================
# GITHUB REPOSITORY PARSING
# ============================================================================
def github_url_to_api_url(github_url):
    """Convert GitHub web URL to API URL"""
    # Example: https://github.com/DarkWebInformer/Ransomchats/tree/main/Akira
    # To: https://api.github.com/repos/DarkWebInformer/Ransomchats/contents/Akira

    parts = github_url.split('/')
    if 'github.com' in github_url:
        # Find the owner and repo
        try:
            github_idx = parts.index('github.com')
            owner = parts[github_idx + 1]
            repo = parts[github_idx + 2]

            # Get the path after /tree/main/ or just after repo name
            if '/tree/main/' in github_url:
                path = github_url.split('/tree/main/')[-1]
            elif '/blob/main/' in github_url:
                path = github_url.split('/blob/main/')[-1]
            else:
                path = ''

            # URL-encode the path to handle spaces and special characters
            if path:
                path = quote(path)

            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            return api_url
        except (ValueError, IndexError):
            raise Exception(f"Could not parse GitHub URL: {github_url}")

    raise Exception(f"Invalid GitHub URL: {github_url}")


def get_directory_items(repo_url):
    """Get list of items (folders/files) from GitHub directory using API"""
    print(f"  📂 Fetching: {repo_url}")

    # Convert web URL to API URL
    api_url = github_url_to_api_url(repo_url)

    # Fetch from API
    json_content = fetch_with_retry(api_url)
    items_data = json.loads(json_content)

    # Parse API response
    items = []
    for item in items_data:
        item_type = 'dir' if item['type'] == 'dir' else 'file'
        items.append({
            'name': item['name'],
            'type': item_type,
            'href': item['html_url']
        })

    return items


def get_ransomware_groups(root_url):
    """Get list of ransomware group folders from root directory"""
    items = get_directory_items(root_url)

    # Filter for directories only, excluding skip items
    groups = [
        item['name'] for item in items
        if item['type'] == 'dir' and item['name'] not in SKIP_ITEMS
    ]

    return sorted(groups)


def get_json_files(group_url):
    """Get list of JSON files from a ransomware group folder"""
    items = get_directory_items(group_url)

    # Filter for JSON files only
    json_files = [
        item['name'] for item in items
        if item['type'] == 'file' and item['name'].endswith('.json')
    ]

    return sorted(json_files)


# ============================================================================
# HTML GENERATION (reused from format_chat.py)
# ============================================================================
def extract_date_from_chat(chat_id, messages=None):
    """
    Extract date from chat_id or messages.
    Handles formats like: 20221011, 20250425b, 20210518_3
    Falls back to first message timestamp if needed.
    """
    # Try to extract first 8 digits from chat_id
    date_match = re.match(r'(\d{8})', str(chat_id))
    if date_match:
        date_str = date_match.group(1)
        try:
            return datetime.strptime(date_str, "%Y%m%d").strftime("%B %d, %Y")
        except:
            pass

    # If that fails and we have messages, try to extract from first message
    if messages and len(messages) > 0:
        first_msg = messages[0]
        timestamp = first_msg.get("timestamp", "")
        # Messages might have dates in them, but typically just time
        # We'll try to use the chat_id digits we found earlier
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), "%Y%m%d").strftime("%B %d, %Y")
            except:
                pass

    # Last resort: return chat_id as-is
    return str(chat_id)


def format_timestamp(timestamp, chat_id, messages=None):
    """Format timestamp with date context"""
    if not timestamp:
        return ""
    date = extract_date_from_chat(chat_id, messages)
    return f"{date} at {timestamp}"


def generate_html(chat_data):
    """Generate polished HTML from chat data"""
    chat_id = chat_data.get("chat_id", "Unknown")
    messages = chat_data.get("messages", [])

    # Parse date for title
    chat_date = extract_date_from_chat(chat_id, messages)

    # Count messages first for header stats
    victim_count = sum(1 for msg in messages if msg.get("party", "").lower() == "victim")
    attacker_count = len(messages) - victim_count

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Session - {chat_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #ffffff;
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}

        .header {{
            background: #f8f9fa;
            color: #333;
            padding: 24px;
            border-bottom: 2px solid #dee2e6;
        }}

        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #212529;
        }}

        .header .subtitle {{
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 12px;
        }}

        .stats {{
            display: flex;
            gap: 20px;
            font-size: 13px;
            font-weight: 500;
            color: #495057;
        }}

        .stat {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .chat-container {{
            padding: 24px;
            max-height: 80vh;
            overflow-y: auto;
            background: #ffffff;
        }}

        .message {{
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid #f0f0f0;
        }}

        .message:last-child {{
            border-bottom: none;
        }}

        .message-header {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            gap: 10px;
        }}

        .party {{
            font-weight: 900;
            font-size: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .party.victim {{
            color: #0066cc;
        }}

        .party.attacker {{
            color: #dc3545;
        }}

        .timestamp {{
            font-size: 12px;
            color: #868e96;
        }}

        .message-content {{
            padding: 4px 0;
            margin-left: 24px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #495057;
        }}

        .message.victim .message-content {{
            color: #004085;
        }}

        .message.attacker .message-content {{
            color: #721c24;
        }}

        .footer {{
            padding: 12px 24px;
            background: #f8f9fa;
            text-align: center;
            font-size: 11px;
            color: #868e96;
            border-top: 1px solid #dee2e6;
        }}

        ::-webkit-scrollbar {{
            width: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #888;
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ransomware Negotiation Chat</h1>
            <div class="subtitle">Session ID: {chat_id} | Date: {chat_date}</div>
            <div class="stats">
                <div class="stat">
                    <span>Total Messages: {len(messages)}</span>
                </div>
                <div class="stat">
                    <span>Victim: {victim_count}</span>
                </div>
                <div class="stat">
                    <span>Attacker: {attacker_count}</span>
                </div>
            </div>
        </div>

        <div class="chat-container">
"""

    # Add messages
    for msg in messages:
        party = msg.get("party", "Unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        # Clean up content - remove extra blank lines
        content = re.sub(r'\n\s*\n+', '\n', content)
        content = content.strip()

        # Determine party class
        party_class = "victim" if party.lower() == "victim" else "attacker"

        # Format timestamp
        time_display = format_timestamp(timestamp, chat_id, messages) if timestamp else "No timestamp"

        html += f"""            <div class="message {party_class}">
                <div class="message-header">
                    <span class="party {party_class}">{party}</span>
                    <span class="timestamp">{time_display}</span>
                </div>
                <div class="message-content">{content}</div>
            </div>
"""

    html += f"""        </div>

        <div class="footer">
            Generated from JSON chat log
        </div>
    </div>
</body>
</html>
"""

    return html


# ============================================================================
# INDEX PAGE GENERATION
# ============================================================================
def generate_index_html(group_stats):
    """Generate index page with statistics for all groups"""
    total_chats = sum(count for _, count in group_stats)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ransomware Negotiation Chats - Index</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #ffffff;
            color: #333;
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}

        .header {{
            background: #f8f9fa;
            color: #333;
            padding: 32px;
            border-bottom: 2px solid #dee2e6;
        }}

        .header h1 {{
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #212529;
        }}

        .header .subtitle {{
            font-size: 16px;
            color: #6c757d;
        }}

        .content {{
            padding: 32px;
        }}

        .summary {{
            background: #e7f3ff;
            border-left: 4px solid #0066cc;
            padding: 16px 20px;
            margin-bottom: 32px;
            border-radius: 4px;
        }}

        .summary h2 {{
            font-size: 18px;
            font-weight: 600;
            color: #004085;
            margin-bottom: 8px;
        }}

        .summary p {{
            font-size: 14px;
            color: #004085;
        }}

        .groups {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }}

        .group-card {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 20px;
            transition: all 0.2s ease;
            text-decoration: none;
            color: inherit;
            display: block;
        }}

        .group-card:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
            border-color: #0066cc;
        }}

        .group-name {{
            font-size: 18px;
            font-weight: 700;
            color: #212529;
            margin-bottom: 8px;
        }}

        .group-count {{
            font-size: 14px;
            color: #6c757d;
        }}

        .group-count strong {{
            color: #0066cc;
            font-weight: 600;
        }}

        .footer {{
            padding: 16px 32px;
            background: #f8f9fa;
            text-align: center;
            font-size: 12px;
            color: #868e96;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ransomware Negotiation Chats</h1>
            <div class="subtitle">Archive of ransomware negotiations organized by threat actor groups</div>
        </div>

        <div class="content">
            <div class="summary">
                <h2>Collection Summary</h2>
                <p><strong>{len(group_stats)}</strong> ransomware groups indexed with <strong>{total_chats}</strong> total negotiation chats</p>
            </div>

            <div class="groups">
"""

    for group_name, chat_count in sorted(group_stats):
        html += f"""                <a href="{group_name}/index.html" class="group-card">
                    <div class="group-name">{group_name}</div>
                    <div class="group-count"><strong>{chat_count}</strong> chat{'' if chat_count == 1 else 's'}</div>
                </a>
"""

    html += f"""            </div>
        </div>

        <div class="footer">
            Generated from DarkWebInformer/Ransomchats repository
        </div>
    </div>
</body>
</html>
"""

    return html


def generate_group_index_html(group_name, json_files):
    """Generate index page for a specific ransomware group"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{group_name} - Ransomware Chats</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #ffffff;
            color: #333;
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}

        .header {{
            background: #f8f9fa;
            color: #333;
            padding: 32px;
            border-bottom: 2px solid #dee2e6;
        }}

        .header h1 {{
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #212529;
        }}

        .header .subtitle {{
            font-size: 16px;
            color: #6c757d;
            margin-bottom: 16px;
        }}

        .back-link {{
            display: inline-block;
            color: #0066cc;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}

        .content {{
            padding: 32px;
        }}

        .chat-list {{
            list-style: none;
        }}

        .chat-item {{
            border-bottom: 1px solid #f0f0f0;
            padding: 16px 0;
        }}

        .chat-item:last-child {{
            border-bottom: none;
        }}

        .chat-link {{
            color: #0066cc;
            text-decoration: none;
            font-size: 16px;
            font-weight: 500;
        }}

        .chat-link:hover {{
            text-decoration: underline;
        }}

        .footer {{
            padding: 16px 32px;
            background: #f8f9fa;
            text-align: center;
            font-size: 12px;
            color: #868e96;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{group_name}</h1>
            <div class="subtitle">{len(json_files)} negotiation chat{'' if len(json_files) == 1 else 's'}</div>
            <a href="../index.html" class="back-link">← Back to all groups</a>
        </div>

        <div class="content">
            <ul class="chat-list">
"""

    for json_file in sorted(json_files):
        html_file = json_file.replace('.json', '.html')
        chat_id = json_file.replace('.json', '')

        # Extract date using the same logic as chat rendering
        date = extract_date_from_chat(chat_id)

        # Format display name
        if date != chat_id:
            # We successfully parsed a date
            display_name = f"{date} ({chat_id})"
        else:
            # Couldn't parse date, just show chat_id
            display_name = chat_id

        html += f"""                <li class="chat-item">
                    <a href="{html_file}" class="chat-link">{display_name}</a>
                </li>
"""

    html += f"""            </ul>
        </div>

        <div class="footer">
            Generated from DarkWebInformer/Ransomchats repository
        </div>
    </div>
</body>
</html>
"""

    return html


# ============================================================================
# MAIN PROCESSING
# ============================================================================
def process_repository(repo_url, output_base, limit=None):
    """Process entire repository and generate HTML files"""
    print("=" * 70)
    print("RANSOMWARE CHAT BULK FORMATTER")
    print("=" * 70)
    print(f"Repository: {repo_url}")
    print(f"Output: {output_base}")
    print(f"Request delay: {REQUEST_DELAY}s | Max retries: {MAX_RETRIES}")
    if limit:
        print(f"Limit: Processing only {limit} group(s)")
    print("=" * 70)
    print()

    # Create output directory
    output_path = Path(output_base)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get list of ransomware group folders
    print("📋 Fetching ransomware group list...")
    try:
        groups = get_ransomware_groups(repo_url)
        print(f"✓ Found {len(groups)} ransomware groups")

        # Apply limit if specified
        if limit and limit > 0:
            groups = groups[:limit]
            print(f"  → Limited to first {len(groups)} group(s) for testing")

        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch group list")
        print(f"   {str(e)}")
        sys.exit(1)

    # Track statistics for index page
    group_stats = []

    # Process each group
    for idx, group_name in enumerate(groups, 1):
        print(f"[{idx}/{len(groups)}] Processing: {group_name}")

        group_url = f"{repo_url}/{group_name}"
        group_output_path = output_path / group_name
        group_output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Get JSON files in this group
            json_files = get_json_files(group_url)

            if not json_files:
                print(f"  ⚠ Empty directory - creating placeholder")
                readme_path = group_output_path / "README.txt"
                readme_path.write_text(
                    f"This directory is empty.\n"
                    f"The origin directory ({group_url}) contained no JSON files.\n"
                    f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                group_stats.append((group_name, 0))
                print(f"  ✓ Created empty directory with README")
                print()
                continue

            print(f"  📄 Found {len(json_files)} chat file(s)")

            # Process each JSON file
            for json_file in json_files:
                json_url = f"https://github.com/DarkWebInformer/Ransomchats/blob/main/{group_name}/{json_file}"
                raw_url = convert_github_url_to_raw(json_url)

                try:
                    # Fetch and parse JSON
                    json_content = fetch_with_retry(raw_url)
                    chat_data = json.loads(json_content)

                    # Generate HTML
                    html_content = generate_html(chat_data)

                    # Save HTML file
                    html_filename = json_file.replace('.json', '.html')
                    html_path = group_output_path / html_filename
                    html_path.write_text(html_content, encoding='utf-8')

                    print(f"    ✓ {json_file} → {html_filename}")

                except json.JSONDecodeError as e:
                    print(f"❌ ERROR: Invalid JSON in {json_file}")
                    print(f"   {str(e)}")
                    sys.exit(1)
                except Exception as e:
                    print(f"❌ ERROR: Failed to process {json_file}")
                    print(f"   {str(e)}")
                    sys.exit(1)

            # Generate group index page
            group_index_html = generate_group_index_html(group_name, json_files)
            group_index_path = group_output_path / "index.html"
            group_index_path.write_text(group_index_html, encoding='utf-8')

            group_stats.append((group_name, len(json_files)))
            print(f"  ✓ Processed {len(json_files)} chat(s) for {group_name}")
            print()

        except Exception as e:
            print(f"❌ ERROR: Failed to process group {group_name}")
            print(f"   {str(e)}")
            sys.exit(1)

    # Generate main index page
    print("📊 Generating main index page...")
    index_html = generate_index_html(group_stats)
    index_path = output_path / "index.html"
    index_path.write_text(index_html, encoding='utf-8')
    print(f"✓ Created index.html")
    print()

    # Final summary
    total_chats = sum(count for _, count in group_stats)
    print("=" * 70)
    print("✅ PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Groups processed: {len(groups)}")
    print(f"Total chats: {total_chats}")
    print(f"Output directory: {output_path.absolute()}")
    print(f"Open: {(output_path / 'index.html').absolute()}")
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python group_format_chat.py <github_repo_url> [--limit N]")
        print("Example: python group_format_chat.py https://github.com/DarkWebInformer/Ransomchats/tree/main")
        print("         python group_format_chat.py https://github.com/DarkWebInformer/Ransomchats/tree/main --limit 2")
        sys.exit(1)

    repo_url = sys.argv[1].rstrip('/')
    output_base = "ransomware_chats"
    limit = None

    # Parse optional --limit argument
    if len(sys.argv) > 2:
        if '--limit' in sys.argv:
            try:
                limit_index = sys.argv.index('--limit')
                limit = int(sys.argv[limit_index + 1])
            except (ValueError, IndexError):
                print("❌ ERROR: --limit requires a numeric argument")
                print("Example: --limit 2")
                sys.exit(1)

    try:
        process_repository(repo_url, output_base, limit=limit)
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
