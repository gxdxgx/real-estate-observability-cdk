export const PROJECT_NAME = 'real-estate-observability';

export const LAMBDA_TIMEOUT_SECONDS = 30;
export const LAMBDA_MEMORY_SIZE = 512;

export const API_THROTTLING = {
  rateLimit: 1000,
  burstLimit: 2000,
};

export const DYNAMODB_CONFIG = {
  billingMode: 'PAY_PER_REQUEST',
  pointInTimeRecovery: true,
  encryption: 'AWS_MANAGED',
} as const;

export const CLOUDWATCH_LOG_RETENTION_DAYS = 14;

export const TAGS = {
  Project: PROJECT_NAME,
  ManagedBy: 'CDK',
} as const;