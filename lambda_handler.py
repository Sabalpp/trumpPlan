"""
AWS Lambda Handler for Political Sentiment Alpha Platform
========================================================

Serverless function for:
1. Periodic data ingestion (EventBridge trigger)
2. API Gateway integration
3. Signal generation on-demand
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

# Set environment for Lambda
os.environ.setdefault('FLASK_ENV', 'production')

from app.main import app as flask_app
from tasks.celery_app import ingest_realtime_data, process_nlp_batch
from models.db import init_db, Event, Signal


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler
    
    Routes requests based on source:
    - API Gateway → Flask app
    - EventBridge → Scheduled task
    - Direct invocation → Custom logic
    
    Args:
        event: Lambda event dict
        context: Lambda context object
    
    Returns:
        Response dict with statusCode, headers, body
    """
    print(f"Lambda invoked: {event.get('source', 'unknown')}")
    
    # Route based on event source
    if 'source' in event and event['source'] == 'aws.events':
        # EventBridge scheduled trigger
        return handle_scheduled_task(event, context)
    
    elif 'httpMethod' in event:
        # API Gateway request
        return handle_api_request(event, context)
    
    elif 'task' in event:
        # Direct task invocation
        return handle_direct_task(event, context)
    
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Unsupported event type'})
        }


def handle_api_request(event: Dict, context: Any) -> Dict:
    """
    Handle API Gateway request through Flask
    
    Args:
        event: API Gateway event
        context: Lambda context
    
    Returns:
        API Gateway response format
    """
    try:
        # Convert API Gateway event to WSGI-compatible format
        from werkzeug.wrappers import Request, Response
        from werkzeug.datastructures import Headers
        
        # Build request
        method = event['httpMethod']
        path = event['path']
        headers = event.get('headers', {})
        body = event.get('body', '')
        query_string = event.get('queryStringParameters', {})
        
        # Create WSGI environ
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': '&'.join(f'{k}={v}' for k, v in query_string.items()) if query_string else '',
            'CONTENT_TYPE': headers.get('content-type', 'application/json'),
            'CONTENT_LENGTH': str(len(body)),
            'wsgi.input': body,
            'SERVER_NAME': 'lambda',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        
        # Add headers
        for key, value in headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key}'] = value
        
        # Process through Flask
        with flask_app.request_context(environ):
            response = flask_app.full_dispatch_request()
            
            # Convert Flask response to API Gateway format
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
    
    except Exception as e:
        print(f"Error handling API request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_scheduled_task(event: Dict, context: Any) -> Dict:
    """
    Handle EventBridge scheduled task
    
    Tasks:
    - ingest-realtime-data: Fetch new political data
    - cleanup-expired-signals: Mark old signals as expired
    - daily-summary: Generate daily stats
    
    Args:
        event: EventBridge event
        context: Lambda context
    
    Returns:
        Task result
    """
    try:
        # Determine which task to run
        rule_name = event.get('detail-type', '')
        
        if 'ingest' in rule_name.lower():
            # Run data ingestion
            result = ingest_realtime_data()
            
        elif 'cleanup' in rule_name.lower():
            # Run cleanup
            from tasks.celery_app import cleanup_expired_signals
            result = cleanup_expired_signals()
            
        elif 'summary' in rule_name.lower():
            # Generate summary
            from tasks.celery_app import generate_daily_summary
            result = generate_daily_summary()
            
        else:
            # Default: data ingestion
            result = ingest_realtime_data()
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        print(f"Error in scheduled task: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_direct_task(event: Dict, context: Any) -> Dict:
    """
    Handle direct Lambda invocation with custom task
    
    Event format:
    {
        "task": "process_events",
        "event_ids": [1, 2, 3]
    }
    
    Args:
        event: Direct invocation event
        context: Lambda context
    
    Returns:
        Task result
    """
    try:
        task = event['task']
        
        if task == 'process_events':
            event_ids = event.get('event_ids', [])
            result = process_nlp_batch(event_ids)
            
        elif task == 'generate_signal':
            text = event.get('text', '')
            timestamp = event.get('timestamp', datetime.utcnow().isoformat())
            
            from nlp.pipeline import NLPPipeline
            pipeline = NLPPipeline()
            result = pipeline.process_text(text, timestamp)
            
        else:
            result = {'error': f'Unknown task: {task}'}
        
        return {
            'statusCode': 200 if 'error' not in result else 500,
            'body': json.dumps(result, default=str)
        }
    
    except Exception as e:
        print(f"Error in direct task: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# For local testing
if __name__ == '__main__':
    # Test EventBridge trigger
    test_event = {
        'source': 'aws.events',
        'detail-type': 'Scheduled Event - Data Ingestion',
        'time': datetime.utcnow().isoformat()
    }
    
    class MockContext:
        function_name = 'test-function'
        memory_limit_in_mb = 512
        invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789:function:test'
        aws_request_id = 'test-request-id'
    
    print("\n🧪 Testing Lambda Handler\n")
    
    print("Test 1: Scheduled task (data ingestion)")
    result = lambda_handler(test_event, MockContext())
    print(f"Result: {result}\n")
    
    # Test API Gateway event
    api_event = {
        'httpMethod': 'GET',
        'path': '/health',
        'headers': {'Content-Type': 'application/json'},
        'queryStringParameters': {},
        'body': ''
    }
    
    print("Test 2: API Gateway request (health check)")
    result = lambda_handler(api_event, MockContext())
    print(f"Status: {result['statusCode']}")
    print(f"Body: {result['body'][:200]}\n")
    
    # Test direct invocation
    direct_event = {
        'task': 'generate_signal',
        'text': 'Boeing is doing great work!',
        'timestamp': '2024-01-01T12:00:00Z'
    }
    
    print("Test 3: Direct invocation (generate signal)")
    result = lambda_handler(direct_event, MockContext())
    print(f"Status: {result['statusCode']}")
    print(f"Result preview: {result['body'][:200]}...\n")

