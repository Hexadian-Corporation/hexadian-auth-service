export interface User {
  _id: string;
  username: string;
  group_ids: string[];
  is_active: boolean;
  rsi_handle: string;
  rsi_verified: boolean;
}

export interface UserCreate {
  username: string;
  password: string;
  rsi_handle: string;
}

export interface UserUpdate {
  username?: string;
  rsi_handle?: string;
}
