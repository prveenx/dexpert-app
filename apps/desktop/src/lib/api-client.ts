export class ApiClient {
  private static instance: ApiClient;
  private port: number | null = null;

  private constructor() {
    const params = new URLSearchParams(window.location.search);
    const portParam = params.get('port');
    if (portParam) {
      this.port = parseInt(portParam, 10);
    }
  }

  public static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  private async getHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = await (window as any).dexpert?.auth?.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private getBaseUrl(): string {
    return `http://127.0.0.1:${this.port || 48765}/api`;
  }

  public async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.getBaseUrl()}${path}`, {
      method: 'GET',
      headers: await this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  public async post<T>(path: string, body: any): Promise<T> {
    const response = await fetch(`${this.getBaseUrl()}${path}`, {
      method: 'POST',
      headers: await this.getHeaders(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  public async patch<T>(path: string, body: any): Promise<T> {
    const response = await fetch(`${this.getBaseUrl()}${path}`, {
      method: 'PATCH',
      headers: await this.getHeaders(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  public async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${this.getBaseUrl()}${path}`, {
      method: 'DELETE',
      headers: await this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }
}
