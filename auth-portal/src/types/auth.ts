import type { TokenResponse } from "@hexadian-corporation/auth-core";

export type { TokenResponse };

export interface RegisterRequest {
  username: string;
  password: string;
  rsi_handle: string;
  app_id?: string;
  app_signature?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthorizeRequest {
  username: string;
  password: string;
  redirect_uri: string;
  state?: string;
}

export interface AuthorizeResponse {
  code: string;
  state: string;
  redirect_uri: string;
}

export interface TokenExchangeRequest {
  code: string;
  redirect_uri: string;
}

export interface User {
  _id: string | null;
  username: string;
  roles: string[];
  is_active: boolean;
  rsi_handle: string | null;
  rsi_verified: boolean;
}

export interface VerificationStartRequest {
  rsi_handle: string;
}

export interface VerificationStartResponse {
  verification_code: string | null;
  verified: boolean;
  message: string;
}

export interface VerificationConfirmRequest {
  rsi_handle: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface ForgotPasswordRequest {
  username: string;
  rsi_handle: string;
}

export interface ForgotPasswordResponse {
  verification_code: string;
  message: string;
}

export interface ConfirmForgotPasswordRequest {
  username: string;
  rsi_handle: string;
  new_password: string;
}
