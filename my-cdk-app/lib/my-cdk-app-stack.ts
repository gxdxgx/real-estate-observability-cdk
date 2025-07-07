import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';

export class MyCdkAppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Lambda function for API endpoints
    const apiHandler = new lambda.Function(this, 'ApiHandler', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import datetime

def handler(event, context):
    method = event['httpMethod']
    path = event['path']
    
    print(f'Request: {method} {path}')
    
    # Simple routing
    if method == 'GET' and path == '/':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'message': 'Welcome to Real Estate Observability API',
                'timestamp': datetime.datetime.now().isoformat()
            })
        }
    
    if method == 'GET' and path == '/health':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'status': 'healthy',
                'timestamp': datetime.datetime.now().isoformat()
            })
        }
    
    if method == 'GET' and path == '/properties':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'properties': [
                    {'id': 1, 'address': '123 Main St', 'price': 500000},
                    {'id': 2, 'address': '456 Oak Ave', 'price': 750000}
                ]
            })
        }
    
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps({
            'error': 'Not found'
        })
    }
      `),
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'RealEstateApi', {
      restApiName: 'Real Estate Observability API',
      description: 'Simple API for real estate observability',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
      },
    });

    // Lambda integration
    const lambdaIntegration = new apigateway.LambdaIntegration(apiHandler);

    // API routes
    api.root.addMethod('GET', lambdaIntegration);
    
    const healthResource = api.root.addResource('health');
    healthResource.addMethod('GET', lambdaIntegration);
    
    const propertiesResource = api.root.addResource('properties');
    propertiesResource.addMethod('GET', lambdaIntegration);

    // Output the API URL
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'API Gateway URL'
    });
  }
}
