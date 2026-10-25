from __future__ import annotations

import json
import re
import sqlite3

import db

CREATE_COST = 100

class ClanError(Exception):
    pass

def init_tables(c) -> None:
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS clans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE COLLATE NOCASE,
            created INTEGER DEFAULT (strftime('%s','now')),
            treasure_yens INTEGER DEFAULT 0,
            treasure_gems INTEGER DEFAULT 0,
            treasure_crystals INTEGER DEFAULT 0,
            announcement TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS clan_members(
            user_id INTEGER PRIMARY KEY,
            clan_id INTEGER NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clan_raids(
            clan_id INTEGER NOT NULL,
            boss_name TEXT NOT NULL,
            hp INTEGER,
            max_hp INTEGER,
            damage_json TEXT,
            active INTEGER DEFAULT 0,
            PRIMARY KEY(clan_id, boss_name)
        );
        """
    )

def _valid_name(name: str) -> str:
    name = " ".join((name or "").split())
    if not re.fullmatch(r"[A-Za-z0-9 ]{3,16}", name):
        raise ClanError("Clan names are 3 to 16 letters or numbers.")
    return name

def membership(user_id: int):
    with db.conn() as c:
        return c.execute(
            "SELECT m.clan_id, k.name, m.role, k.treasure_yens, k.treasure_gems, k.treasure_crystals, k.announcement "
            "FROM clan_members m JOIN clans k ON k.id = m.clan_id WHERE m.user_id = ?",
            (user_id,),
        ).fetchone()

def clan_by_name(name: str):
    if not name:
        return None
    with db.conn() as c:
        return c.execute("SELECT * FROM clans WHERE name = ? COLLATE NOCASE", (name.strip(),)).fetchone()

def members(clan_id: int) -> list:
    with db.conn() as c:
        return c.execute(
            """
            SELECT m.user_id, m.role, p.first_name, p.username
            FROM clan_members m
            LEFT JOIN players p ON p.user_id = m.user_id
            WHERE m.clan_id = ?
            ORDER BY CASE m.role WHEN 'leader' THEN 0 WHEN 'officer' THEN 1 ELSE 2 END, p.first_name
            """,
            (clan_id,),
        ).fetchall()

def _role_of(user_id: int, clan_id: int):
    with db.conn() as c:
        row = c.execute("SELECT role FROM clan_members WHERE user_id = ? AND clan_id = ?", (user_id, clan_id)).fetchone()
        return row["role"] if row else None

def _require(actor: int, clan_id: int, allowed: tuple) -> str:
    role = _role_of(actor, clan_id)
    if role not in allowed:
        raise ClanError("You don't have permission for that.")
    return role

def create(user_id: int, name: str) -> int:
    name = _valid_name(name)
    if membership(user_id):
        raise ClanError("Leave your current clan before creating a new one.")
    if clan_by_name(name):
        raise ClanError("That clan name is already taken.")
    if not db.spend(user_id, "crystals", CREATE_COST):
        raise ClanError(f"A clan costs {CREATE_COST} crystals.")
    with db.conn() as c:
        cur = c.execute("INSERT INTO clans(name, treasure_yens, treasure_gems, treasure_crystals) VALUES(?,?,?,?)", (name, 0, 0, 0))
        clan_id = cur.lastrowid
        c.execute("INSERT INTO clan_members(user_id, clan_id, role) VALUES(?,?,'leader')", (user_id, clan_id))
    return clan_id

def join(user_id: int, name: str) -> int:
    if membership(user_id):
        raise ClanError("Leave your current clan first.")
    clan = clan_by_name(name)
    if clan is None:
        raise ClanError("No clan with that name.")
    with db.conn() as c:
        c.execute("INSERT INTO clan_members(user_id, clan_id, role) VALUES(?,?,'member')", (user_id, clan["id"]))
    return clan["id"]

def add(actor: int, target: int) -> None:
    m = membership(actor)
    if m is None:
        raise ClanError("You are not in a clan.")
    _require(actor, m["clan_id"], ("leader", "officer"))
    if membership(target):
        raise ClanError("That player is already in a clan.")
    with db.conn() as c:
        c.execute("INSERT INTO clan_members(user_id, clan_id, role) VALUES(?,?,'member')", (target, m["clan_id"]))

def remove(actor: int, target: int) -> None:
    m = membership(actor)
    if m is None:
        raise ClanError("You are not in a clan.")
    if membership(target) is None or membership(target)["clan_id"] != m["clan_id"]:
        raise ClanError("That player is not in your clan.")
    if actor == target:
        raise ClanError("Use /clan leave to leave.")
    my_role = _require(actor, m["clan_id"], ("leader", "officer"))
    their_role = _role_of(target, m["clan_id"])
    if their_role == "leader":
        raise ClanError("You cannot remove the leader.")
    if my_role == "officer" and their_role != "member":
        raise ClanError("Officers can only remove members.")
    with db.conn() as c:
        c.execute("DELETE FROM clan_members WHERE user_id = ?", (target,))

def promote(actor: int, target: int) -> None:
    m = membership(actor)
    if m is None:
        raise ClanError("You are not in a clan.")
    if membership(target) is None or membership(target)["clan_id"] != m["clan_id"]:
        raise ClanError("That player is not in your clan.")
    _require(actor, m["clan_id"], ("leader",))
    if _role_of(target, m["clan_id"]) != "member":
        raise ClanError("Only members can be promoted to officer.")
    with db.conn() as c:
        c.execute("UPDATE clan_members SET role='officer' WHERE user_id=?", (target,))

def demote(actor: int, target: int) -> None:
    m = membership(actor)
    if m is None:
        raise ClanError("You are not in a clan.")
    if membership(target) is None or membership(target)["clan_id"] != m["clan_id"]:
        raise ClanError("That player is not in your clan.")
    _require(actor, m["clan_id"], ("leader",))
    if _role_of(target, m["clan_id"]) != "officer":
        raise ClanError("Only officers can be demoted.")
    with db.conn() as c:
        c.execute("UPDATE clan_members SET role='member' WHERE user_id=?", (target,))

def transfer(actor: int, target: int) -> None:
    m = membership(actor)
    if m is None:
        raise ClanError("You are not in a clan.")
    if membership(target) is None or membership(target)["clan_id"] != m["clan_id"]:
        raise ClanError("That player is not in your clan.")
    _require(actor, m["clan_id"], ("leader",))
    with db.conn() as c:
        c.execute("UPDATE clan_members SET role='officer' WHERE user_id=?", (actor,))
        c.execute("UPDATE clan_members SET role='leader' WHERE user_id=?", (target,))

def leave(user_id: int) -> str:
    m = membership(user_id)
    if m is None:
        raise ClanError("You are not in a clan.")
    others = [r for r in members(m["clan_id"]) if r["user_id"] != user_id]
    if _role_of(user_id, m["clan_id"]) == "leader" and others:
        raise ClanError("Give leadership away first with /clan transfer then leave.")
    with db.conn() as c:
        c.execute("DELETE FROM clan_members WHERE user_id=?", (user_id,))
        if not others:
            c.execute("DELETE FROM clans WHERE id=?", (m["clan_id"],))
            return "disbanded"
    return "left"

def disband(user_id: int) -> None:
    m = membership(user_id)
    if m is None:
        raise ClanError("You are not in a clan.")
    _require(user_id, m["clan_id"], ("leader",))
    with db.conn() as c:
        c.execute("DELETE FROM clan_members WHERE clan_id=?", (m["clan_id"],))
        c.execute("DELETE FROM clans WHERE id=?", (m["clan_id"],))

def top_clans(limit: int = 10) -> list:
    with db.conn() as c:
        return c.execute(
            "SELECT k.name, COUNT(m.user_id) AS n FROM clans k LEFT JOIN clan_members m ON m.clan_id = k.id GROUP BY k.id ORDER BY n DESC, k.name LIMIT ?",
            (limit,),
        ).fetchall()

def set_announcement(clan_id: int, text: str) -> None:
    with db.conn() as c:
        c.execute("UPDATE clans SET announcement=? WHERE id=?", (text, clan_id))

def get_announcement(clan_id: int) -> str:
    with db.conn() as c:
        row = c.execute("SELECT announcement FROM clans WHERE id=?", (clan_id,)).fetchone()
        return row["announcement"] if row else ""

def add_treasure(clan_id: int, yens: int = 0, gems: int = 0, crystals: int = 0) -> None:
    with db.conn() as c:
        c.execute(
            "UPDATE clans SET treasure_yens = treasure_yens + ?, treasure_gems = treasure_gems + ?, treasure_crystals = treasure_crystals + ? WHERE id=?",
            (yens, gems, crystals, clan_id),
        )

def clan_raid_state(clan_id: int):
    with db.conn() as c:
        return c.execute("SELECT * FROM clan_raids WHERE clan_id=? AND active=1", (clan_id,)).fetchone()

def clan_raid_start(clan_id: int, boss_name: str, hp: int, dmg: int) -> None:
    with db.conn() as c:
        c.execute(
            "INSERT INTO clan_raids(clan_id, boss_name, hp, max_hp, damage_json, active) VALUES(?,?,?, ?, ?, 1) "
            "ON CONFLICT(clan_id, boss_name) DO UPDATE SET hp=excluded.hp, max_hp=excluded.max_hp, damage_json=excluded.damage_json, active=1",
            (clan_id, boss_name, hp, hp, json.dumps({}),),
        )

def clan_raid_hit(clan_id: int, user_id: int, damage: int):
    with db.conn() as c:
        row = c.execute("SELECT * FROM clan_raids WHERE clan_id=? AND active=1", (clan_id,)).fetchone()
        if row is None:
            return None
        dmg_by = json.loads(row["damage_json"] or "{}")
        dmg_by[str(user_id)] = dmg_by.get(str(user_id), 0) + damage
        hp = max(0, row["hp"] - damage)
        defeated = hp == 0
        c.execute(
            "UPDATE clan_raids SET hp=?, damage_json=?, active=? WHERE clan_id=? AND boss_name=?",
            (hp, json.dumps(dmg_by), 0 if defeated else 1, clan_id, row["boss_name"]),
        )
        return hp, defeated, dmg_by, row["boss_name"]

def clan_raid_claim(clan_id: int):
    with db.conn() as c:
        row = c.execute("SELECT * FROM clans WHERE id=?", (clan_id,)).fetchone()
        if row is None:
            return None
        rewards = {
            "yens": row["treasure_yens"],
            "gems": row["treasure_gems"],
            "crystals": row["treasure_crystals"],
        }
        return rewards
