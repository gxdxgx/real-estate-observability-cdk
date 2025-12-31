import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';
import { EnvironmentConfig } from '../config/environments';
import { DYNAMODB_CONFIG } from '../config/constants';

export interface DatabaseStackProps extends cdk.StackProps {
  readonly config: EnvironmentConfig;
}

export class DatabaseStack extends cdk.Stack {
  public readonly propertiesTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    const { config } = props;

    // Properties table
    this.propertiesTable = new dynamodb.Table(this, 'PropertiesTable', {
      tableName: `${config.dynamoDbTablePrefix}-properties`,
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'createdAt',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: DYNAMODB_CONFIG.pointInTimeRecovery,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: config.environment === 'prod' 
        ? cdk.RemovalPolicy.RETAIN 
        : cdk.RemovalPolicy.DESTROY,
    });

    // Global Secondary Index for querying by status
    this.propertiesTable.addGlobalSecondaryIndex({
      indexName: 'StatusIndex',
      partitionKey: {
        name: 'status',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'updatedAt',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // Global Secondary Index for querying by location
    this.propertiesTable.addGlobalSecondaryIndex({
      indexName: 'LocationIndex',
      partitionKey: {
        name: 'location',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'price',
        type: dynamodb.AttributeType.NUMBER,
      },
    });

    // Outputs
    new cdk.CfnOutput(this, 'PropertiesTableName', {
      value: this.propertiesTable.tableName,
      description: 'Properties DynamoDB table name',
      exportName: `${config.environment}-properties-table-name`,
    });

    new cdk.CfnOutput(this, 'PropertiesTableArn', {
      value: this.propertiesTable.tableArn,
      description: 'Properties DynamoDB table ARN',
      exportName: `${config.environment}-properties-table-arn`,
    });
  }
}