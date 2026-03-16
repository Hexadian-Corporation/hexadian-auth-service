export interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  is_active: boolean;
  rsi_handle: string | null;
  rsi_verified: boolean;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  roles?: string[];
}

export interface UserUpdate {
  email?: string;
  roles?: string[];
  is_active?: boolean;
}
