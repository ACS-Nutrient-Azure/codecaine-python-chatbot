"""
Direct DynamoDB integration tests
Tests database read/write operations without API layer
"""
import boto3
from datetime import datetime
from uuid import uuid4
import os
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-northeast-2")
ENDPOINT = os.getenv("DYNAMODB_ENDPOINT_URL", "https://dynamodb.ap-northeast-2.amazonaws.com")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "ChatbotData")

dynamodb = boto3.resource(
    'dynamodb',
    region_name=REGION,
    endpoint_url=ENDPOINT,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)
table = dynamodb.Table(TABLE_NAME)

TEST_COGNITO_ID = "test-user-db-" + str(uuid4())[:8]
TEST_CONVERSATION_ID = "test-conv-" + str(uuid4())[:8]

def test_write_message():
    """Test writing a message to DynamoDB"""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    message_id = str(uuid4())
    
    item = {
        'PK': f"USER#{TEST_COGNITO_ID}",
        'SK': f"CONV#{TEST_CONVERSATION_ID}#MSG#{timestamp}#{message_id}",
        'GSI1PK': f"CONV#{TEST_CONVERSATION_ID}",
        'GSI1SK': f"MSG#{timestamp}#{message_id}",
        'is_bot': 0,
        'message': 'Test message from integration test',
        'created_at': timestamp
    }
    
    table.put_item(Item=item)
    print(f"✓ Message written to DynamoDB: {message_id}")
    return message_id

def test_read_message():
    """Test reading messages from DynamoDB using GSI"""
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :pk AND begins_with(GSI1SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f"CONV#{TEST_CONVERSATION_ID}",
            ':sk': 'MSG#'
        }
    )
    
    items = response.get('Items', [])
    print(f"✓ Messages read from DynamoDB: {len(items)} items")
    return items

def test_write_analysis():
    """Test writing analysis result to DynamoDB"""
    result_id = str(uuid4())[:8]
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    item = {
        'PK': f"USER#{TEST_COGNITO_ID}",
        'SK': f"ANALYSIS#{result_id}",
        'conversation_id': TEST_CONVERSATION_ID,
        'chat_summary': '{"title": "Test Analysis", "deficient_nutrients": ["비타민C"]}',
        'created_at': timestamp
    }
    
    table.put_item(Item=item)
    print(f"✓ Analysis result written to DynamoDB: {result_id}")
    return result_id

def test_read_analysis():
    """Test reading analysis results from DynamoDB"""
    response = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f"USER#{TEST_COGNITO_ID}",
            ':sk': 'ANALYSIS#'
        }
    )
    
    items = response.get('Items', [])
    print(f"✓ Analysis results read from DynamoDB: {len(items)} items")
    return items

def cleanup():
    """Clean up test data"""
    try:
        # Query all items for test user
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': f"USER#{TEST_COGNITO_ID}"}
        )
        
        # Delete each item
        for item in response.get('Items', []):
            table.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
        
        print(f"✓ Cleaned up {len(response.get('Items', []))} test items")
    except Exception as e:
        print(f"⚠ Cleanup warning: {e}")

def run_all_tests():
    print("\n=== DynamoDB Integration Tests ===\n")
    try:
        # Write tests
        test_write_message()
        test_write_analysis()
        
        # Read tests
        messages = test_read_message()
        assert len(messages) > 0, "No messages found"
        
        analyses = test_read_analysis()
        assert len(analyses) > 0, "No analysis results found"
        
        print("\n✅ All DynamoDB tests passed!\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
    finally:
        cleanup()

if __name__ == "__main__":
    run_all_tests()
