import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { PythonLambdaFunction } from '../constructs/lambda-function';
import { EnvironmentConfig } from '../config/environments';
import { API_THROTTLING } from '../config/constants';
import * as path from 'path';
import * as fs from 'fs';

export interface ApiStackProps extends cdk.StackProps {
  readonly config: EnvironmentConfig;
}

export class ApiStack extends cdk.Stack {
  public readonly api: apigateway.RestApi;
  public readonly healthCheckFunction: PythonLambdaFunction;
  public readonly calculateCashFlowFunction: PythonLambdaFunction;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    const { config } = props;

    // Create API Gateway
    this.api = new apigateway.RestApi(this, 'Api', {
      restApiName: `${config.environment}-real-estate-api`,
      description: `Real Estate Observability API - ${config.environment}`,
      deployOptions: {
        stageName: config.apiStage,
        throttlingRateLimit: API_THROTTLING.rateLimit,
        throttlingBurstLimit: API_THROTTLING.burstLimit,
        tracingEnabled: config.enableXRay,
        metricsEnabled: config.enableCustomMetrics,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: config.corsOrigins,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key', 'X-Amz-Security-Token'],
        allowCredentials: true,
      },
    });

    // Lambda functions base path - use src directory to include shared modules
    // Use absolute path to ensure correct mounting in Docker
    const lambdaBasePath = path.resolve(__dirname, '../../../src');

    // Create shared dependencies layer
    // Use pre-built lambda-layer directory created during Docker build
    // This avoids CDK bundling issues and ensures consistent builds
    // The lambda-layer directory contains python/ subdirectory with all dependencies
    const layerPath = path.resolve(__dirname, '../../../lambda-layer');
    
    // Check if lambda-layer directory exists
    if (!fs.existsSync(layerPath)) {
      throw new Error(
        `Lambda layer directory not found at ${layerPath}. ` +
        `Please rebuild the Docker container: docker compose build cdk`
      );
    }
    
    // Verify python subdirectory exists
    const pythonSubdir = path.join(layerPath, 'python');
    if (!fs.existsSync(pythonSubdir)) {
      throw new Error(
        `Lambda layer python subdirectory not found at ${pythonSubdir}. ` +
        `Please rebuild the Docker container: docker compose build cdk`
      );
    }
    
    const dependenciesLayer = new lambda.LayerVersion(this, 'DependenciesLayer', {
      code: lambda.Code.fromAsset(layerPath, {
        assetHashType: cdk.AssetHashType.SOURCE, // Use source hash for better caching
        // No bundling needed - directory structure is already correct
      }),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      description: 'Shared Python dependencies layer',
    });

    // Health check function
    this.healthCheckFunction = new PythonLambdaFunction(this, 'HealthCheckFunction', {
      config,
      functionName: `${config.environment}-health-check`,
      description: 'Health check endpoint',
      codePath: lambdaBasePath,
      handler: 'handlers.api.health.health_check.handler',
      layers: [dependenciesLayer],
    });

    // Calculate cash flow function
    this.calculateCashFlowFunction = new PythonLambdaFunction(this, 'CalculateCashFlowFunction', {
      config,
      functionName: `${config.environment}-calculate-cash-flow`,
      description: 'Calculate cash flow for real estate investment',
      codePath: lambdaBasePath,
      handler: 'handlers.api.calculate.cash_flow.handler',
      layers: [dependenciesLayer],
    });

    // Create Lambda integrations
    const healthCheckIntegration = new apigateway.LambdaIntegration(this.healthCheckFunction.function);
    const calculateCashFlowIntegration = new apigateway.LambdaIntegration(this.calculateCashFlowFunction.function);

    // API routes
    // Health endpoint
    const healthResource = this.api.root.addResource('health');
    healthResource.addMethod('GET', healthCheckIntegration);

    // API v1 routes
    const apiResource = this.api.root.addResource('api');
    const v1Resource = apiResource.addResource('v1');
    const calculateResource = v1Resource.addResource('calculate');
    const cashFlowResource = calculateResource.addResource('cash-flow');
    cashFlowResource.addMethod('POST', calculateCashFlowIntegration);

    // Root endpoint (welcome message)
    this.api.root.addMethod('GET', healthCheckIntegration);

    // Add request validation
    const requestValidator = new apigateway.RequestValidator(this, 'RequestValidator', {
      restApi: this.api,
      validateRequestBody: true,
      validateRequestParameters: true,
    });

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.api.url,
      description: 'API Gateway URL',
      exportName: `${config.environment}-api-url`,
    });

    new cdk.CfnOutput(this, 'ApiId', {
      value: this.api.restApiId,
      description: 'API Gateway ID',
      exportName: `${config.environment}-api-id`,
    });
  }
}