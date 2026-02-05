#!/usr/bin/env python3
"""
Flask API for Alice Display Image Reports
Deployable to various hosting services
"""

import os
import json
import time
import random
import string
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# CORS configuration
CORS(app, origins=[
    'https://aliceagent.github.io',
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000'
])

# Notion configuration (from environment variables)
NOTION_API_KEY = os.environ.get('NOTION_API_KEY', '')
NOTION_API_VERSION = '2022-06-28'
REPORTS_DATABASE_ID = os.environ.get('REPORTS_DATABASE_ID', '2fd41906-4d30-8148-a926-e0e19b0a8851')

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'service': 'Alice Display Image Report API',
        'timestamp': time.time()
    })

@app.route('/health', methods=['GET'])
def health():
    """Detailed health endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0'
    })

@app.route('/api/report', methods=['POST'])
def create_report():
    """Main report creation endpoint"""
    try:
        # Get JSON data
        report_data = request.get_json()
        
        if not report_data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        if not report_data.get('image_data') or not report_data.get('categories'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: image_data and categories'
            }), 400

        print(f"Received report: {json.dumps(report_data, indent=2)}")

        # Create report in Notion
        notion_result = create_report_in_notion(report_data)
        
        if notion_result['success']:
            print(f"Successfully created report: {notion_result['page_id']}")
            return jsonify({
                'success': True,
                'message': 'Report created successfully',
                'notion_page_id': notion_result['page_id'],
                'report_id': notion_result['report_id']
            }), 200
        else:
            print(f"Failed to create report: {notion_result['error']}")
            return jsonify({
                'success': False,
                'error': notion_result['error']
            }), 500

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def create_report_in_notion(report_data):
    """Create a report entry in Notion database"""
    try:
        # Generate unique report ID
        timestamp = int(time.time())
        random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        report_id = f"RPT-{timestamp}-{random_id}"

        print(f"Creating Notion report: {report_id}")

        # Build Notion page properties using correct database schema
        properties = {
            "Report ID": {
                "title": [
                    {
                        "text": {
                            "content": report_id
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": "New"
                }
            },
            "Categories": {
                "multi_select": [{"name": category} for category in report_data['categories']]
            },
            "Notes": {
                "rich_text": [
                    {
                        "text": {
                            "content": report_data.get('notes', 'No additional notes provided')
                        }
                    }
                ]
            },
            "Image Title": {
                "rich_text": [
                    {
                        "text": {
                            "content": report_data.get('image_data', {}).get('title', '')
                        }
                    }
                ]
            },
            "Art Style": {
                "rich_text": [
                    {
                        "text": {
                            "content": report_data.get('image_data', {}).get('style', '')
                        }
                    }
                ]
            },
            "Image Row #": {
                "number": report_data.get('image_data', {}).get('row_number', 0)
            },
            "Image Notion ID": {
                "rich_text": [
                    {
                        "text": {
                            "content": report_data.get('image_data', {}).get('notion_id', '')
                        }
                    }
                ]
            }
        }

        # Add optional context fields
        context_data = report_data.get('context_data', {})
        
        if context_data.get('time_of_day') in ['Morning', 'Midday', 'Evening', 'Night']:
            properties["Time of Day"] = {
                "select": {
                    "name": context_data['time_of_day']
                }
            }

        if context_data.get('weather_shown'):
            properties["Weather Shown"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": context_data['weather_shown']
                        }
                    }
                ]
            }

        if context_data.get('actual_weather'):
            properties["Actual Weather"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": context_data['actual_weather']
                        }
                    }
                ]
            }

        if 'weather_mismatch' in context_data:
            properties["Weather Mismatch"] = {
                "checkbox": bool(context_data['weather_mismatch'])
            }

        for field in ['holiday', 'hebrew_date', 'sunrise', 'sunset']:
            if context_data.get(field):
                field_name = field.replace('_', ' ').title()
                if field_name == 'Hebrew Date':
                    field_name = 'Hebrew Date'
                properties[field_name] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": str(context_data[field])
                            }
                        }
                    ]
                }

        # Create page in Notion database
        response = requests.post(
            'https://api.notion.com/v1/pages',
            headers={
                'Authorization': f'Bearer {NOTION_API_KEY}',
                'Content-Type': 'application/json',
                'Notion-Version': NOTION_API_VERSION
            },
            json={
                'parent': {
                    'database_id': REPORTS_DATABASE_ID
                },
                'properties': properties
            }
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Successfully created Notion page: {result['id']}")
            
            return {
                'success': True,
                'page_id': result['id'],
                'report_id': report_id
            }
        else:
            error_text = response.text
            print(f"Notion API error: {response.status_code} {error_text}")
            
            return {
                'success': False,
                'error': f'Notion API error: {response.status_code}'
            }

    except Exception as e:
        print(f"Error creating Notion page: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"Starting Alice Report API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)