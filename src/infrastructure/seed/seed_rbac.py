import hashlib
import secrets

from pymongo import MongoClient

from src.infrastructure.config.settings import Settings

PERMISSIONS: list[dict[str, str]] = [
    {"code": "contracts:read", "description": "Read contracts"},
    {"code": "contracts:write", "description": "Create and update contracts"},
    {"code": "contracts:delete", "description": "Delete contracts"},
    {"code": "locations:read", "description": "Read locations"},
    {"code": "locations:write", "description": "Create and update locations"},
    {"code": "locations:delete", "description": "Delete locations"},
    {"code": "commodities:read", "description": "Read commodities"},
    {"code": "commodities:write", "description": "Create and update commodities"},
    {"code": "commodities:delete", "description": "Delete commodities"},
    {"code": "ships:read", "description": "Read ships"},
    {"code": "ships:write", "description": "Create and update ships"},
    {"code": "ships:delete", "description": "Delete ships"},
    {"code": "graphs:read", "description": "Read graphs"},
    {"code": "graphs:write", "description": "Create and update graphs"},
    {"code": "graphs:delete", "description": "Delete graphs"},
    {"code": "routes:read", "description": "Read routes"},
    {"code": "routes:write", "description": "Create and update routes"},
    {"code": "routes:delete", "description": "Delete routes"},
    {"code": "users:read", "description": "Read users"},
    {"code": "users:write", "description": "Create and update users"},
    {"code": "users:admin", "description": "Administer users"},
    {"code": "rbac:manage", "description": "Manage RBAC configuration"},
]

ROLES: list[dict[str, object]] = [
    {
        "name": "Super Admin",
        "description": "Full system access",
        "permission_codes": [p["code"] for p in PERMISSIONS],
    },
    {
        "name": "Member",
        "description": "Default role for registered users",
        "permission_codes": [
            "contracts:read",
            "locations:read",
            "commodities:read",
            "ships:read",
            "graphs:read",
            "routes:read",
            "users:read",
            "contracts:write",
        ],
    },
    {
        "name": "Content Manager",
        "description": "Read and write access to all content",
        "permission_codes": [
            "contracts:read",
            "contracts:write",
            "locations:read",
            "locations:write",
            "commodities:read",
            "commodities:write",
            "ships:read",
            "ships:write",
            "graphs:read",
            "graphs:write",
            "routes:read",
            "routes:write",
            "users:read",
            "users:write",
        ],
    },
]

GROUPS: list[dict[str, object]] = [
    {
        "name": "Admins",
        "description": "Full system access. For administrators.",
        "role_names": ["Super Admin"],
    },
    {
        "name": "Users",
        "description": "Default group for new registered users. Read access + can create contracts.",
        "role_names": ["Member"],
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
            result = groups_col.insert_one(
                {
                    "name": name,
                    "description": group_def["description"],
                    "role_ids": role_ids,
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

    client.close()
    print("Seed complete")


if __name__ == "__main__":
    seed()
