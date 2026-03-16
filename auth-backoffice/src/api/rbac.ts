import type {
  Permission,
  PermissionCreate,
  PermissionUpdate,
  Role,
  RoleCreate,
  RoleUpdate,
  Group,
  GroupCreate,
  GroupUpdate,
} from "@/types/rbac";

const API_BASE = "/api/auth";

// Permissions
export async function listPermissions(): Promise<Permission[]> {
  const response = await fetch(`${API_BASE}/permissions`);
  if (!response.ok) {
    throw new Error(`Failed to list permissions: ${response.statusText}`);
  }
  return response.json() as Promise<Permission[]>;
}

export async function createPermission(data: PermissionCreate): Promise<Permission> {
  const response = await fetch(`${API_BASE}/permissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create permission: ${response.statusText}`);
  }
  return response.json() as Promise<Permission>;
}

export async function updatePermission(id: string, data: PermissionUpdate): Promise<Permission> {
  const response = await fetch(`${API_BASE}/permissions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update permission: ${response.statusText}`);
  }
  return response.json() as Promise<Permission>;
}

export async function deletePermission(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/permissions/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete permission: ${response.statusText}`);
  }
}

// Roles
export async function listRoles(): Promise<Role[]> {
  const response = await fetch(`${API_BASE}/roles`);
  if (!response.ok) {
    throw new Error(`Failed to list roles: ${response.statusText}`);
  }
  return response.json() as Promise<Role[]>;
}

export async function getRole(id: string): Promise<Role> {
  const response = await fetch(`${API_BASE}/roles/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to get role: ${response.statusText}`);
  }
  return response.json() as Promise<Role>;
}

export async function createRole(data: RoleCreate): Promise<Role> {
  const response = await fetch(`${API_BASE}/roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create role: ${response.statusText}`);
  }
  return response.json() as Promise<Role>;
}

export async function updateRole(id: string, data: RoleUpdate): Promise<Role> {
  const response = await fetch(`${API_BASE}/roles/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update role: ${response.statusText}`);
  }
  return response.json() as Promise<Role>;
}

export async function deleteRole(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/roles/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete role: ${response.statusText}`);
  }
}

// Groups
export async function listGroups(): Promise<Group[]> {
  const response = await fetch(`${API_BASE}/groups`);
  if (!response.ok) {
    throw new Error(`Failed to list groups: ${response.statusText}`);
  }
  return response.json() as Promise<Group[]>;
}

export async function getGroup(id: string): Promise<Group> {
  const response = await fetch(`${API_BASE}/groups/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to get group: ${response.statusText}`);
  }
  return response.json() as Promise<Group>;
}

export async function createGroup(data: GroupCreate): Promise<Group> {
  const response = await fetch(`${API_BASE}/groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create group: ${response.statusText}`);
  }
  return response.json() as Promise<Group>;
}

export async function updateGroup(id: string, data: GroupUpdate): Promise<Group> {
  const response = await fetch(`${API_BASE}/groups/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update group: ${response.statusText}`);
  }
  return response.json() as Promise<Group>;
}

export async function deleteGroup(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/groups/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete group: ${response.statusText}`);
  }
}
