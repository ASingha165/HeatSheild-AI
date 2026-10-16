/**
 * Centralized Typed API Client for HeatShield AI.
 */

import type {
  HealthResponse,
  LocationsResponse,
  ReportAnalyzeRequest,
  ReportAnalyzeResponse,
  SystemConfigResponse,
} from '../types/api';

const RAW_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').trim();
// If base URL has a trailing slash, strip it
const API_BASE = RAW_BASE_URL.replace(/\/+$/, '');

class ApiClient {
  private getUrl(path: string): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return API_BASE ? `${API_BASE}${cleanPath}` : cleanPath;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, timeoutMs = 45000): Promise<T> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(this.getUrl(endpoint), {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          } else if (errData.message) {
            errorMsg = errData.message;
          }
        } catch {
          // Response body was not JSON
        }
        throw new Error(errorMsg);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw new Error(`Request to ${endpoint} timed out after ${timeoutMs / 1000} seconds.`);
      }
      throw err;
    } finally {
      clearTimeout(id);
    }
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health', { method: 'GET' }, 8000);
  }

  async getConfigStatus(): Promise<SystemConfigResponse> {
    return this.request<SystemConfigResponse>('/api/config/status', { method: 'GET' }, 8000);
  }

  async getLocations(): Promise<LocationsResponse> {
    return this.request<LocationsResponse>('/api/locations', { method: 'GET' }, 10000);
  }

  async analyzeReport(payload: ReportAnalyzeRequest): Promise<ReportAnalyzeResponse> {
    return this.request<ReportAnalyzeResponse>(
      '/api/reports/analyze',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      60000 // 60s timeout to allow CPU Decider forward-pass
    );
  }

  async getReportById(reportId: string): Promise<ReportAnalyzeResponse> {
    return this.request<ReportAnalyzeResponse>(`/api/reports/${encodeURIComponent(reportId)}`, { method: 'GET' });
  }
}

export const api = new ApiClient();
