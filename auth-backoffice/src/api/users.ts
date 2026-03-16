import type { User, UserCreate, UserUpdate } from "@/types/user";
import { authFetch } from "@/lib/auth";

const API_BASE = "/api/auth";

export async function listUsers(): Promise<User[]> {
  const response = await authFetch(`${API_BASE}/users`);
  if (!response.ok) {
    throw new Error(`Failed to list users: ${response.statusText}`);
  }
  return response.json() as Promise<User[]>;
}

export async function getUser(id: string): Promise<User> {
  const response = await authFetch(`${API_BASE}/users/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to get user: ${response.statusText}`);
  }
  return response.json() as Promise<User>;
}

export async function createUser(data: UserCreate): Promise<User> {
  const response = await authFetch(`${API_BASE}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create user: ${response.statusText}`);
  }
  return response.json() as Promise<User>;
}

export async function updateUser(id: string, data: UserUpdate): Promise<User> {
  const response = await authFetch(`${API_BASE}/users/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update user: ${response.statusText}`);
  }
  return response.json() as Promise<User>;
}

export async function deleteUser(id: string): Promise<void> {
  const response = await authFetch(`${API_BASE}/users/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete user: ${response.statusText}`);
  }
}

export async function resetPassword(id: string, newPassword: string): Promise<void> {
  const response = await authFetch(`${API_BASE}/users/${id}/password-reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_password: newPassword }),
  });
  if (!response.ok) {
    throw new Error(`Failed to reset password: ${response.statusText}`);
  }
}
