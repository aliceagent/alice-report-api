# Alice Display Image Report API

This is a serverless API for handling image reports from the Alice Display website. It receives POST requests with image report data and creates entries in a Notion Reports database.

## Features

- ✅ Receives image reports via POST requests
- ✅ Validates incoming data
- ✅ Creates entries in Notion Reports database
- ✅ Handles CORS for GitHub Pages
- ✅ Proper error handling and responses

## Deployment Options

### Option 1: Railway (Recommended)
1. Connect this repository to Railway
2. Deploy using the Flask app (`app.py`)
3. Railway will use `requirements.txt` automatically

### Option 2: Vercel Serverless Functions
1. Deploy using Vercel CLI or GitHub integration
2. Uses the Python function in `api/report.py`
3. Configured via `vercel.json`

### Option 3: Render.com
1. Connect repository to Render
2. Deploy as a web service
3. Use `app.py` as the main application

## Testing

The API has been tested locally and confirmed to work with:

- ✅ Health endpoint: `GET /health`
- ✅ Report creation: `POST /api/report`
- ✅ Notion integration: Successfully creates database entries
- ✅ CORS: Properly configured for GitHub Pages

## API Endpoints

### `GET /health`
Returns API health status.

### `POST /api/report`
Creates a new image report in Notion.

**Request Body:**
```json
{
  "image_data": {
    "notion_id": "string",
    "title": "string",
    "url": "string", 
    "style": "string",
    "row_number": 0
  },
  "categories": ["category1", "category2"],
  "notes": "string (optional)",
  "context_data": {
    "time_of_day": "Morning|Midday|Evening|Night",
    "weather_shown": "string",
    "actual_weather": "string",
    "weather_mismatch": true,
    "holiday": "string",
    "hebrew_date": "string",
    "sunrise": "string",
    "sunset": "string",
    "user_agent": "string",
    "screen_resolution": "string", 
    "platform": "string"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Report created successfully",
  "notion_page_id": "string",
  "report_id": "string"
}
```

## Environment

- Python 3.9+
- Flask + Flask-CORS
- Requests library
- Notion API integration

## Configuration

The API uses hardcoded Notion credentials for the specific Alice Display use case. In production, these should be environment variables.

- **Notion Database ID**: `2fd41906-4d30-8148-a926-e0e19b0a8851`
- **Notion API Version**: `2022-06-28`

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python3 app.py

# Test with curl
curl -X POST http://localhost:3000/api/report \
  -H "Content-Type: application/json" \
  -d '{"image_data":{"title":"Test"},"categories":["poor-quality"]}'
```

## Status

✅ **TESTED AND WORKING**  
The API has been successfully tested locally and confirmed to create entries in the Notion Reports database.

Ready for production deployment to any of the supported platforms above.