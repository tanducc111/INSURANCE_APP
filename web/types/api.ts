export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
};

export type ApiListParams = {
  skip?: number;
  limit?: number;
  search?: string;
};
