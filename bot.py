from __future__ import annotations

import json
import os
import random
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import clans
import db
import game_data as G

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

EXPLORE_STATES = {}

def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

def is_admin(uid: int) -> bool:
    p = db.player(uid)
    return bool(p and p["admin"])

def ensure_player_for_update(update: Update):
    uid = update.effective_user.id
    db.ensure_player(uid, update.effective_user.first_name or "Player", update.effective_user.username)

def resolve_target_id(args: list[str], update: Update):
    if update.message and update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        if u and not u.is_bot:
            return u.id
    if not args:
        return None
    token = args[0]
    if token.startswith("@"):
        row = db.player_by_username(token[1:])
        return row["user_id"] if row else None
    if token.isdigit():
        return int(token)
    return None

def parse_amount(value: str) -> int:
    try:
        amount = int(value)
    except ValueError:
        return 0
    return max(1, amount)

def resource_name(name: str) -> str | None:
    aliases = {
        "yen": "yens", "yens": "yens",
        "gem": "gems", "gems": "gems",
        "crystal": "crystals", "crystals": "crystals",
        "ticket": "tickets", "tickets": "tickets",
        "skill_point": "skill_points", "skill_points": "skill_points", "sp": "skill_points",
        "elite_key": "keys_elite", "elite_keys": "keys_elite",
        "boss_key": "keys_boss", "boss_keys": "keys_boss",
        "exp": "exp",
        "money": "yens",
    }
    key = (name or "").strip().lower()
    return aliases.get(key)

def get_world_multiplier(uid: int) -> float:
    p = db.player(uid)
    if not p:
        return 1.0
    world = p["travel"] or "Earth"
    return G.PLANETS.get(world, G.PLANETS["Earth"])["multiplier"]

def player_stats(uid: int) -> tuple[int, int, int, int]:
    p = db.player(uid)
    if not p:
        return (0, 0, 0, 0)

    lvl = db.level_of(p["exp"])
    atk = 10 + lvl * 3
    hp = 100 + lvl * 12

    if p["weapon"] in G.EQUIPMENT:
        atk += G.EQUIPMENT[p["weapon"]][1]
    if p["armor"] in G.EQUIPMENT:
        hp += G.EQUIPMENT[p["armor"]][1] * 2

    if p["equipped_char"]:
        matches = [row for row in db.characters(uid) if row["name"] == p["equipped_char"]]
        if matches:
            rarity = matches[0]["rarity"]
            atk += G.RARITY_ATK.get(rarity, 10)
            hp += G.RARITY_HP.get(rarity, 20)

    atk += sum(G.SKILL_ATK.get(s, 0) for s in db.skills(uid))
    atk += (int(p["rank"] or 1) * 10)
    hp += (int(p["rank"] or 1) * 20)
    return atk, hp, lvl, int(p["rank"] or 1)

def start_random_battle(player_hp: int, player_atk: int, enemy_hp: int, enemy_dmg: int, enrage: bool = False):
    log = []
    p_hp = player_hp
    e_hp = enemy_hp
    e_max = enemy_hp
    for rnd in range(1, 60):
        hit = max(5, int(player_atk * random.uniform(0.8, 1.35)))
        e_hp -= hit
        if e_hp <= 0:
            log.append(f"Round {rnd}: You hit for {hit}. Victory!")
            return True, max(1, p_hp), log
        mult = 1.3 if enrage and e_hp <= e_max // 2 else 1.0
        taken = max(5, int(enemy_dmg * mult * random.uniform(0.8, 1.25)))
        p_hp -= taken
        log.append(f"Round {rnd}: You hit for {hit}, took {taken}.")
        if p_hp <= 0:
            return False, 0, log
    return False, max(0, p_hp), log + ["Battle dragged on and you backed off."]

# -----------------------------------------------------------
# Start / help
# -----------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    db.ensure_player(uid, update.effective_user.first_name, update.effective_user.username)
    await update.message.reply_text(
        "Welcome to Dragon Battle RPG.\n\n"
        "Commands:\n"
        "/profile\n"
        "/explore\n"
        "/shop\n"
        "/buy <id> [qty]\n"
        "/inventory\n"
        "/gacha [qty]\n"
        "/mycharacters\n"
        "/team\n"
        "/equip <name>\n"
        "/skills\n"
        "/learn <skill>\n"
        "/wish\n"
        "/summon <elite|mythical|legendary>\n"
        "/daily\n"
        "/weekly\n"
        "/rankup\n"
        "/travel\n"
        "/fusion <char1> <char2>\n"
        "/clan\n"
        "/leaderboard\n"
        "/give <target> <amount> <resource>\n"
        "/admin_add\n"
        "/raid\n"
        "/raid_start\n"
        "/raid_attack\n"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "How to play:\n\n"
        "1. Travel to stronger planets to get higher rewards.\n"
        "2. Explore enemies to build stats and gear.\n"
        "3. Gacha for strong units.\n"
        "4. Use /rankup to unlock stronger growth.\n"
        "5. Fusion creates stronger combinations.\n"
        "6. Bosses, raids, and summons give rare rewards.\n"
    )
    await update.message.reply_text(text)

# -----------------------------------------------------------
# Profile
# -----------------------------------------------------------

async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    level = db.level_of(p["exp"])
    rank = int(p["rank"] or 1)
    attack, hp, _, _ = player_stats(uid)
    world = p["travel"] or "Earth"

    text = (
        f"Name: {escape(p['first_name'])}\n"
        f"Username: @{escape(p['username'] or 'unknown')}\n"
        f"Level: {level}\n"
        f"Rank: {rank} ({G.RANKS.get(rank, 'Unknown')})\n"
        f"World: {world}\n"
        f"EXP: {p['exp']}\n"
        f"Yens: {p['yens']}\n"
        f"Gems: {p['gems']}\n"
        f"Crystals: {p['crystals']}\n"
        f"Tickets: {p['tickets']}\n"
        f"Skill Points: {p['skill_points']}\n"
        f"Elite Keys: {p['keys_elite']}\n"
        f"Boss Keys: {p['keys_boss']}\n"
        f"Equipped Character: {escape(p['equipped_char'] or 'none')}\n"
        f"Weapon: {escape(p['weapon'] or 'none')}\n"
        f"Armor: {escape(p['armor'] or 'none')}\n"
        f"ATK: {attack}\n"
        f"HP: {hp}\n"
    )
    await update.message.reply_text(text)

# -----------------------------------------------------------
# Explore menu
# -----------------------------------------------------------

async def cmd_explore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    db.ensure_player(uid, update.effective_user.first_name, update.effective_user.username)
    EXPLORE_STATES[uid] = {"mode": "explore"}
    await update.message.reply_text(
        "Explore Menu:\n"
        "1. Battle\n"
        "2. Run away\n"
        "3. Info\n"
    )

async def handle_explore_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    uid = update.effective_user.id
    if uid not in EXPLORE_STATES:
        return

    choice = (update.message.text or "").strip()
    if choice not in {"1", "2", "3"}:
        return

    p = db.player(uid)
    if not p:
        return

    if choice == "1":
        world_mult = get_world_multiplier(uid)
        enemy = random.choice(G.NPCS)
        name, hp, dmg, reward = enemy
        player_atk, player_hp, _, _ = player_stats(uid)
        won, left_hp, log = start_random_battle(player_hp, player_atk, hp, dmg)
        if won:
            reward_total = int(reward * world_mult * (1 + (int(p["rank"] or 1) * 0.2)))
            db.give(uid, yens=reward_total, exp=60, skill_points=5)
            if random.random() < 0.25:
                db.give(uid, gems=random.randint(1, 4))
            if random.random() < 0.10:
                db.give(uid, crystals=1)
            if random.random() < 0.15:
                db.give(uid, tickets=1)
            if random.random() < 0.15:
                star = random.choice(list(G.DRAGON_BALL_STARS))
                db.add_dragon_ball(uid, star)
            if random.random() < 0.18:
                item = random.choice(list(G.EQUIPMENT))
                db.add_item(uid, item)
            db.set_field(uid, "npc_streak", (p["npc_streak"] or 0) + 1)
            await update.message.reply_text(
                f"Victory! You defeated {name}.\n"
                f"Reward: {reward_total} yens + 60 exp + 5 skill points\n"
                f"Battle log:\n{chr(10).join(log[-4:])}"
            )
        else:
            await update.message.reply_text(
                f"Defeat. {name} won.\nBattle log:\n{chr(10).join(log[-4:])}"
            )
    elif choice == "2":
        await update.message.reply_text("You ran away safely.")
    elif choice == "3":
        world = p["travel"] or "Earth"
        mult = get_world_multiplier(uid)
        await update.message.reply_text(
            "Explore Info:\n"
            f"Current world: {world}\n"
            f"World multiplier: {mult}x\n"
            "Boss appears every 15 wins.\n"
            "Higher worlds give stronger rewards.\n"
        )

    EXPLORE_STATES.pop(uid, None)

# -----------------------------------------------------------
# Shop
# -----------------------------------------------------------

async def cmd_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    lines = [
        "Shop Categories:",
        "1. Weapons",
        "2. Armors",
        "3. Crystals",
        "4. Healing",
        "5. Fusion",
        "6. Keys & Tickets",
    ]
    await update.message.reply_text("\n".join(lines))

async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    args = context.args
    if len(args) < 2:
        qty = 1
        item_id = args[0]
    else:
        item_id = args[0]
        qty = max(1, int(args[1]))

    if not item_id.isdigit():
        await update.message.reply_text("Usage: /buy <id> [qty]")
        return

    sid = int(item_id)
    item = G.SHOP.get(sid)
    if not item:
        await update.message.reply_text("Invalid item ID.")
        return

    name, price, currency, kind, amount = item
    total = price * qty

    if not db.spend(uid, currency, total):
        await update.message.reply_text(f"Not enough {currency}.")
        return

    if kind == "weapon":
        db.add_item(uid, name, qty)
        await update.message.reply_text(f"You bought {name} x{qty}.")
    elif kind == "armor":
        db.add_item(uid, name, qty)
        await update.message.reply_text(f"You bought {name} x{qty}.")
    elif kind == "crystal":
        db.give(uid, crystals=amount * qty)
        await update.message.reply_text(f"You bought {amount * qty} crystals.")
    elif kind == "ticket":
        db.give(uid, tickets=amount * qty)
        await update.message.reply_text(f"You bought {amount * qty} gacha tickets.")
    elif kind == "heal":
        db.add_item(uid, name, qty)
        await update.message.reply_text(f"You bought {name} x{qty}.")
    elif kind == "fusion":
        db.add_item(uid, name, qty)
        await update.message.reply_text(f"You bought {name} x{qty}.")
    elif kind == "key_elite":
        db.give(uid, keys_elite=amount * qty)
        await update.message.reply_text(f"You bought {amount * qty} Elite Keys.")
    elif kind == "key_boss":
        db.give(uid, keys_boss=amount * qty)
        await update.message.reply_text(f"You bought {amount * qty} Boss Keys.")
    else:
        await update.message.reply_text("Purchase complete.")

# -----------------------------------------------------------
# Inventory / characters
# -----------------------------------------------------------

async def cmd_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    items = db.items(uid)
    if not items:
        await update.message.reply_text("Inventory empty.")
        return

    lines = ["Inventory", "Items:"]
    for item, qty in items:
        lines.append(f"- {item} x{qty}")
    await update.message.reply_text("\n".join(lines))

async def cmd_characters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    groups = db.characters_by_rarity(uid)
    lines = ["My Characters"]
    for rarity in ["omni", "mythical", "legendary", "epic", "rare", "common"]:
        names = groups.get(rarity, [])
        if not names:
            continue
        lines.append(f"\n{rarity.upper()}:")
        for name in names:
            lines.append(f"- {name}")
    await update.message.reply_text("\n".join(lines))

async def cmd_equipment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /equip <name>")
        return

    name = " ".join(args)
    if name in G.EQUIPMENT:
        if name not in [row["item"] for row in db.items(uid)]:
            await update.message.reply_text("You do not own that item.")
            return
        db.set_field(uid, "weapon" if G.EQUIPMENT[name][0] == "weapon" else "armor", name)
        await update.message.reply_text(f"Equipped {name}.")
        return

    if db.has_character(uid, name):
        db.set_field(uid, "equipped_char", name)
        await update.message.reply_text(f"Equipped {name}.")
        return

    await update.message.reply_text("You do not own that item or character.")

async def cmd_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    attack, hp, level, rank = player_stats(uid)
    text = (
        f"Team Info:\n"
        f"Character: {escape(p['equipped_char'] or 'none')}\n"
        f"Weapon: {escape(p['weapon'] or 'none')}\n"
        f"Armor: {escape(p['armor'] or 'none')}\n"
        f"ATK: {attack}\n"
        f"HP: {hp}\n"
        f"Level: {level}\n"
        f"Rank: {rank}\n"
    )
    await update.message.reply_text(text)

# -----------------------------------------------------------
# Gacha
# -----------------------------------------------------------

async def cmd_gacha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    args = context.args
    qty = 1
    if args and args[0].isdigit():
        qty = max(1, min(int(args[0]), 20))
    else:
        qty = 1

    if p["tickets"] < qty:
        await update.message.reply_text(f"You need {qty} tickets.")
        return

    if not db.spend(uid, "tickets", qty):
        await update.message.reply_text("Not enough tickets.")
        return

    rolls = []
    for _ in range(qty):
        rarity = random.choices(
            population=[name for name, _ in G.GACHA_RATES],
            weights=[w for _, w in G.GACHA_RATES],
            k=1,
        )[0]
        pool = [name for name, rarity_name in G.CHARACTERS if rarity_name == rarity]
        if not pool:
            continue
        name = random.choice(pool)
        db.add_character(uid, name, rarity)
        rolls.append(f"{name} ({rarity})")

    text = "Gacha Results:\n" + "\n".join(rolls)
    await update.message.reply_text(text)

# -----------------------------------------------------------
# Skills
# -----------------------------------------------------------

async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    lines = ["Skill Shop:"]
    for name, cost in G.SKILLS.items():
        lines.append(f"- {name}: {cost} skill points +{G.SKILL_ATK[name]} dmg")
    await update.message.reply_text("\n".join(lines))

async def cmd_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /learn <skill>")
        return
    name = " ".join(args)
    if name not in G.SKILLS:
        await update.message.reply_text("Skill not found.")
        return
    if p["skill_points"] < G.SKILLS[name]:
        await update.message.reply_text("Not enough skill points.")
        return
    if not db.spend(uid, "skill_points", G.SKILLS[name]):
        await update.message.reply_text("Not enough skill points.")
        return
    if db.add_skill(uid, name):
        await update.message.reply_text(f"Learned skill {name}.")
    else:
        await update.message.reply_text(f"You already know {name}.")

# -----------------------------------------------------------
# Wish
# -----------------------------------------------------------

async def cmd_wish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    if not db.take_one_of_each_dragon_ball(uid):
        await update.message.reply_text("You need one of each 1★ to 7★ Dragon Ball.")
        return

    roll = random.random()
    if roll < 0.12:
        rarity = "mythical"
        names = [n for n, r in G.CHARACTERS if r == rarity]
        name = random.choice(names)
        db.add_character(uid, name, rarity)
        result = f"a mythical character: {name}"
    elif roll < 0.30:
        db.add_item(uid, "Deadly Divine Sword")
        result = "a legendary weapon: Deadly Divine Sword"
    elif roll < 0.52:
        db.add_skill(uid, "Universe Breaker")
        result = "the skill: Universe Breaker"
    elif roll < 0.76:
        db.give(uid, yens=100000, gems=250, crystals=15, skill_points=20)
        result = "100,000 yens, 250 gems, 15 crystals, 20 skill points"
    else:
        db.give(uid, gems=500, crystals=20)
        result = "500 gems and 20 crystals"

    await update.message.reply_text(f"Shenron grants your wish: {result}.")

# -----------------------------------------------------------
# Summon
# -----------------------------------------------------------

async def cmd_summon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /summon <elite|mythical|legendary>")
        return

    kind = context.args[0].lower()
    data = G.SUMMONS.get(kind)
    if not data:
        await update.message.reply_text("Use elite, mythical, or legendary.")
        return

    boss_name, boss_hp, boss_dmg, reward_mult, key_col = data
    if p[key_col] <= 0:
        await update.message.reply_text(f"You need a {kind} key.")
        return

    if not db.spend(uid, key_col, 1):
        await update.message.reply_text(f"You need a {kind} key.")
        return

    player_atk, player_hp, _, _ = player_stats(uid)
    won, left_hp, log = start_random_battle(player_hp, player_atk, boss_hp, boss_dmg, True)
    if won:
        db.give(uid, yens=20000 * reward_mult, gems=50 * reward_mult, crystals=6 * reward_mult, exp=500 * reward_mult, skill_points=20 * reward_mult)
        if random.random() < 0.60:
            db.add_item(uid, random.choice(list(G.EQUIPMENT)))
        if random.random() < 0.30:
            db.add_skill(uid, random.choice(list(G.SKILLS)))
        if random.random() < 0.40:
            db.add_dragon_ball(uid, random.randint(1, 7))
        await update.message.reply_text(
            f"Boss defeated: {boss_name}\n"
            f"Rewards: {20000 * reward_mult} yens, {50 * reward_mult} gems, {6 * reward_mult} crystals, {500 * reward_mult} exp, +{20 * reward_mult} skill points\n"
            f"Battle log:\n{chr(10).join(log[-5:])}"
        )
    else:
        await update.message.reply_text(f"You lost to {boss_name}.\nBattle log:\n{chr(10).join(log[-5:])}")

# -----------------------------------------------------------
# Daily / weekly / rankup
# -----------------------------------------------------------

async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    result = db.claim_daily(uid)
    if result is None:
        await update.message.reply_text("Daily already claimed. Try again tomorrow.")
        return
    streak, rewards = result
    await update.message.reply_text(f"Daily reward claimed! Streak {streak}. Rewards: {rewards}")

async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    result = db.claim_weekly(uid)
    if result is None:
        await update.message.reply_text("Weekly already claimed. Try again next week.")
        return
    rewards, star = result
    await update.message.reply_text(f"Weekly reward claimed! Rewards: {rewards}\nDragon ball star: {star}")

async def cmd_rankup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    rank = int(p["rank"] or 1)
    max_rank = max(G.RANKS)
    if rank >= max_rank:
        await update.message.reply_text("You are already at the maximum rank.")
        return

    cost = G.RANKUP_CRYSTALS.get(rank)
    if cost is None:
        await update.message.reply_text("Rank system is not configured for this rank.")
        return

    if p["crystals"] < cost:
        await update.message.reply_text(f"Rank {rank} -> {rank + 1} needs {cost} crystals. You have {p['crystals']}.")
        return

    if not db.spend(uid, "crystals", cost):
        await update.message.reply_text("Not enough crystals.")
        return

    db.set_field(uid, "rank", rank + 1)
    db.give(uid, exp=250 * rank, skill_points=30 * rank)
    await update.message.reply_text(
        f"Rank up successful! You reached {G.RANKS[rank + 1]}.\n"
        f"EXP +{250 * rank}\n"
        f"Skill points +{30 * rank}\n"
        f"Attack and HP increase from rank growth."
    )

# -----------------------------------------------------------
# Travel
# -----------------------------------------------------------

async def cmd_travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    text = ["Travel Worlds:"]
    for idx, name in enumerate(G.PLANET_ORDER, 1):
        data = G.PLANETS[name]
        text.append(f"{idx}. {name} ({data['level_min']} - {data['level_max']}) x{data['multiplier']} rewards")
    text.append("Use /travel <planet number> to travel.")
    await update.message.reply_text("\n".join(text))

async def cmd_set_travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /travel <planet number>")
        return

    idx = int(args[0])
    names = list(G.PLANET_ORDER)
    if idx < 1 or idx > len(names):
        await update.message.reply_text("Planet not found.")
        return

    name = names[idx - 1]
    level = db.level_of(p["exp"])
    if level < G.PLANETS[name]["level_min"]:
        await update.message.reply_text(f"You need level {G.PLANETS[name]['level_min']} to travel to {name}.")
        return

    db.set_field(uid, "travel", name)
    await update.message.reply_text(f"Travel successful! You are now in {name}. Rewards are increased by {G.PLANETS[name]['multiplier']}x.")

# -----------------------------------------------------------
# Fusion
# -----------------------------------------------------------

async def cmd_fusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /fusion <character_1> <character_2>")
        return

    char1 = " ".join(args[:2])
    char2 = " ".join(args[2:4]) if len(args) >= 4 else args[1]

    if not db.has_character(uid, char1) or not db.has_character(uid, char2):
        await update.message.reply_text("Both characters must be in your collection.")
        return

    if char1 == char2:
        await update.message.reply_text("You cannot fuse the same character.")
        return

    if not any(item in [row["item"] for row in db.items(uid)] for item in ["Fusion Material", "Fusion Core", "Fusion Crystal", "Fusion Catalyst"]):
        await update.message.reply_text("You need at least one fusion material.")
        return

    material = random.choice(["Fusion Material", "Fusion Core", "Fusion Crystal", "Fusion Catalyst"])
    db.remove_item(uid, material, 1)

    rarity1 = next((row["rarity"] for row in db.characters(uid) if row["name"] == char1), "common")
    rarity2 = next((row["rarity"] for row in db.characters(uid) if row["name"] == char2), "common")

    result_rarity = "common"
    if rarity1 == "mythical" or rarity2 == "mythical":
        result_rarity = "mythical"
    elif rarity1 == "legendary" or rarity2 == "legendary":
        result_rarity = "legendary"
    elif rarity1 == "epic" or rarity2 == "epic":
        result_rarity = "epic"
    elif rarity1 == "rare" or rarity2 == "rare":
        result_rarity = "rare"

    result_name = f"{char1} + {char2}"
    db.add_character(uid, result_name, result_rarity)
    await update.message.reply_text(f"Fusion successful! You created {result_name} ({result_rarity}).")

# -----------------------------------------------------------
# Leaderboard
# -----------------------------------------------------------

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    with db.conn() as c:
        rows = c.execute("SELECT first_name, exp, rank FROM players ORDER BY exp DESC LIMIT 10").fetchall()
    if not rows:
        await update.message.reply_text("No players yet.")
        return
    lines = ["Leaderboard:"]
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. {row['first_name']} - EXP {row['exp']} - Rank {row['rank']}")
    await update.message.reply_text("\n".join(lines))

# -----------------------------------------------------------
# Give / admin
# -----------------------------------------------------------

async def cmd_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /give <target> <amount> <resource>")
        return

    target_id = resolve_target_id(args[:1], update)
    if target_id is None:
        await update.message.reply_text("Target user not found.")
        return

    amount = parse_amount(args[1])
    if amount <= 0:
        await update.message.reply_text("Amount must be > 0.")
        return

    resource = resource_name(args[2])
    if resource is None:
        await update.message.reply_text("Invalid resource. Use yens, gems, crystals, tickets, skill_points, keys_elite, keys_boss, exp.")
        return

    if uid != target_id and not is_admin(uid):
        await update.message.reply_text("You cannot give to others unless you are an admin.")
        return

    db.give(target_id, **{resource: amount})
    await update.message.reply_text(f"Gift sent to {target_id}: {amount} {resource}.")

async def cmd_admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    if not (is_owner(uid) or is_admin(uid)):
        await update.message.reply_text("You are not allowed to use admin commands.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Usage: /admin_add <target> <amount> <resource|item|character|skill|dragon_ball>\n"
            "Examples:\n"
            "/admin_add @friend 1000 gems\n"
            "/admin_add 123456789 5 crystals\n"
            "/admin_add 123456789 1 item Potion\n"
            "/admin_add 123456789 1 character Goku\n"
            "/admin_add 123456789 1 skill Kaioken\n"
            "/admin_add 123456789 2 dragon_ball 3"
        )
        return

    target_id = resolve_target_id(args[:1], update)
    if target_id is None:
        await update.message.reply_text("Player not found.")
        return

    amount = parse_amount(args[1])
    if amount <= 0:
        await update.message.reply_text("Amount must be > 0.")
        return

    kind = args[2].lower()
    extra = " ".join(args[3:]) if len(args) >= 4 else ""

    if kind in {"resource", "resource_name"}:
        resource = resource_name(args[3]) if len(args) >= 4 else None
        if resource is None:
            await update.message.reply_text("Invalid resource.")
            return
        db.give(target_id, **{resource: amount})
        await update.message.reply_text(f"Admin gave {amount} {resource} to {target_id}.")
        return

    if kind == "item":
        db.add_item(target_id, extra, amount)
        await update.message.reply_text(f"Admin added {amount}x {extra} to {target_id}.")
        return

    if kind == "character":
        db.add_character(target_id, extra, "legendary")
        await update.message.reply_text(f"Admin added character {extra} to {target_id}.")
        return

    if kind == "skill":
        db.add_skill(target_id, extra)
        await update.message.reply_text(f"Admin added skill {extra} to {target_id}.")
        return

    if kind == "dragon_ball":
        try:
            star = int(extra)
        except ValueError:
            await update.message.reply_text("Dragon ball star must be a number 1 to 7.")
            return
        if star < 1 or star > 7:
            await update.message.reply_text("Dragon ball star must be between 1 and 7.")
            return
        db.add_dragon_ball(target_id, star, amount)
        await update.message.reply_text(f"Admin added {amount}x {star}★ dragon balls to {target_id}.")
        return

    await update.message.reply_text("Unknown admin type.")

async def cmd_admin_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    if not (is_owner(uid) or is_admin(uid)):
        await update.message.reply_text("You are not allowed to use admin commands.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /admin_set <target> <field> <value>")
        return

    target_id = resolve_target_id(args[:1], update)
    if target_id is None:
        await update.message.reply_text("Target not found.")
        return

    field = resource_name(args[1])
    if field is None:
        await update.message.reply_text("Invalid field.")
        return

    value = parse_amount(args[2])
    db.set_field(target_id, field, value)
    await update.message.reply_text(f"Admin set {field} = {value} for {target_id}.")

# -----------------------------------------------------------
# Clan system
# -----------------------------------------------------------

async def cmd_clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_player_for_update(update)
    uid = update.effective_user.id
    p = db.player(uid)
    if not p:
        await update.message.reply_text("Use /start first.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Clan Menu:\n"
            "1. Create a clan\n"
            "2. Join a clan\n"
            "3. Info\n"
            "4. Members\n"
            "5. Manage\n"
            "6. Treasure\n"
            "7. Raid\n"
            "8. Announcement\n"
            "9. Invite\n"
            "Use: /clan create <name> | /clan join <name> | /clan info | /clan members | /clan manage | /clan treasure | /clan raid | /clan announce | /clan invite <target>"
        )
        return

    action = args[0].lower()
    if action == "create":
        if len(args) < 2:
            await update.message.reply_text("Usage: /clan create <name>")
            return
        name = " ".join(args[1:])
        try:
            clans.create(uid, name)
            await update.message.reply_text(f"Clan created: {name}")
        except clans.ClanError as exc:
            await update.message.reply_text(str(exc))
    elif action == "join":
        if len(args) < 2:
            await update.message.reply_text("Usage: /clan join <name>")
            return
        name = " ".join(args[1:])
        try:
            clans.join(uid, name)
            await update.message.reply_text(f"You joined {name}")
        except clans.ClanError as exc:
            await update.message.reply_text(str(exc))
    elif action == "info":
        row = clans.membership(uid)
        if row is None:
            await update.message.reply_text("You are not in a clan.")
            return
        await update.message.reply_text(
            f"Clan: {row['name']}\n"
            f"Role: {row['role']}\n"
            f"Treasure: Yens {row['treasure_yens']}, Gems {row['treasure_gems']}, Crystals {row['treasure_crystals']}\n"
            f"Announcement: {row['announcement'] or 'No announcement'}"
        )
    elif action == "members":
        row = clans.membership(uid)
        if row is None:
            await update.message.reply_text("You are not in a clan.")
            return
        rows = clans.members(row["clan_id"])
        lines = [f"Clan: {row['name']}"]
        for r in rows:
            lines.append(f"- {r['first_name']} ({r['role']})")
        await update.message.reply_text("\n".join(lines))
    elif action == "manage":
        row = clans.membership(uid)
        if row is None:
            await update.message.reply_text("You are not in a clan.")
            return
        role = row["role"]
        if role not in {"leader", "officer"}:
            await update.message.reply_text("Only leader/officer can manage clan.")
            return
        await update.message.reply_text(
            "Clan management:\n"
            "Leader/officer commands:\n"
            "/clan add <target>\n"
            "/clan remove <target>\n"
            "/clan promote <target>\n"
            "/clan demote <target>\n"
            "/clan transfer <target>\n"
            "/clan leave\n"
            "/clan disband confirm"
        )
    elif action == "treasure":
        row = clans.membership(uid)
        if row is None:
            await update.message.reply_text("You are not in a clan.")
            return
        clan = clans.clan_by_name(row["name"])
        if clan is None:
            await update.message.reply_text("Clan not found.")
            return
        await update.message.reply_text(
            f"Clan Treasure:\n"
            f"Yens: {clan['treasure_yens']}\n"
            f"Gems: {clan['treasure_gems']}\n"
            f"Crystals: {clan['treasure_crystals']}\n"
            f"Use /clan raid to start clan raid."
        )
    elif action == "raid":
        row = clans.membership(uid)
        if row is None:
            await update.message.reply_text("You are not in a clan.")
            return

        target_boss = "Perfect Cell"
        if len(context.args) >= 2:
            target_boss = " ".join(context.args[1:])
        if target_boss not in G.CLAN_RAIDS:
            await update.message.reply_text("Clan raid bosses: Perfect Cell, Frieza, Majin Buu, Beerus")
            return

        boss_info = G.CLAN_RAIDS[target_boss]
        mem = clans.membership(uid)
        clan_id = mem["clan_id"]
        raid_state = clans.clan_raid_state(clan_id)
        if raid_state is None:
            clans.clan_raid_start(clan_id, target_boss, boss_info["hp"], boss_info["dmg"])
            await update.message.reply_text(
                f"Clan raid started: {
