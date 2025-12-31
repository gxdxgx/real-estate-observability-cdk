import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError
from aws_lambda_powertools import Tracer

tracer = Tracer()

class DynamoDBConnection:
    """DynamoDB connection manager with best practices."""
    
    def __init__(self):
        self._dynamodb = None
        self._region = os.environ.get('REGION', 'ap-northeast-1')
    
    @property
    def dynamodb(self):
        """Lazy initialization of DynamoDB resource."""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource('dynamodb', region_name=self._region)
        return self._dynamodb
    
    @tracer.capture_method
    def get_table(self, table_name: str):
        """Get DynamoDB table with error handling."""
        try:
            table = self.dynamodb.Table(table_name)
            # Verify table exists by getting its status
            table.load()
            return table
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise ValueError(f"Table {table_name} not found")
            raise e
    
    @tracer.capture_method
    def health_check(self, table_name: str) -> bool:
        """Check if DynamoDB table is accessible."""
        try:
            table = self.get_table(table_name)
            table.load()
            return True
        except Exception:
            return False

# Global connection instance
db_connection = DynamoDBConnection()

def get_db_connection() -> DynamoDBConnection:
    """Get the global DynamoDB connection instance."""
    return db_connection