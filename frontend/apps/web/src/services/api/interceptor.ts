const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api/v1";

export interface RequestOptions extends RequestInit {
  auth?: boolean;
}

class ApiClient {
  private isRefreshing = false;

  private refreshPromise: Promise<void> | null = null;

  private getAccessToken(): string | null {
    if (typeof window === "undefined") {
      return null;
    }

    return localStorage.getItem("access_token");
  }

  private getRefreshToken(): string | null {
    if (typeof window === "undefined") {
      return null;
    }

    return localStorage.getItem("refresh_token");
  }

  private saveTokens(
    accessToken: string,
    refreshToken: string,
  ) {
    localStorage.setItem(
      "access_token",
      accessToken,
    );

    localStorage.setItem(
      "refresh_token",
      refreshToken,
    );
  }

  private clearTokens() {
    localStorage.removeItem(
      "access_token",
    );

    localStorage.removeItem(
      "refresh_token",
    );
  }

  private async refreshAccessToken() {
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;

    this.refreshPromise = (async () => {
      const refreshToken =
        this.getRefreshToken();

      if (!refreshToken) {
        this.clearTokens();

        throw new Error(
          "Refresh token missing.",
        );
      }

      const response = await fetch(
        `${API_BASE_URL}/auth/refresh`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            refresh_token:
              refreshToken,
          }),
        },
      );

      if (!response.ok) {
        this.clearTokens();

        throw new Error(
          "Refresh failed.",
        );
      }

      const tokens =
        await response.json();

      this.saveTokens(
        tokens.access_token,
        tokens.refresh_token,
      );
    })();

    try {
      await this.refreshPromise;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {},
    retry = true,
  ): Promise<T> {
    const {
      auth = true,
      headers,
      ...config
    } = options;

    const requestHeaders =
      new Headers(headers);

    requestHeaders.set(
      "Content-Type",
      "application/json",
    );

    if (auth) {
      const token =
        this.getAccessToken();

      if (token) {
        requestHeaders.set(
          "Authorization",
          `Bearer ${token}`,
        );
      }
    }

    const response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        ...config,
        headers: requestHeaders,
      },
    );

    if (
      response.status === 401 &&
      auth &&
      retry
    ) {
      try {
        await this.refreshAccessToken();

        return this.request<T>(
          endpoint,
          options,
          false,
        );
      } catch {
        this.clearTokens();

        if (
          typeof window !== "undefined"
        ) {
          window.location.href =
            "/login";
        }

        throw new Error(
          "Session expired."
        );
      }
    }

    if (!response.ok) {
      let message =
        "Request failed.";

      try {
        const error =
          await response.json();

        message =
          error.detail ??
          message;
      } catch {}

      throw new Error(
        message,
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  get<T>(
    endpoint: string,
    auth = true,
  ) {
    return this.request<T>(
      endpoint,
      {
        method: "GET",
        auth,
      },
    );
  }

  post<T>(
    endpoint: string,
    body?: unknown,
    auth = true,
  ) {
    return this.request<T>(
      endpoint,
      {
        method: "POST",
        auth,
        body: body
          ? JSON.stringify(body)
          : undefined,
      },
    );
  }

  put<T>(
    endpoint: string,
    body?: unknown,
    auth = true,
  ) {
    return this.request<T>(
      endpoint,
      {
        method: "PUT",
        auth,
        body: body
          ? JSON.stringify(body)
          : undefined,
      },
    );
  }

  patch<T>(
    endpoint: string,
    body?: unknown,
    auth = true,
  ) {
    return this.request<T>(
      endpoint,
      {
        method: "PATCH",
        auth,
        body: body
          ? JSON.stringify(body)
          : undefined,
      },
    );
  }

  delete<T>(
    endpoint: string,
    auth = true,
  ) {
    return this.request<T>(
      endpoint,
      {
        method: "DELETE",
        auth,
      },
    );
  }
}

export const api =
  new ApiClient();