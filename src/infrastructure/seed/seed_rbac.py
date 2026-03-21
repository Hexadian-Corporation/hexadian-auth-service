import asyncio
import hashlib
import secrets

from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import Settings

PERMISSIONS: list[dict[str, str]] = [
    {"code": "hhh:contracts:read", "description": "Read contracts"},
    {"code": "hhh:contracts:write", "description": "Create and update contracts"},
    {"code": "hhh:contracts:delete", "description": "Delete contracts"},
    {"code": "hhh:maps:read", "description": "Read locations"},
    {"code": "hhh:maps:write", "description": "Create and update locations"},
    {"code": "hhh:maps:delete", "description": "Delete locations"},
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
    {"code": "auth:users:manage", "description": "Manage users"},
    {"code": "auth:groups:manage", "description": "Manage groups"},
    {"code": "auth:roles:manage", "description": "Manage roles"},
    {"code": "auth:permissions:manage", "description": "Manage permissions"},
    {"code": "auth:rbac:manage", "description": "Manage RBAC configuration"},
    {"code": "auth:settings:manage", "description": "Manage portal settings"},
    # --- Algorithm permissions ---
    {"code": "hhh:algorithm:dijkstra", "description": "Use Dijkstra shortest path algorithm"},
    {"code": "hhh:algorithm:astar", "description": "Use A* heuristic pathfinding algorithm"},
    {"code": "hhh:algorithm:aco", "description": "Use Ant Colony Optimization algorithm"},
    {"code": "hhh:algorithm:ford_fulkerson", "description": "Use Ford-Fulkerson max flow algorithm"},
    # --- Feature permissions (premium) ---
    {"code": "hhh:feature:gpu", "description": "GPU processing via WebGPU compute shaders"},
    {"code": "hhh:feature:step_by_step", "description": "Step-by-step route navigation screen"},
    {"code": "hhh:feature:multi_system", "description": "Multi-system routes across gateways"},
    {"code": "hhh:feature:export", "description": "Export route to image/PDF"},
    {"code": "hhh:feature:risk_analysis", "description": "Risk/benefit analysis (reward/collateral ratio)"},
    {"code": "hhh:feature:route_comparison", "description": "Compare distance vs time routes side by side"},
    {"code": "hhh:feature:history_unlimited", "description": "Unlimited flight plan history"},
    {"code": "hhh:feature:simultaneous_plans", "description": "Multiple simultaneous flight plans"},
    {"code": "hhh:feature:cargo_limit", "description": "Custom cargo limit below ship capacity"},
    {"code": "hhh:feature:distance_finder", "description": "Distance Finder: shortest path between any two locations"},
    # --- Import / sync permissions (M30) ---
    {"code": "hhh:locations:import", "description": "Bulk import locations"},
    {"code": "hhh:distances:import", "description": "Bulk import distances"},
    {"code": "hhh:ships:import", "description": "Bulk import ships"},
    {"code": "hhh:commodities:import", "description": "Bulk import commodities"},
    {"code": "hhh:contracts:import", "description": "Bulk import game contracts"},
    {"code": "hhh:contracts:clone", "description": "Clone a contract"},
    {"code": "hhh:data:full-sync", "description": "Full-sync mode (deprecate absent items)"},
    {"code": "hhh:data:sync", "description": "Trigger dataminer sync"},
]

ROLES: list[dict[str, object]] = [
    # --- Auth roles ---
    {
        "name": "Auth Admin",
        "description": "Full auth administration: user CRUD, RBAC management",
        "permission_codes": [
            "auth:users:manage",
            "auth:groups:manage",
            "auth:roles:manage",
            "auth:permissions:manage",
            "auth:rbac:manage",
            "auth:settings:manage",
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
        "name": "HHH Maps Manager",
        "description": "Full access to locations and distances",
        "permission_codes": [
            "hhh:maps:read",
            "hhh:maps:write",
            "hhh:maps:delete",
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
            "hhh:maps:read",
            "hhh:commodities:read",
            "hhh:ships:read",
            "hhh:graphs:read",
            "hhh:routes:read",
        ],
    },
    # --- Algorithm roles ---
    {
        "name": "HHH Algorithm User",
        "description": "Basic algorithm access: Dijkstra + route creation",
        "permission_codes": [
            "hhh:algorithm:dijkstra",
            "hhh:routes:write",
        ],
    },
    {
        "name": "HHH Algorithm Premium",
        "description": "Premium algorithm access: all optimization algorithms",
        "permission_codes": [
            "hhh:algorithm:dijkstra",
            "hhh:algorithm:astar",
            "hhh:algorithm:aco",
            "hhh:algorithm:ford_fulkerson",
        ],
    },
    # --- Data import / sync roles (M30) ---
    {
        "name": "HHH Data Import",
        "description": "Import and sync game data: locations, distances, ships, commodities, contracts",
        "permission_codes": [
            "hhh:locations:import",
            "hhh:distances:import",
            "hhh:ships:import",
            "hhh:commodities:import",
            "hhh:contracts:import",
            "hhh:contracts:clone",
            "hhh:data:full-sync",
            "hhh:data:sync",
        ],
    },
    # --- Feature roles (premium) ---
    {
        "name": "HHH Feature Premium",
        "description": "All premium frontend features for Hexadian Members+",
        "permission_codes": [
            "hhh:feature:gpu",
            "hhh:feature:step_by_step",
            "hhh:feature:multi_system",
            "hhh:feature:export",
            "hhh:feature:risk_analysis",
            "hhh:feature:route_comparison",
            "hhh:feature:history_unlimited",
            "hhh:feature:simultaneous_plans",
            "hhh:feature:cargo_limit",
            "hhh:feature:distance_finder",
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
            "HHH Maps Manager",
            "HHH Commodities Manager",
            "HHH Ships Manager",
            "HHH Graphs Manager",
            "HHH Routes Manager",
            "HHH Data Import",
            "HHH Algorithm Premium",
            "HHH Feature Premium",
        ],
        "auto_assign_apps": [],
    },
    {
        "name": "Users",
        "description": "Default group for new registered users. Read access + basic algorithm.",
        "role_names": [
            "HHH Viewer",
            "HHH Algorithm User",
        ],
        "auto_assign_apps": ["hhh-frontend"],
    },
    {
        "name": "Hexadian Members",
        "description": "Premium users with full algorithm and feature access.",
        "role_names": [
            "HHH Viewer",
            "HHH Algorithm Premium",
            "HHH Feature Premium",
        ],
        "auto_assign_apps": [],
    },
]


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}:{hashed.hex()}"


async def seed(settings: Settings | None = None) -> None:
    if settings is None:
        settings = Settings()

    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongo_uri)
    try:
        db = client[settings.mongo_db]

        permissions_col = db["permissions"]
        roles_col = db["roles"]
        groups_col = db["groups"]
        users_col = db["users"]

        # ==================== PHASE 1: Permissions ====================
        # Each permission is independent — parallelise get-or-create
        async def _ensure_permission(perm: dict[str, str]) -> tuple[str, str]:
            existing = await permissions_col.find_one({"code": perm["code"]})
            if existing:
                return perm["code"], str(existing["_id"])
            result = await permissions_col.insert_one({"code": perm["code"], "description": perm["description"]})
            return perm["code"], str(result.inserted_id)

        perm_pairs = await asyncio.gather(*[_ensure_permission(p) for p in PERMISSIONS])
        perm_id_map: dict[str, str] = dict(perm_pairs)
        print(f"Permissions: {len(perm_id_map)} ready")

        # ==================== PHASE 2: Roles ====================
        # All roles are independent given perm_id_map — parallelise
        async def _ensure_role(role_def: dict[str, object]) -> tuple[str, str]:
            name = str(role_def["name"])
            existing = await roles_col.find_one({"name": name})
            if existing:
                return name, str(existing["_id"])
            permission_codes = role_def["permission_codes"]
            assert isinstance(permission_codes, list)
            permission_ids = [perm_id_map[code] for code in permission_codes]
            result = await roles_col.insert_one(
                {
                    "name": name,
                    "description": role_def["description"],
                    "permission_ids": permission_ids,
                }
            )
            return name, str(result.inserted_id)

        role_pairs = await asyncio.gather(*[_ensure_role(r) for r in ROLES])
        role_id_map: dict[str, str] = dict(role_pairs)
        print(f"Roles: {len(role_id_map)} ready")

        # ==================== PHASE 3: Groups ====================
        # All groups are independent given role_id_map — parallelise
        async def _ensure_group(group_def: dict[str, object]) -> tuple[str, str]:
            name = str(group_def["name"])
            existing = await groups_col.find_one({"name": name})
            if existing:
                return name, str(existing["_id"])
            role_names = group_def["role_names"]
            assert isinstance(role_names, list)
            role_ids = [role_id_map[rn] for rn in role_names]
            auto_assign_apps = group_def.get("auto_assign_apps", [])
            assert isinstance(auto_assign_apps, list)
            result = await groups_col.insert_one(
                {
                    "name": name,
                    "description": group_def["description"],
                    "role_ids": role_ids,
                    "auto_assign_apps": auto_assign_apps,
                }
            )
            return name, str(result.inserted_id)

        group_pairs = await asyncio.gather(*[_ensure_group(g) for g in GROUPS])
        group_id_map: dict[str, str] = dict(group_pairs)
        print(f"Groups: {len(group_id_map)} ready")

        # --- Admin User ---
        admin_exists = await users_col.find_one({"username": "admin"})
        if not admin_exists:
            hashed = _hash_password(settings.admin_password)
            await users_col.insert_one(
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

        # --- Cleanup: remove stale permissions no longer in the spec ---
        current_codes = {p["code"] for p in PERMISSIONS}
        cleanup_result = await permissions_col.delete_many({"code": {"$nin": list(current_codes)}})
        if cleanup_result.deleted_count:
            print(f"Cleaned up {cleanup_result.deleted_count} stale permission(s)")

        # --- Cleanup: remove deprecated roles no longer in the spec ---
        current_role_names = {str(r["name"]) for r in ROLES}
        cleanup_result = await roles_col.delete_many({"name": {"$nin": list(current_role_names)}})
        if cleanup_result.deleted_count:
            print(f"Cleaned up {cleanup_result.deleted_count} stale role(s)")

        # --- Cleanup: remove deprecated groups no longer in the spec ---
        current_group_names = {str(g["name"]) for g in GROUPS}
        cleanup_result = await groups_col.delete_many({"name": {"$nin": list(current_group_names)}})
        if cleanup_result.deleted_count:
            print(f"Cleaned up {cleanup_result.deleted_count} stale group(s)")

        print("Seed complete")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed())
