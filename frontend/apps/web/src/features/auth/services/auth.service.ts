import { api } from "@/services/api/interceptor";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterResponse {
  id: string;
  username: string;
  email: string;
}
export interface UserResponse {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
}

export const AuthService = {
  login(credentials: LoginRequest) {
    return api.post<LoginResponse>(
      "/auth/login",
      credentials,
      false
    );
  },

  register(data: RegisterRequest) {
    return api.post<RegisterResponse>(
      "/auth/register",
      data,
      false
    );
  },

  me() {
    return api.get<UserResponse>("/auth/me");
  },
};