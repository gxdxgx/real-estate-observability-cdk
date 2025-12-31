export interface EnvironmentConfig {
  readonly environment: string;
  readonly region: string;
  readonly account?: string;
  readonly apiStage: string;
  readonly logLevel: string;
  readonly enableXRay: boolean;
  readonly enableCustomMetrics: boolean;
  readonly corsOrigins: string[];
  readonly lambdaRuntime: 'python3.12' | 'python3.11' | 'python3.10';
  readonly dynamoDbTablePrefix: string;
}

export const getEnvironmentConfig = (environment: string): EnvironmentConfig => {
  const baseConfig = {
    environment,
    region: process.env.AWS_REGION || 'ap-northeast-1',
    lambdaRuntime: 'python3.12' as const,
    dynamoDbTablePrefix: `real-estate-observability-${environment}`,
  };

  switch (environment) {
    case 'dev':
      return {
        ...baseConfig,
        apiStage: 'dev',
        logLevel: 'DEBUG',
        enableXRay: false,
        enableCustomMetrics: true,
        corsOrigins: ['*'],
      };
    
    case 'staging':
      return {
        ...baseConfig,
        apiStage: 'staging',
        logLevel: 'INFO',
        enableXRay: false,
        enableCustomMetrics: true,
        corsOrigins: ['https://staging.example.com'],
      };
    
    case 'prod':
      return {
        ...baseConfig,
        apiStage: 'prod',
        logLevel: 'WARN',
        enableXRay: false,
        enableCustomMetrics: true,
        corsOrigins: ['https://example.com'],
      };
    
    default:
      throw new Error(`Unknown environment: ${environment}`);
  }
};