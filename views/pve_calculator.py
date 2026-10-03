import math

import pandas as pd
import streamlit as st

st.title("PVE Calculator")
st.caption(
    "Estimate hits to kill, kills per hour, average time per drop, "
    "and expected drops over 100 hours."
)

# ----------------------------------------------------------------------
# 1. STATIC GAME DATA
# ----------------------------------------------------------------------
AUTUMN_MULTIPLIER = 1.5

PICKAXES = {
    "Molten Pickaxe": 1,
    "Hellfire Pickaxe": 5,
    "Magma Mauler Pickaxe": 10,
    "Blazebreaker Pickaxe": 100,
    "Ashen Axe Pickaxe": 500,
    "Netherfang Pickaxe": 1_000,
    "Flarestrike Pickaxe": 2_500,
    "Brimstone Blade Pickaxe": 5_000,
    "Forged Lava Pickaxe": 10_000,
    "Emberforge Pickaxe": 20_000,
    "Cinderstrike Pickaxe": 50_000,
    "Netherite Nightmare Pickaxe": 100_000,
    "Volcanic Bite Pickaxe": 250_000,
    "1* Volcanic Bite Pickaxe": 255_000,
    "2* Volcanic Bite Pickaxe": 260_000,
}

BLUDGEONS = {
    "Basic Bludgeon": 285_000,
    "Handy Bludgeon": 320_000,
    "Advanced Bludgeon": 355_000,
    "Hefty Bludgeon": 390_000,
    "Expert Bludgeon": 425_000,
    "Deadly Bludgeon": 460_000,
    "Fleshripper Bludgeon": 500_000,
}

BEDROCK_TALISMANS = {
    "None": ("pct", 0.0),
    "Bedrock Talisman I": ("flat", 250),
    "Bedrock Talisman II": ("pct", 0.15),
    "Bedrock Talisman III": ("pct", 0.35),
    "Ash Talisman": ("pct", 0.35),
}

T3_MOBS = {
    "Fire Slinger": {
        "hp": 100,
        "ash": 1,
        "drops": [
            ("T4 Keys", 2_500),
            ("Slinger Core", 5_000),
            ("Blazebound Talisman", 1_000),
            ("Embercore Talisman", 10_000),
        ],
    },
    "Fire Mage": {
        "hp": 10_000,
        "ash": 25,
        "drops": [
            ("T4 Keys", 2_500),
            ("Mage Core", 10_000),
            ("Embercore Talisman", 1_000),
            ("Talisman of Infernal Flames", 50_000),
        ],
    },
    "Zhurak the Emberborn": {
        "hp": 1_000_000,
        "ash": 1_500,
        "drops": [
            ("T4 Keys", 1_500),
            ("Emberborn Core", 50_000),
            ("Talisman of Infernal Flames", 10_000),
            ("Abyssflame Talisman", 20_000),
            ("Primordial Flame Talisman", 100_000),
        ],
    },
}

T4_MOBS = {
    "Frozen Alex": {
        "hp": 2_000_000,
        "ash": 2_500,
        "drops": [
            ("T4 Keys", 750),
            ("Frozen Alex Core", 20_000),
            ("Talisman of Frost", 5_000),
            ("Glacierheart Talisman", 20_000),
        ],
    },
    "Frozen Captain": {
        "hp": 5_000_000,
        "ash": 7_500,
        "drops": [
            ("T4 Keys", 333),
            ("Captain Core", 25_000),
            ("Glacierheart Talisman", 5_000),
            ("Cryoshade Talisman", 20_000),
        ],
    },
}

T5_MOBS = {
    "Corruptonaut": {
        "hp": 20_000_000,
        "ash": 33_000,
        "drops": [
            ("T4 Keys", 110),
            ("T5 Keys", 2_000),
            ("1* Conjunction", 5_000),
            ("2* Conjunction", 20_000),
            ("Harded Andecite Talisman", 10_000),
        ],
    },
    "Stardust Wizard": {
        "hp": 50_000_000,
        "ash": 95_000,
        "drops": [
            ("T4 Keys", 40),
            ("T5 Keys", 550),
            ("2* Conjunction", 5_000),
            ("3* Conjunction", 20_000),
            ("Boiling Core Talisman", 10_000),
        ],
    },
    "Space Pirate": {
        "hp": 175_000_000,
        "ash": 380_000,
        "drops": [
            ("T4 Keys", 15),
            ("T5 Keys", 140),
            ("3* Conjunction", 5_000),
            ("4* Conjunction", 20_000),
            ("Solar Crown Talisman", 10_000),
        ],
    },
    "Galactic Terror": {
        "hp": 500_000_000,
        "ash": 1_250_000,
        "drops": [
            ("T4 Keys", 6),
            ("T5 Keys", 40),
            ("4* Conjunction", 5_000),
            ("5* Conjunction", 20_000),
            ("Fungal Beacon", 10_000),
        ],
    },
    "Celestial Emperor": {
        "hp": 2_500_000_000,
        "ash": 7_200_000,
        "drops": [
            ("T4 Keys", 2),
            ("T5 Keys", 12),
            ("5* Conjunction", 5_000),
            ("Cosmic Superwarp Conjunction", 20_000),
            ("Soulsucked Singularity", 10_000),
        ],
    },
}

PET_DROPS = {
    3: ("Fire Hydra Pet", 45_000),
    4: ("Silver Serpent Pet", 75_000),
}

# ----------------------------------------------------------------------
# 2. HELPERS
# ----------------------------------------------------------------------
def format_duration(seconds: float) -> str:
    """Render a duration in a human-readable unit."""
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    if seconds < 3600:
        return f"{seconds / 60:.1f} min"
    if seconds < 86_400:
        return f"{seconds / 3600:.2f} h"
    if seconds < 86_400 * 365:
        return f"{seconds / 86_400:.2f} d"
    return f"{seconds / (86_400 * 365):.2f} y"


def calc_damage(
    weapon_damage, bedrock_choice, t3_pct, tier, t5_pct, autumn
):
    """
    Final damage:
        weapon * (1 + talisman_pct + t3_pct)          [percentage talismans]
        (weapon + 250) * (1 + t3_pct)                 [Bedrock Talisman I]
        ... then * (1 + t5_pct) on T5 mobs
        ... then * 1.5 during Autumn
    """
    b_type, b_value = BEDROCK_TALISMANS[bedrock_choice]
    t3_bonus = t3_pct / 100

    if b_type == "flat":
        dmg = (weapon_damage + b_value) * (1 + t3_bonus)
    else:
        dmg = weapon_damage * (1 + b_value + t3_bonus)

    if tier == 5:
        dmg *= 1 + (t5_pct / 100)

    if autumn:
        dmg *= AUTUMN_MULTIPLIER

    return dmg


def calc_pet_effects(base_hp, pet_type, pet_level):
    if pet_level <= 0 or pet_type == "None":
        return base_hp, 1.0

    bonus_fraction = pet_level / 400  # (level/4) percent

    if pet_type == "Serpent":
        effective_hp = base_hp * (1 - bonus_fraction)
        return effective_hp, 1.0
    if pet_type == "Bone Dragon":
        return base_hp, 1 + bonus_fraction
    return base_hp, 1.0


def analyze_mob(
    mob_data, tier, weapon_damage, bedrock_choice,
    t3_pct, t5_pct, autumn, attack_speed, pet_type, pet_level
):
    damage = calc_damage(
        weapon_damage, bedrock_choice, t3_pct, tier, t5_pct, autumn
    )

    base_hp = mob_data["hp"]
    effective_hp, kills_mult = calc_pet_effects(base_hp, pet_type, pet_level)

    hits = math.ceil(effective_hp / damage)
    time_per_fight = hits / attack_speed

    # Effective time per kill accounts for Bone Dragon's double-kill.
    effective_time_per_kill = (
        time_per_fight / kills_mult if kills_mult > 0 else 0
    )
    kills_per_hour = (
        3600 / effective_time_per_kill if effective_time_per_kill > 0 else 0
    )

    rows = []

    if mob_data.get("ash", 0) > 0:
        ash_per_kill = mob_data["ash"]
        rows.append(
            {
                "Drop": "Ash",
                "Rate": f"{ash_per_kill:,} / kill",
                "Time per Drop": format_duration(effective_time_per_kill),
                "Drops in 100h": kills_per_hour * 100 * ash_per_kill,
            }
        )

    for drop_name, one_in_n in mob_data["drops"]:
        time_per_drop = effective_time_per_kill * one_in_n
        drops_100h = kills_per_hour * 100 / one_in_n
        rows.append(
            {
                "Drop": drop_name,
                "Rate": f"1 / {one_in_n:,}",
                "Time per Drop": format_duration(time_per_drop),
                "Drops in 100h": drops_100h,
            }
        )

    if tier in PET_DROPS:
        pet_drop_name, pet_odds = PET_DROPS[tier]
        rows.append(
            {
                "Drop": pet_drop_name,
                "Rate": f"1 / {pet_odds:,}",
                "Time per Drop": format_duration(
                    effective_time_per_kill * pet_odds
                ),
                "Drops in 100h": kills_per_hour * 100 / pet_odds,
            }
        )

    return hits, kills_per_hour, damage, effective_hp, rows


def render_mob(
    mob_name, mob_data, tier, weapon_damage, bedrock_choice,
    t3_pct, t5_pct, autumn, attack_speed, pet_type, pet_level
):
    hits, kph, damage, eff_hp, rows = analyze_mob(
        mob_data, tier, weapon_damage, bedrock_choice,
        t3_pct, t5_pct, autumn, attack_speed, pet_type, pet_level
    )

    st.markdown(f"#### {mob_name}")

    base_hp = mob_data["hp"]
    show_effective = (
        pet_type == "Serpent" and pet_level > 0 and eff_hp != base_hp
    )

    if show_effective:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("HP", f"{base_hp:,}")
        c2.metric("Effective HP", f"{eff_hp:,.0f}")
        c3.metric("Damage / Hit", f"{damage:,.2f}")
        c4.metric("Hits to Kill", f"{hits:,}")
        c5.metric("Kills / Hour", f"{kph:,.2f}")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("HP", f"{base_hp:,}")
        c2.metric("Damage / Hit", f"{damage:,.2f}")
        c3.metric("Hits to Kill", f"{hits:,}")
        c4.metric("Kills / Hour", f"{kph:,.2f}")

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Drop": st.column_config.TextColumn("Drop", width="medium"),
            "Rate": st.column_config.TextColumn("Rate", width="small"),
            "Time per Drop": st.column_config.TextColumn(
                "Time per Drop", width="small"
            ),
            "Drops in 100h": st.column_config.NumberColumn(
                "Drops in 100h", format="%,.2f"
            ),
        },
    )


# ----------------------------------------------------------------------
# 3. USER INPUTS
# ----------------------------------------------------------------------
st.subheader("Your Setup")

weapon_type = st.radio(
    "Weapon Type",
    ["Pickaxe", "Bludgeon"],
    horizontal=True,
)

weapon_dict = PICKAXES if weapon_type == "Pickaxe" else BLUDGEONS
weapon_name = st.selectbox("Weapon", list(weapon_dict.keys()))
weapon_damage = weapon_dict[weapon_name]

col1, col2 = st.columns(2)
with col1:
    attack_speed = st.number_input(
        "Attack Speed (hits / second)",
        min_value=0.1,
        max_value=100.0,
        value=5.0,
        step=0.1,
        help=(
            "How many times per second your weapon hits. The default (5) "
            "may not match your setup — run an in-game test (e.g. time how "
            "long it takes to kill a low-HP mob) to find your true rate "
            "for accurate results."
        ),
    )
with col2:
    autumn = st.toggle(
        "Autumn Event (1.5x Damage)",
        value=False,
        help="Toggles the monthly Autumn event damage bonus.",
    )

col3, col4 = st.columns(2)
with col3:
    bedrock_choice = st.selectbox(
        "Bedrock Talismans",
        list(BEDROCK_TALISMANS.keys()),
        help=(
            "Bedrock Talisman I adds a flat +250 damage to the weapon. "
            "Talismans II, III and Ash add their percentage bonus "
            "additively with the T3 Damage Upgrader."
        ),
    )
with col4:
    t3_upgrader_options = [f"{p}%" for p in range(0, 71, 10)]
    t3_choice = st.selectbox(
        "T3 Damage Upgrader",
        t3_upgrader_options,
        index=0,
        help="Applies to all mob tiers (T3, T4 and T5).",
    )
    t3_pct = int(t3_choice.rstrip("%"))

t5_options = [f"{p}%" for p in range(0, 36, 5)]
t5_choice = st.selectbox(
    "T5 Damage Upgrader",
    t5_options,
    index=0,
    help="Applies to T5 mobs only, on top of the T3 upgrader.",
)
t5_pct = int(t5_choice.rstrip("%"))

# --- Pet selection ---
st.markdown("##### Pet")
pet_type = st.radio(
    "Pet",
    ["None", "Serpent", "Bone Dragon"],
    horizontal=True,
    label_visibility="collapsed",
    help=(
        "Serpent reduces a mob's effective HP by (level / 4)%. "
        "Bone Dragon grants a (level / 4)% chance to double-kill."
    ),
)

if pet_type == "None":
    pet_level = 0
else:
    pet_level = st.number_input(
        f"{pet_type} Level",
        min_value=0,
        max_value=100,
        value=0,
        step=1,
        help=(
            "Level 50 = 12.5% effect. Level 100 = 25% effect."
        ),
    )

# --- Summary caption ---
b_type, b_value = BEDROCK_TALISMANS[bedrock_choice]
if b_type == "flat":
    bedrock_str = f"+{b_value:,} flat"
else:
    bedrock_str = f"+{b_value * 100:.0f}%"

pet_str = "None"
if pet_type != "None" and pet_level > 0:
    pet_str = f"{pet_type} Lv{pet_level} ({pet_level / 4:.2f}%)"

st.caption(
    f"**Weapon:** {weapon_name} ({weapon_damage:,} dmg) · "
    f"**Bedrock:** {bedrock_choice} ({bedrock_str}) · "
    f"**T3 Upgrader:** +{t3_pct}% · "
    f"**T5 Upgrader:** +{t5_pct}% · "
    f"**Attack Speed:** {attack_speed} hits/s · "
    f"**Pet:** {pet_str}"
    + (" · **Autumn active (1.5x)**" if autumn else "")
)

# ----------------------------------------------------------------------
# 4. RESULTS
# ----------------------------------------------------------------------
st.divider()

st.header("T3 Mobs")
for mob_name, mob_data in T3_MOBS.items():
    render_mob(
        mob_name, mob_data, 3, weapon_damage, bedrock_choice,
        t3_pct, t5_pct, autumn, attack_speed, pet_type, pet_level
    )
    st.write("")

st.divider()

st.header("T4 Mobs")
for mob_name, mob_data in T4_MOBS.items():
    render_mob(
        mob_name, mob_data, 4, weapon_damage, bedrock_choice,
        t3_pct, t5_pct, autumn, attack_speed, pet_type, pet_level
    )
    st.write("")

st.divider()

st.header("T5 Mobs")
st.caption(
    "T5 mobs are affected by the T5 Damage Upgrader on top of the "
    "T3 Damage Upgrader and Bedrock Talisman."
)
for mob_name, mob_data in T5_MOBS.items():
    render_mob(
        mob_name, mob_data, 5, weapon_damage, bedrock_choice,
        t3_pct, t5_pct, autumn, attack_speed, pet_type, pet_level
    )
    st.write("")