import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { EnvironmentConfig } from '../config/environments';
import { LAMBDA_TIMEOUT_SECONDS, LAMBDA_MEMORY_SIZE, CLOUDWATCH_LOG_RETENTION_DAYS } from '../config/constants';
import * as path from 'path';

export interface PythonLambdaFunctionProps {
  readonly config: EnvironmentConfig;
  readonly functionName: string;
  readonly description?: string;
  readonly codePath: string;
  readonly handler: string;
  readonly environment?: { [key: string]: string };
  readonly timeout?: cdk.Duration;
  readonly memorySize?: number;
  readonly layers?: lambda.ILayerVersion[];
}

export class PythonLambdaFunction extends Construct {
  public readonly function: lambda.Function;

  constructor(scope: Construct, id: string, props: PythonLambdaFunctionProps) {
    super(scope, id);

    // Create log group with retention (14 days)
    const logGroup = new logs.LogGroup(this, 'LogGroup', {
      logGroupName: `/aws/lambda/${props.functionName}`,
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Environment variables
    const environment = {
      LOG_LEVEL: props.config.logLevel,
      ENVIRONMENT: props.config.environment,
      REGION: props.config.region,
      ...props.environment,
    };

    // Prepare layers array
    const layers: lambda.ILayerVersion[] = [
      // Add AWS Lambda Powertools layer
      lambda.LayerVersion.fromLayerVersionArn(
        this,
        'PowertoolsLayer',
        `arn:aws:lambda:${props.config.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:68`
      ),
    ];
    
    // Add custom layers if provided
    if (props.layers) {
      layers.push(...props.layers);
    }
    
    // Create Lambda function (dependencies are in layer, so only copy source code)
    // No need for Docker bundling - just copy source code directly
    this.function = new lambda.Function(this, 'Function', {
      functionName: props.functionName,
      description: props.description,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: props.handler,
      code: lambda.Code.fromAsset(props.codePath, {
        assetHashType: cdk.AssetHashType.SOURCE, // Use source hash for better caching
        // No bundling needed - just copy source code as-is
      }),
      environment,
      timeout: props.timeout || cdk.Duration.seconds(LAMBDA_TIMEOUT_SECONDS),
      memorySize: props.memorySize || LAMBDA_MEMORY_SIZE,
      tracing: props.config.enableXRay ? lambda.Tracing.ACTIVE : lambda.Tracing.DISABLED,
      logGroup,
      // Enable container reuse for better performance
      reservedConcurrentExecutions: undefined,
      layers,
    });

    // Add tags
    cdk.Tags.of(this.function).add('FunctionName', props.functionName);
    cdk.Tags.of(this.function).add('Environment', props.config.environment);
  }
}