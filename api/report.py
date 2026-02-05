from http.server import BaseHTTPRequestHandler
import json
import os
import time
import random
import string
import urllib.request
import urllib.error

# Notion configuration (from environment variables)
NOTION_API_KEY = os.environ.get('NOTION_API_KEY', '')
NOTION_API_VERSION = '2022-06-28'
REPORTS_DATABASE_ID = os.environ.get('REPORTS_DATABASE_ID', '2fd41906-4d30-8148-a926-e0e19b0a8851')

def generate_report_id():
    """Generate a unique report ID"""
    timestamp = int(time.time())
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"RPT-{timestamp}-{suffix}"

def create_notion_report(report_data):
    """Create a report entry in Notion"""
    url = "https://api.notion.com/v1/pages"
    
    report_id = generate_report_id()
    
    # Build categories multi-select
    categories = []
    for cat in report_data.get('categories', []):
        categories.append({"name": cat})
    
    # Build the page properties (matching Notion database schema)
    properties = {
        "Report ID": {"title": [{"text": {"content": report_id}}]},
        "Status": {"select": {"name": "New"}},
        "Categories": {"multi_select": categories},
        "Notes": {"rich_text": [{"text": {"content": report_data.get('notes', '')[:2000]}}]},
        "Image Title": {"rich_text": [{"text": {"content": report_data.get('imageTitle', '')[:200]}}]},
        "Image Notion ID": {"rich_text": [{"text": {"content": report_data.get('imageId', '')}}]},
    }
    
    # Add optional select fields only if values provided
    weather = report_data.get('weatherShown', '')
    if weather:
        properties["Weather Shown"] = {"select": {"name": weather}}
    
    time_of_day = report_data.get('timeOfDay', '')
    if time_of_day:
        properties["Time of Day"] = {"select": {"name": time_of_day}}
    
    payload = {
        "parent": {"database_id": REPORTS_DATABASE_ID},
        "properties": properties
    }
    
    headers = {
        'Authorization': f'Bearer {NOTION_API_KEY}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_API_VERSION
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {"success": True, "reportId": report_id, "notionPageId": result.get('id')}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {"success": False, "error": f"Notion API error: {e.code}", "details": error_body}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            report_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "Invalid JSON"}).encode())
            return
        
        # Create report in Notion
        result = create_notion_report(report_data)
        
        if result.get('success'):
            self.send_response(200)
        else:
            self.send_response(500)
        
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "service": "Alice Report API"}).encode())
