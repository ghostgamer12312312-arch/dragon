
6) game_data.py
```python name=game_data.py
from __future__ import annotations

# -----------------------------------------------------------
# Game config
# -----------------------------------------------------------

STARTING_RESOURCES = {
    "yens": 500000,
    "gems": 20000,
    "crystals": 5555,
    "tickets": 130,
    "skill_points": 120,
    "keys_elite": 10,
    "keys_boss": 10,
    "exp": 0,
}

PLANETS = {
    "Earth": {"level_min": 1, "level_max": 20, "multiplier": 1.0},
    "Hell": {"level_min": 21, "level_max": 39, "multiplier": 2.0},
    "Kai Planet": {"level_min": 40, "level_max": 59, "multiplier": 3.0},
    "Supreme Kai Planet": {"level_min": 60, "level_max": 79, "multiplier": 4.0},
    "Beerus Planet": {"level_min": 80, "level_max": 99, "multiplier": 5.0},
    "Universe 7": {"level_min": 100, "level_max": 999, "multiplier": 7.0},
}
PLANET_ORDER = ["Earth", "Hell", "Kai Planet", "Supreme Kai Planet", "Beerus Planet", "Universe 7"]

# -----------------------------------------------------------
# NPCs
# -----------------------------------------------------------

NPCS = [
    ("Bandit Rookie", 70, 8, 140),
    ("Wild Wolf", 100, 12, 220),
    ("Rogue Ninja", 150, 16, 360),
    ("Iron Golem", 210, 20, 520),
    ("Shadow Sorcerer", 270, 24, 720),
    ("Dark Knight", 350, 30, 980),
    ("Storm Samurai", 420, 36, 1500),
    ("Void Hunter", 500, 44, 1850),
    ("Planetary Raider", 620, 52, 2300),
    ("Cosmic Assassin", 760, 62, 2900),
    ("Galaxy Thug", 860, 70, 3400),
    ("Planet Breaker", 980, 80, 4200),
    ("Star Dragon Raider", 1100, 90, 4700),
]

NPC_STREAK_FOR_BOSS = 15

BOSS = {
    "name": "Frieza Force Commander",
    "hp": 1800,
    "dmg": 60,
    "yens": 9000,
    "gems": 900,
    "crystals": 60,
    "tickets": 5,
    "skill_points": 20,
}

# -----------------------------------------------------------
# Characters
# -----------------------------------------------------------

CHARACTERS = [
    # Mythical x10
    ("Beerus", "mythical"),
    ("Whis", "mythical"),
    ("Goku Black", "mythical"),
    ("Broly", "mythical"),
    ("Golden Frieza", "mythical"),
    ("Super Saiyan 4 Gogeta", "mythical"),
    ("Vegito Blue", "mythical"),
    ("Fusion Zamasu", "mythical"),
    ("Omega Shenron", "mythical"),
    ("Grand Zeno", "mythical"),

    # Legendary x10
    ("Goku", "legendary"),
    ("Vegeta", "legendary"),
    ("Jiren", "legendary"),
    ("Majin Buu", "legendary"),
    ("Vegeta Blue", "legendary"),
    ("King Vegeta", "legendary"),
    ("Caulifla", "legendary"),
    ("Moro", "legendary"),
    ("Gogeta", "legendary"),
    ("Super Buu", "legendary"),

    # Epic x10
    ("Gohan", "epic"),
    ("Piccolo", "epic"),
    ("Frieza", "epic"),
    ("Cell", "epic"),
    ("Future Trunks", "epic"),
    ("Bardock", "epic"),
    ("Cabba", "epic"),
    ("King Cold", "epic"),
    ("Buu", "epic"),
    ("Basil", "epic"),

    # Rare x10
    ("Trunks", "rare"),
    ("Krillin", "rare"),
    ("Android 18", "rare"),
    ("Hit", "rare"),
    ("Toppo", "rare"),
    ("Nappa", "rare"),
    ("Raditz", "rare"),
    ("Tien", "rare"),
    ("Pan", "rare"),
    ("Videl", "rare"),

    # Omni Kings x8
    ("Omni King Zeno", "omni"),
    ("Omni King Future Zeno", "omni"),
    ("Omni King Vegeks", "omni"),
    ("Omni King Cereal", "omni"),
    ("Omni King Yemma", "omni"),
    ("Omni King Constellation", "omni"),
    ("Omni King Universe 11", "omni"),
    ("Omni King Time", "omni"),
]

RARITY_ORDER = {
    "common": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
    "mythical": 5,
    "omni": 6,
}

RARITY_ATK = {
    "common": 100,
    "rare": 135,
    "epic": 163,
    "legendary": 199,
    "mythical": 255,
    "omni": 342,
}

RARITY_HP = {
    "common": 150,
    "rare": 250,
    "epic": 321,
    "legendary": 431,
    "mythical": 555,
    "omni": 780,
}

GACHA_RATES = [
    ("common", 38),
    ("rare", 28),
    ("epic", 16),
    ("legendary", 10),
    ("mythical", 6),
    ("omni", 2),
]

# -----------------------------------------------------------
# Weapons (10+)
# -----------------------------------------------------------

WEAPONS = {
    "Wooden Sword": 8,
    "Iron Sword": 12,
    "Saiyan Blade": 25,
    "Kamehameha Blade": 42,
    "Ultra Sword": 60,
    "God Breaker": 80,
    "Destructo Blade": 100,
    "Black Hole Blade": 120,
    "Galaxy Cutter": 150,
    "Crusher Edge": 185,
    "Supernova Blade": 220,
    "Deadly Divine Sword": 260,
}

EQUIPMENT = {
    "Wooden Sword": ("weapon", 108),
    "Iron Sword": ("weapon", 112),
    "Saiyan Blade": ("weapon", 125),
    "Kamehameha Blade": ("weapon", 412),
    "Ultra Sword": ("weapon", 160),
    "God Breaker": ("weapon", 180),
    "Destructo Blade": ("weapon", 221),
    "Black Hole Blade": ("weapon", 220),
    "Galaxy Cutter": ("weapon", 250),
    "Crusher Edge": ("weapon", 285),
    "Supernova Blade": ("wweapon, 320),
    "Deadly Divine Sword": ("weapon", 360),
    "Leather Vest": ("armor", 114),
    "Steel Armor": ("armor", 126),
    "Saiyan Armor": ("armor", 144),
    "God Armor": ("armor", 170),
    "Battle Armor": ("armor", 192),
    "Celestial Armor": ("armor", 220),
    "Doom Armor": ("armor", 250),
    "Ultra Guard": ("armor", 280),
    "Katchin Armor": ("armor", 320),
    "Mystic Guard": ("armor", 360),
    "Grand Priest Suit": ("armor", 320),
    "Divine Battle Suit": ("armor", 380),
    "Heavenly Guardian Suit": ("armor", 430),
    "Kaio Suit": ("armor", 500),
}

# -----------------------------------------------------------
# Shop
# -----------------------------------------------------------

SHOP = {
    1: ("Wooden Sword", 500, "yens", "weapon", 1),
    2: ("Iron Sword", 2000, "yens", "weapon", 1),
    3: ("Saiyan Blade", 12000, "yens", "weapon", 1),
    4: ("Kamehameha Blade", 26000, "yens", "weapon", 1),
    5: ("Destructo Blade", 40000, "yens", "weapon", 1),
    6: ("Black Hole Blade", 68000, "yens", "weapon", 1),
    7: ("Galaxy Cutter", 98000, "yens", "weapon", 1),
    8: ("Crusher Edge", 130000, "yens", "weapon", 1),
    9: ("Supernova Blade", 180000, "yens", "weapon", 1),
    10: ("Deadly Divine Sword", 260000, "yens", "weapon", 1),

    11: ("Leather Vest", 600, "yens", "armor", 1),
    12: ("Steel Armor", 2200, "yens", "armor", 1),
    13: ("Saiyan Armor", 13000, "yens", "armor", 1),
    14: ("God Armor", 50000, "yens", "armor", 1),
    15: ("Battle Armor", 80000, "yens", "armor", 1),
    16: ("Celestial Armor", 120000, "yens", "armor", 1),
    17: ("Doom Armor", 180000, "yens", "armor", 1),
    18: ("Ultra Guard", 220000, "yens", "armor", 1),
    19: ("Grand Priest Suit", 300000, "yens", "armor", 1),
    20: ("Divine Battle Suit", 420000, "yens", "armor", 1),

    21: ("Crystal", 30, "gems", "crystal", 1),
    22: ("Gacha Ticket", 60, "gems", "ticket", 1),
    23: ("Potion", 100, "yens", "heal", 1),
    24: ("Mega Potion", 250, "yens", "heal", 1),
    25: ("Revive", 350, "yens", "heal", 1),
    26: ("Senzu Bean", 800, "yens", "heal", 1),

    27: ("Elite Key", 1200, "yens", "key_elite", 1),
    28: ("Boss Key", 2600, "yens", "key_boss", 1),

    29: ("Fusion Material", 250, "gems", "fusion", 1),
    30: ("Fusion Core", 500, "gems", "fusion", 1),
    31: ("Fusion Crystal", 1200, "gems", "fusion", 1),
    32: ("Fusion Catalyst", 2500, "gems", "fusion", 1),
}

# -----------------------------------------------------------
# Skills
# -----------------------------------------------------------

SKILLS = {
    "Ki Blast": 9,
    "Kaioken": 6,
    "Instant Transmission": 10,
    "Spirit Bomb": 18,
    "Solar Flare": 12,
    "Destructo Disk": 16,
    "Ultra Instinct": 22,
    "Final Flash": 20,
    "God Kamehameha": 25,
    "Big Bang Attack": 28,
    "Black Hole Attack": 32,
    "Time Skip": 20,
    "Nova Burst": 26,
    "Dragon Fist": 30,
    "Final Explosion": 35,
    "Kamehameha Wave": 38,
    "Heavenly Rush": 42,
    "Universe Breaker": 48,
    "Halo Blast": 50,
    "Godly Burst": 54,
}

SKILL_ATK = {
    "Ki Blast": 100,
    "Kaioken": 116,
    "Instant Transmission": 114,
    "Spirit Bomb": 192,
    "Solar Flare": 171,
    "Destructo Disk": 190,
    "Ultra Instinct": 215,
    "Final Flash": 128,
    "God Kamehameha": 222,
    "Big Bang Attack": 214,
    "Black Hole Attack": 224,
    "Time Skip": 132,
    "Nova Burst": 220,
    "Dragon Fist": 198,
    "Final Explosion": 292,
    "Kamehameha Wave": 225,
    "Heavenly Rush": 390,
    "Universe Breaker": 344,
    "Halo Blast": 368,
    "Godly Burst": 465,
}

# -----------------------------------------------------------
# Dragon balls
# -----------------------------------------------------------

DRAGON_BALL_STARS = range(1, 8)

# -----------------------------------------------------------
# Summons
# -----------------------------------------------------------

SUMMONS = {
    "elite": ("Elite Ginyu Force", 260000, 11000, 3000, "keys_elite"),
    "mythical": ("Mythical Perfect Cell", 700000, 18000, 1116, "keys_boss"),
    "legendary": ("God of Destruction", 1100000, 2600, 1000, "keys_boss"),
}

# -----------------------------------------------------------
# Clan raid bosses
# -----------------------------------------------------------

CLAN_RAIDS = {
    "Perfect Cell": {
        "hp": 40000,
        "dmg": 399,
        "reward_yens": 25000000,
        "reward_gems": 50000,
        "reward_crystals": 3000,
        "reward_tickets": 50,
        "reward_skill_points": 100,
    },
    "Frieza": {
        "hp": 70000,
        "dmg": 1200,
        "reward_yens": 500000000,
        "reward_gems": 90000,
        "reward_crystals": 6000,
        "reward_tickets": 70,
        "reward_skill_points": 120,
    },
    "Majin Buu": {
        "hp": 95000,
        "dmg": 1700,
        "reward_yens": 80000000,
        "reward_gems": 120000,
        "reward_crystals": 8000,
        "reward_tickets": 100,
        "reward_skill_points": 150,
    },
    "Beerus": {
        "hp": 140000,
        "dmg": 2400,
        "reward_yens": 120000000,
        "reward_gems": 180000,
        "reward_crystals": 10000,
        "reward_tickets": 150,
        "reward_skill_points": 190,
    },
}

# -----------------------------------------------------------
# Raid
# -----------------------------------------------------------

RAID = {
    "hp": 120000,
    "dmg": 500,
    "reward_mult": 1000,
    "attack_cooldown_s": 0,
}

# -----------------------------------------------------------
# Ranks
# -----------------------------------------------------------

RANKS = {
    1: "Beginner",
    2: "Novice",
    3: "King",
    4: "Emperor",
    5: "Demigod",
    6: "Immortal",
    7: "Titan",
    8: "Oracle",
    9: "Celestial",
    10: "God",
}

RANKUP_CRYSTALS = {
    1: 500,
    2: 4000,
    3: 20000,
    4: 70000,
    5: 150000,
    6: 300000,
    7: 600000,
    8: 1000000,
    9: 2000000,
}

CLAN_CREATE_CRYSTALS = 100

FUSION_MATERIALS = {
    "Fusion Material": 1,
    "Fusion Core": 2,
    "Fusion Crystal": 3,
    "Fusion Catalyst": 4,
}
