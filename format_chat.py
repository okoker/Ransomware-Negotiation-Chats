#!/usr/bin/env python3
"""
Ransomware Chat Formatter
Converts JSON chat logs to polished HTML format
"""

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


def convert_github_url(url):
    """Convert GitHub blob URL to raw content URL"""
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url


def fetch_json(url):
    """Fetch JSON content from URL"""
    url = convert_github_url(url)
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)


def format_timestamp(timestamp, chat_id):
    """Format timestamp with date context"""
    if not timestamp:
        return ""
    # Parse chat_id to get date
    try:
        date = datetime.strptime(chat_id, "%Y%m%d").strftime("%B %d, %Y")
    except:
        date = chat_id
    return f"{date} at {timestamp}"


def generate_html(chat_data):
    """Generate polished HTML from chat data"""
    chat_id = chat_data.get("chat_id", "Unknown")
    messages = chat_data.get("messages", [])

    # Parse date for title
    try:
        chat_date = datetime.strptime(chat_id, "%Y%m%d").strftime("%B %d, %Y")
    except:
        chat_date = chat_id

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
        import re
        content = re.sub(r'\n\s*\n+', '\n', content)
        content = content.strip()

        # Determine party class
        party_class = "victim" if party.lower() == "victim" else "attacker"

        # Format timestamp
        time_display = format_timestamp(timestamp, chat_id) if timestamp else "No timestamp"

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


def main():
    if len(sys.argv) < 2:
        print("Usage: python format_chat.py <url_to_json>")
        print("Example: python format_chat.py https://github.com/DarkWebInformer/Ransomchats/blob/main/BlackBasta/20221011.json")
        sys.exit(1)

    url = sys.argv[1]
    print(f"Fetching chat data from: {url}")

    # Fetch and parse JSON
    chat_data = fetch_json(url)

    # Generate HTML
    html_content = generate_html(chat_data)

    # Save to file
    chat_id = chat_data.get("chat_id", "chat")
    output_file = f"chat_{chat_id}.html"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Chat formatted successfully!")
    print(f"✓ Output saved to: {output_file}")
    print(f"✓ Total messages: {len(chat_data.get('messages', []))}")


if __name__ == "__main__":
    main()
