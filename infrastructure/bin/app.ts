#!/usr/bin/env node
import 'dotenv/config';
import * as cdk from 'aws-cdk-lib';
import { getEnvironmentConfig } from '../lib/config/environments';
import { TAGS } from '../lib/config/constants';

// 各スタックで定義したリソースをインポート
import { ApiStack } from '../lib/stacks/api-stack';


const app = new cdk.App();

// Get environment from context or default to 'dev'
const environment = app.node.tryGetContext('environment') || process.env.ENVIRONMENT || 'dev';
const config = getEnvironmentConfig(environment);

// Common stack props
const stackProps: cdk.StackProps = {
  env: {
    account: config.account || process.env.CDK_DEFAULT_ACCOUNT,
    region: config.region,
  },
  tags: {
    ...TAGS,
    Environment: config.environment,
  },
};

// Create stacks
const apiStack = new ApiStack(app, `ApiStack-${config.environment}`, {
  ...stackProps,
  config,
});