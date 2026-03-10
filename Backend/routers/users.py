from fastapi import APIRouter, HTTPException, Path, Body, Header
router = APIRouter()
import database
from models import CreateUserRequest, UpdateUserRequest

VALID_ROLES = ("Local", "Regional", "Global", "Admin")


async def _require_admin(x_user_id: int) -> None:
    """Raise 403 if the user is not Admin. Call with X-User-Id from header."""
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (x_user_id,)) as cur:
            row = await cur.fetchone()
        if not row or row[0] != "Admin":
            raise HTTPException(status_code=403, detail="Only Admin users can perform this action")
    finally:
        await conn.close()


@router.get("/users")
async def get_users():
    """Get all users (any role can list users)."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("SELECT id, name, email, role, country, therapeutic_area, region FROM users ORDER BY id") as cur:
            users = await cur.fetchall()
        return {"users": [dict(row) for row in users]}
    finally:
        await conn.close()


@router.post("/users", status_code=201)
async def create_user(
    request: CreateUserRequest = Body(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Create a new user. Admin only. Header: X-User-Id (must be Admin)."""
    await _require_admin(x_user_id)
    if request.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {VALID_ROLES}")
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT id FROM users WHERE email = ?", (request.email,)) as cur:
            if await cur.fetchone():
                raise HTTPException(status_code=400, detail="Email already in use")
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        await conn.execute(
            """INSERT INTO users (name, email, role, country, therapeutic_area, region) VALUES (?, ?, ?, ?, ?, ?)""",
            (request.name, request.email.strip(), request.role, request.country or None, request.therapeutic_area or None, request.region or None),
        )
        await conn.commit()
        async with conn.execute("SELECT id, name, email, role, country, therapeutic_area, region FROM users WHERE id = last_insert_rowid()") as cur:
            row = await cur.fetchone()
        return dict(row) if row else {"message": "User created"}
    finally:
        await conn.close()


@router.put("/users/{user_id}")
async def update_user(
    user_id: int = Path(...),
    request: UpdateUserRequest = Body(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Update a user. Admin only. Header: X-User-Id (must be Admin)."""
    await _require_admin(x_user_id)
    updates = []
    params = []
    if request.name is not None:
        updates.append("name = ?")
        params.append(request.name)
    if request.email is not None:
        updates.append("email = ?")
        params.append(request.email.strip())
    if request.role is not None:
        if request.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"role must be one of {VALID_ROLES}")
        updates.append("role = ?")
        params.append(request.role)
    if request.country is not None:
        updates.append("country = ?")
        params.append(request.country)
    if request.therapeutic_area is not None:
        updates.append("therapeutic_area = ?")
        params.append(request.therapeutic_area)
    if request.region is not None:
        updates.append("region = ?")
        params.append(request.region)
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    params.append(user_id)
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cur:
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
        if request.email is not None:
            async with conn.execute("SELECT id FROM users WHERE email = ? AND id != ?", (request.email, user_id)) as cur:
                if await cur.fetchone():
                    raise HTTPException(status_code=400, detail="Email already in use")
        await conn.execute("UPDATE users SET " + ", ".join(updates) + " WHERE id = ?", tuple(params))
        await conn.commit()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("SELECT id, name, email, role, country, therapeutic_area, region FROM users WHERE id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        return dict(row)
    finally:
        await conn.close()


@router.delete("/users/{user_id}", status_code=200)
async def delete_user(
    user_id: int = Path(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Delete a user. Admin only. Fails if user is referenced in pcrs or notifications. Header: X-User-Id (must be Admin)."""
    await _require_admin(x_user_id)
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cur:
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
        for table, col in [
            ("pcrs", "submitted_by"), ("pcrs", "local_approved_by"), ("pcrs", "regional_approved_by"),
            ("pcrs", "escalated_by"), ("pcrs", "global_approved_by"), ("notifications", "user_id"),
            ("chat_participants", "user_id"), ("messages", "sender_id"),
        ]:
            async with conn.execute(f"SELECT 1 FROM {table} WHERE {col} = ? LIMIT 1", (user_id,)) as cur:
                if await cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"User is referenced in {table}; cannot delete")
        await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await conn.commit()
        return {"message": "User deleted", "user_id": user_id}
    finally:
        await conn.close()

