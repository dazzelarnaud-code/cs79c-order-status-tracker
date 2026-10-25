"""Sample order status API for the CS 79C final project."""

import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
sns = boto3.client("sns")
PROJECT = "Daz Arnaud, CS 79C Final Project"


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"project": PROJECT, **body}),
    }


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    if method == "POST":
        try:
            data = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return response(400, {"error": "Body must be valid JSON."})
        if not isinstance(data, dict):
            return response(400, {"error": "Body must be a JSON object."})
        item_name = data.get("itemName")
        if not isinstance(item_name, str) or not 1 <= len(item_name.strip()) <= 80:
            return response(400, {"error": "itemName must have 1 to 80 characters."})
        order = {
            "orderId": str(uuid.uuid4()),
            "itemName": item_name.strip(),
            "status": "received",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        try:
            table.put_item(Item=order, ConditionExpression="attribute_not_exists(orderId)")
            sns.publish(
                TopicArn=os.environ["TOPIC_ARN"],
                Message=json.dumps({"orderId": order["orderId"], "status": order["status"]}),
                Subject="Sample order created",
            )
        except ClientError:
            return response(500, {"error": "The order service is unavailable."})
        return response(201, order)
    if method == "GET":
        order_id = (event.get("pathParameters") or {}).get("orderId", "")
        if not order_id:
            return response(400, {"error": "An order ID is required."})
        try:
            order = table.get_item(Key={"orderId": order_id}).get("Item")
        except ClientError:
            return response(500, {"error": "The order service is unavailable."})
        return response(200, order) if order else response(404, {"error": "Order not found."})
    return response(405, {"error": "Method not allowed."})
