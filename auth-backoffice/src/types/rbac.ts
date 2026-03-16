export interface Permission {
  id: string;
  name: string;
  description: string;
}

export interface PermissionCreate {
  name: string;
  description: string;
}

export interface PermissionUpdate {
  description?: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
}

export interface RoleCreate {
  name: string;
  description: string;
  permissions?: string[];
}

export interface RoleUpdate {
  description?: string;
  permissions?: string[];
}

export interface Group {
  id: string;
  name: string;
  description: string;
  roles: string[];
}

export interface GroupCreate {
  name: string;
  description: string;
  roles?: string[];
}

export interface GroupUpdate {
  description?: string;
  roles?: string[];
}
