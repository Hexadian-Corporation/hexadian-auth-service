export interface Permission {
  _id: string;
  code: string;
  description: string;
}

export interface PermissionCreate {
  code: string;
  description: string;
}

export interface Role {
  _id: string;
  name: string;
  description: string;
  permission_ids: string[];
}

export interface RoleCreate {
  name: string;
  description: string;
  permission_ids: string[];
}

export interface Group {
  _id: string;
  name: string;
  description: string;
  role_ids: string[];
  auto_assign_apps: string[];
}

export interface GroupCreate {
  name: string;
  description: string;
  role_ids: string[];
  auto_assign_apps: string[];
}
