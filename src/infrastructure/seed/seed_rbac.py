import hashlib
import secrets

from pymongo import MongoClient

from src.infrastructure.config.settings import Settings

PERMISSIONS: list[dict[str, str]] = [
    {"code": "hhh:contracts:read", "description": "Read contracts"},
    {"code": "hhh:contracts:write", "description": "Create and update contracts"},
    {"code": "hhh:contracts:delete", "description": "Delete contracts"},
    {"code": "hhh:locations:read", "description": "Read locations"},
    {"code": "hhh:locations:write", "description": "Create and update locations"},
    {"code": "hhh:locations:delete", "description": "Delete locations"},
    {"code": "hhh:commodities:read", "description": "Read commodities"},
    {"code": "hhh:commodities:write", "description": "Create and update commodities"},
    {"code": "hhh:commodities:delete", "description": "Delete commodities"},
    {"code": "hhh:ships:read", "description": "Read ships"},
    {"code": "hhh:ships:write", "description": "Create and update ships"},
    {"code": "hhh:ships:delete", "description": "Delete ships"},
    {"code": "hhh:graphs:read", "description": "Read graphs"},
    {"code": "hhh:graphs:write", "description": "Create and update graphs"},
    {"code": "hhh:graphs:delete", "description": "Delete graphs"},
    {"code": "hhh:routes:read", "description": "Read routes"},
    {"code": "hhh:routes:write", "description": "Create and update routes"},
    {"code": "hhh:routes:delete", "description": "Delete routes"},
    {"code": "auth:users:read", "description": "Read users"},
    {"code": "auth:users:write", "description": "Create and update users"},
    {"code": "auth:users:admin", "description": "Administer users"},
    {"code": "auth:rbac:manage", "description": "Manage RBAC configuration"},
    {"code": "auth:settings:manage", "description": "Manage portal settings"},
]

ROLES: list[dict[str, object]] = [
    # --- Auth roles ---
    {
        "name": "Auth Admin",
        "description": "Full auth administration: user CRUD, RBAC management",
        "permission_codes": [
            "auth:users:read",
            "auth:users:write",
            "auth:users:admin",
            "auth:rbac:manage",
            "auth:settings:manage",
        ],
    },
    {
        "name": "Auth User Manager",
        "description": "Read and write access to user accounts",
        "permission_codes": [
            "auth:users:read",
            "auth:users:write",
        ],
    },
    # --- HHH roles (per sub-module) ---
    {
        "name": "HHH Contracts Manager",
        "description": "Full access to contracts",
        "permission_codes": [
            "hhh:contracts:read",
            "hhh:contracts:write",
            "hhh:contracts:delete",
        ],
    },
    {
        "name": "HHH Locations Manager",
        "description": "Full access to locations",
        "permission_codes": [
            "hhh:locations:read",
            "hhh:locations:write",
            "hhh:locations:delete",
        ],
    },
    {
        "name": "HHH Commodities Manager",
        "description": "Full access to commodities",
        "permission_codes": [
            "hhh:commodities:read",
            "hhh:commodities:write",
            "hhh:commodities:delete",
        ],
    },
    {
        "name": "HHH Ships Manager",
        "description": "Full access to ships",
        "permission_codes": [
            "hhh:ships:read",
            "hhh:ships:write",
            "hhh:ships:delete",
        ],
    },
    {
        "name": "HHH Graphs Manager",
        "description": "Full access to graphs",
        "permission_codes": [
            "hhh:graphs:read",
            "hhh:graphs:write",
            "hhh:graphs:delete",
        ],
    },
    {
        "name": "HHH Routes Manager",
        "description": "Full access to routes",
        "permission_codes": [
            "hhh:routes:read",
            "hhh:routes:write",
            "hhh:routes:delete",
        ],
    },
    {
        "name": "HHH Viewer",
        "description": "Read-only access to all HHH resources",
        "permission_codes": [
            "hhh:contracts:read",
            "hhh:locations:read",
            "hhh:commodities:read",
            "hhh:ships:read",
            "hhh:graphs:read",
            "hhh:routes:read",
        ],
    },
]

GROUPS: list[dict[str, object]] = [
    {
        "name": "Admins",
        "description": "Full system access. For administrators.",
        "role_names": [
            "Auth Admin",
            "HHH Contracts Manager",
            "HHH Locations Manager",
            "HHH Commodities Manager",
            "HHH Ships Manager",
            "HHH Graphs Manager",
            "HHH Routes Manager",
        ],
        "auto_assign_apps": [],
    },
    {
        "name": "Users",
        "description": "Default group for new registered users. Read access + can create contracts.",
        "role_names": [
            "HHH Viewer",
            "HHH Contracts Manager",
        ],
        "auto_assign_apps": ["hhh-frontend"],
    },
    {
        "name": "Content Managers",
        "description": "Full content management across all HHH modules + user management.",
        "role_names": [
            "Auth User Manager",
            "HHH Contracts Manager",
            "HHH Locations Manager",
            "HHH Commodities Manager",
            "HHH Ships Manager",
            "HHH Graphs Manager",
            "HHH Routes Manager",
        ],
        "auto_assign_apps": [],
    },
]


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}:{hashed.hex()}"


def seed(settings: Settings | None = None) -> None:
    if settings is None:
        settings = Settings()

    client: MongoClient = MongoClient(settings.mongo_uri)
    try:
        db = client[settings.mongo_db]

        permissions_col = db["permissions"]
        roles_col = db["roles"]
        groups_col = db["groups"]
        users_col = db["users"]

        # --- Permissions ---
        perm_id_map: dict[str, str] = {}
        for perm in PERMISSIONS:
            existing = permissions_col.find_one({"code": perm["code"]})
            if existing:
                perm_id_map[perm["code"]] = str(existing["_id"])
            else:
                result = permissions_col.insert_one({"code": perm["code"], "description": perm["description"]})
                perm_id_map[perm["code"]] = str(result.inserted_id)
        print(f"Permissions: {len(perm_id_map)} ready")

        # --- Roles ---
        role_id_map: dict[str, str] = {}
        for role_def in ROLES:
            name = str(role_def["name"])
            existing = roles_col.find_one({"name": name})
            if existing:
                role_id_map[name] = str(existing["_id"])
            else:
                permission_codes = role_def["permission_codes"]
                assert isinstance(permission_codes, list)
                permission_ids = [perm_id_map[code] for code in permission_codes]
                result = roles_col.insert_one(
                    {
                        "name": name,
                        "description": role_def["description"],
                        "permission_ids": permission_ids,
                    }
                )
                role_id_map[name] = str(result.inserted_id)
        print(f"Roles: {len(role_id_map)} ready")

        # --- Groups ---
        group_id_map: dict[str, str] = {}
        for group_def in GROUPS:
            name = str(group_def["name"])
            existing = groups_col.find_one({"name": name})
            if existing:
                group_id_map[name] = str(existing["_id"])
            else:
                role_names = group_def["role_names"]
                assert isinstance(role_names, list)
                role_ids = [role_id_map[rn] for rn in role_names]
                auto_assign_apps = group_def.get("auto_assign_apps", [])
                assert isinstance(auto_assign_apps, list)
                result = groups_col.insert_one(
                    {
                        "name": name,
                        "description": group_def["description"],
                        "role_ids": role_ids,
                        "auto_assign_apps": auto_assign_apps,
                    }
                )
                group_id_map[name] = str(result.inserted_id)
        print(f"Groups: {len(group_id_map)} ready")

        # --- Admin User ---
        admin_exists = users_col.find_one({"username": "admin"})
        if not admin_exists:
            hashed = _hash_password(settings.admin_password)
            users_col.insert_one(
                {
                    "username": "admin",
                    "hashed_password": hashed,
                    "group_ids": [group_id_map["Admins"]],
                    "is_active": True,
                    "rsi_handle": "HexadianAdmin",
                    "rsi_verified": False,
                    "rsi_verification_code": None,
                }
            )
            print("Admin user created")
        else:
            print("Admin user already exists")

        print("Seed complete")
    finally:
        client.close()


if __name__ == "__main__":
    seed()
