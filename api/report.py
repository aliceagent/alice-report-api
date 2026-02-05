"""
Vercel Python Serverless Function: Alice Display Image Report API
"""

import json
import time
import random
import string
import requests
from urllib.parse import parse_qs

# Notion configuration (from environment variables)
import os
NOTION_API_KEY = os.environ.get('NOTION_API_KEY', '')
NOTION_API_VERSION = '2022-06-28'
REPORTS_DATABASE_ID = os.environ.get('REPORTS_DATABASE_ID', '2fd41906-4d30-8148-a926-e0e19b0a8851')

def handler(request):
    """Main handler for Vercel"""
    
    # Set CORS headers
    headers = {
        'Access-Control-Allow-Origin': 'https://aliceagent.github.io',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 204,
            'headers': headers,
            'body': ''
        }
    
    # Only allow POST
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': 'Method not allowed'})
        }
    
    try:
        # Parse JSON body
        if hasattr(request, 'json') and request.json:
            report_data = request.json
        else:
            # Try to parse from body
            body = request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            report_data = json.loads(body)
        
        # Validate required fields
        if not report_data.get('image_data') or not report_data.get('categories'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required fields: image_data and categories'
                })
            }

        # Create report in Notion
        notion_result = create_report_in_notion(report_data)
        
        if notion_result['success']:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'message': 'Report created successfully',
                    'notion_page_id': notion_result['page_id'],
                    'report_id': notion_result['report_id']
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': notion_result['error']
                })
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }

def create_report_in_notion(report_data):
    """Create a report entry in Notion database"""
    try:
        # Generate unique report ID
        timestamp = int(time.time())
        random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        report_id = f"RPT-{timestamp}-{random_id}"

        # Build Notion page properties
        properties = {
            "Report ID": {
                "title": [{"text": {"content": report_id}}]
            },
            "Status": {
                "select": {"name": "New"}
            },
            "Categories": {
                "multi_select": [{"name": category} for category in report_data['categories']]
            },
            "Notes": {
                "rich_text": [{"text": {"content": report_data.get('notes', 'No additional notes provided')}}]
            },
            "Image Title": {
                "rich_text": [{"text": {"content": report_data.get('image_data', {}).get('title', '')}}]
            },
            "Art Style": {
                "rich_text": [{"text": {"content": report_data.get('image_data', {}).get('style', '')}}]
            },
            "Image Row #": {
                "number": report_data.get('image_data', {}).get('row_number', 0)
            },
            "Image Notion ID": {
                "rich_text": [{"text": {"content": report_data.get('image_data', {}).get('notion_id', '')}}]
            }
        }

        # Add context fields if provided
        context_data = report_data.get('context_data', {})
        
        if context_data.get('time_of_day') in ['Morning', 'Midday', 'Evening', 'Night']:
            properties["Time of Day"] = {"select": {"name": context_data['time_of_day']}}

        for field in ['weather_shown', 'actual_weather', 'holiday', 'hebrew_date', 'sunrise', 'sunset']:
            if context_data.get(field):
                field_name = field.replace('_', ' ').title()
                if field_name == 'Hebrew Date':
                    field_name = 'Hebrew Date'
                elif field_name == 'Weather Shown':
                    field_name = 'Weather Shown'
                elif field_name == 'Actual Weather':
                    field_name = 'Actual Weather'
                properties[field_name] = {
                    "rich_text": [{"text": {"content": str(context_data[field])}}]
                }

        if 'weather_mismatch' in context_data:
            properties["Weather Mismatch"] = {"checkbox": bool(context_data['weather_mismatch'])}

        # Create page in Notion
        response = requests.post(
            'https://api.notion.com/v1/pages',
            headers={
                'Authorization': f'Bearer {NOTION_API_KEY}',
                'Content-Type': 'application/json',
                'Notion-Version': NOTION_API_VERSION
            },
            json={
                'parent': {'database_id': REPORTS_DATABASE_ID},
                'properties': properties
            }
        )

        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'page_id': result['id'],
                'report_id': report_id
            }
        else:
            return {
                'success': False,
                'error': f'Notion API error: {response.status_code}'
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }