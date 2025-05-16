export interface ResponseHeader {
  code: string;
  message: string;
  timestamp: string;
}

export interface ResponseBody<T = any> {
  data?: T;
  metadata?: {
    total?: number;
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_direction?: string;
  };
}

export interface StandardResponse<T = any> {
  header: ResponseHeader;
  body: ResponseBody<T>;
}

export interface BulkUploadResult {
  status: 'success' | 'partial_success' | 'error';
  message: string;
  total_rows: number;
  success_count: number;
  error_count: number;
  failed_items: Array<{
    row: number;
    name: string;
    error: string;
  }>;
} 