import json
import boto3
import uuid
import logging
from datetime import datetime

# Initialize AWS clients
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("MoodTracker")

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Main Lambda function to handle different HTTP methods."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,DELETE"
    }

    try:
        if not isinstance(event, dict):
            logger.error("❌ Invalid event format. Expected a dictionary.")
            return error_response(400, "Invalid event format", cors_headers)

        logger.info(f"🔍 Full event received: {json.dumps(event, indent=2)}")

        http_method = event.get("httpMethod")
        if not http_method:
            logger.error("❌ 'httpMethod' not found in event")
            return error_response(400, "httpMethod not found in event", cors_headers)

        logger.info(f"✅ HTTP Method: {http_method}")

        # Handle CORS Preflight request
        if http_method == "OPTIONS":
            return success_response(200, {"message": "CORS Preflight"}, cors_headers)

        # Route request to appropriate handler
        handlers = {
            "POST": create_mood,
            "GET": get_mood,
            "PUT": update_mood,
            "DELETE": delete_mood
        }
        
        handler_function = handlers.get(http_method)
        if not handler_function:
            return error_response(405, "Method Not Allowed", cors_headers)

        return handler_function(event, cors_headers)

    except Exception as e:
        logger.error(f"❌ Critical error in lambda_handler: {str(e)}", exc_info=True)
        return error_response(500, "Internal Server Error", cors_headers)

def create_mood(event, headers):
    """Create a new mood entry."""
    try:
        body = json.loads(event.get("body", "{}"))
        mood = body.get("mood", "").strip().lower()
        note = body.get("note", "")

        if not mood:
            return error_response(400, "Mood is required", headers)

        # Generate AI suggestion using Amazon Bedrock
        titan_payload = {"inputText": f"How do I deal with feeling {mood}?"}
        logger.info(f"📩 Sending payload to Amazon Bedrock: {json.dumps(titan_payload, indent=2)}")

        response = bedrock.invoke_model(
            modelId="amazon.titan-text-express-v1",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(titan_payload)
        )

        response_body = json.loads(response["body"].read().decode("utf-8"))
        logger.info(f"📨 Received response from Amazon Bedrock: {json.dumps(response_body, indent=2)}")

        suggestion = response_body.get("results", [{}])[0].get("outputText", "No suggestion found.")
        
        mood_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Save to DynamoDB
        table.put_item(
            Item={
                "mood_id": mood_id,
                "mood": mood,
                "note": note,
                "suggestion": suggestion,
                "timestamp": timestamp
            }
        )

        return success_response(201, {
            "mood_id": mood_id,
            "mood": mood,
            "note": note,
            "suggestion": suggestion,
            "timestamp": timestamp
        }, headers)

    except Exception as e:
        logger.error(f"❌ Error in create_mood: {str(e)}", exc_info=True)
        return error_response(500, "Internal Server Error", headers)

def get_mood(event, headers):
    """Retrieve a mood entry by mood_id."""
    try:
        mood_id = event.get("pathParameters", {}).get("mood_id")
        if not mood_id:
            return error_response(400, "mood_id is required", headers)

        response = table.get_item(Key={"mood_id": mood_id})
        if "Item" not in response:
            return error_response(404, "Mood entry not found", headers)

        return success_response(200, response["Item"], headers)

    except Exception as e:
        logger.error(f"❌ Error in get_mood: {str(e)}", exc_info=True)
        return error_response(500, "Internal Server Error", headers)

def update_mood(event, headers):
    """Update an existing mood entry."""
    try:
        body = json.loads(event.get("body", "{}"))
        mood_id = body.get("mood_id")
        new_mood = body.get("mood")
        new_note = body.get("note")

        if not mood_id:
            return error_response(400, "mood_id is required", headers)

        update_expression = []
        expression_values = {}

        if new_mood:
            update_expression.append("mood = :m")
            expression_values[":m"] = new_mood
        if new_note:
            update_expression.append("note = :n")
            expression_values[":n"] = new_note

        if not update_expression:
            return error_response(400, "No fields to update", headers)

        update_expr = "SET " + ", ".join(update_expression)

        table.update_item(
            Key={"mood_id": mood_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expression_values
        )

        return success_response(200, {"message": "Mood updated successfully"}, headers)

    except Exception as e:
        logger.error(f"❌ Error in update_mood: {str(e)}", exc_info=True)
        return error_response(500, "Internal Server Error", headers)

def delete_mood(event, headers):
    """Delete a mood entry."""
    try:
        mood_id = event.get("pathParameters", {}).get("mood_id")
        if not mood_id:
            return error_response(400, "mood_id is required", headers)

        table.delete_item(Key={"mood_id": mood_id})

        return success_response(200, {"message": "Mood entry deleted successfully"}, headers)

    except Exception as e:
        logger.error(f"❌ Error in delete_mood: {str(e)}", exc_info=True)
        return error_response(500, "Internal Server Error", headers)

def success_response(status_code, body, headers=None):
    """Generate a successful API response."""
    response = {"statusCode": status_code, "body": json.dumps(body)}
    if headers:
        response["headers"] = headers
    return response

def error_response(status_code, message, headers=None):
    """Generate an error API response."""
    response = {"statusCode": status_code, "body": json.dumps({"error": message})}
    if headers:
        response["headers"] = headers
    return response
