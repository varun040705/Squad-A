const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api/v1";

export interface RequestOptions extends RequestInit {
  auth?: boolean;
}

class ApiClient {
  private getAccessToken(): string |null {
    if (typeof window === "undefined") {
      return null;
    }

    return localStorage.getItem("access_token");
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      auth = true,
      headers,
      ...config
    } = options;

    const requestHeaders = new Headers(headers);

    requestHeaders.set(
      "Content-Type",
      "application/json"
    );

    if (auth) {
      const token = this.getAccessToken();

      if (token) {
        requestHeaders.set(
          "Authorization",
          `Bearer ${token}`
        );
      }
    }

    const response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        ...config,
        headers: requestHeaders,
      }
    );

    if (!response.ok) {
      let message = "Request failed";

      try {
        const error = await response.json();

        message = error.detail || message;
      } catch {}

      throw new Error(message);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  get<T>(
    endpoint: string,
    auth = true
  ) {
    return this.request<T>(endpoint, {
      method: "GET",
      auth,
    });
  }

  post<T>(
    endpoint: string,
    body?: unknown,
    auth = true
  ) {
    return this.request<T>(endpoint, {
      method: "POST",
      auth,
      body: body
        ? JSON.stringify(body)
        : undefined,
    });
  }

  put<T>(
    endpoint: string,
    body?: unknown,
    auth = true
  ) {
    return this.request<T>(endpoint, {
      method: "PUT",
      auth,
      body: body
        ? JSON.stringify(body)
        : undefined,
    });
  }

  patch<T>(
    endpoint: string,
    body?: unknown,
    auth = true
  ) {
    return this.request<T>(endpoint, {
      method: "PATCH",
      auth,
      body: body
        ? JSON.stringify(body)
        : undefined,
    });
  }

  delete<T>(
    endpoint: string,
    auth = true
  ) {
    return this.request<T>(endpoint, {
      method: "DELETE",
      auth,
    });
  }
}

export const api = new ApiClient();