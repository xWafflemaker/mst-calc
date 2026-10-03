import math
import pandas as pd
import streamlit as st

st.title("Pet XP Calculator")
st.caption(
    "Calculate XP, spirit requirements, and coins cost to level pets "
    "to a target level or to level 100."
)

# ----------------------------------------------------------------------
# 1. CONSTANTS & HELPERS
# ----------------------------------------------------------------------
M = 10**6
B = 10**9
T = 10**12
QD = 10**15

PETS = [
    "Slime", "Bee", "Parrot", "Ocelot", "Cyclops", "Caspian Tiger",
    "Fire Hydra", "Piglin", "Bone Dragon", "Silver Serpent",
    "Goat", "Sea Dragon", "Goblin Shark", "Dune Ram", "Raven",
    "Solar Scorpion",
]

BASE_XP_PER_SPIRIT = 1500
BATCH_SIZE = 64


def xp_to_level(from_level: int, to_level: int) -> int:
    if to_level <= from_level:
        return 0

    def S(n: int) -> int:
        """Sum of squares :O"""
        return n * (n + 1) * (2 * n + 1) // 6

    return 100 * (S(to_level - 1) - S(from_level - 1))


def xp_per_spirit(wisdom: int) -> float:
    return BASE_XP_PER_SPIRIT * (1 + wisdom / 100)


def wisdom_level_cost(level: int) -> int:
    if level <= 0:
        return 0
    if level <= 10:
        return level * 10 * M
    if level <= 20:
        return (level - 10) * 1 * B
    if level <= 30:
        return (level - 20) * 1 * T
    if level <= 40:
        return (level - 30) * 100 * T
    return (level - 40) * 1 * QD


def total_wisdom_cost(level: int) -> int:
    return sum(wisdom_level_cost(i) for i in range(1, level + 1))


def format_coins(v: float) -> str:
    if v >= QD:
        return f"{v / QD:,.2f} Qd"
    if v >= T:
        return f"{v / T:,.2f} t"
    if v >= B:
        return f"{v / B:,.2f} b"
    if v >= M:
        return f"{v / M:,.2f} m"
    return f"{v:,.0f}"


# ----------------------------------------------------------------------
# 2. INPUTS
# ----------------------------------------------------------------------
st.subheader("Your Setup")

col1, col2 = st.columns(2)
with col1:
    target_level = st.number_input(
        "Target Pet Level",
        min_value=1, max_value=100, value=50, step=1,
        help="The level you're aiming for.",
    )
with col2:
    wisdom = st.number_input(
        "Spirit Wisdom Level",
        min_value=0, max_value=50, value=0, step=1,
        help="0 = no upgrade. Each level adds 1% XP per spirit (max 50%).",
    )

spirit_cost_T = st.number_input(
    "Spirit Cost per 64 (in trillions)",
    min_value=0.0, value=800.0, step=1.0,
    help="Cost to buy a batch of 64 spirits, in trillions (T).",
)

spirit_cost_per_64 = spirit_cost_T * T
spirit_cost_per_unit = spirit_cost_per_64 / BATCH_SIZE
current_xps = xp_per_spirit(wisdom)

st.markdown("##### Current Pet Levels")
st.caption("Set each pet's current level. A fresh pet starts at level 1.")

levels_df = pd.DataFrame(
    {
        "Pet": PETS,
        "Current Level": [0] * len(PETS),
    }
)

edited = st.data_editor(
    levels_df,
    use_container_width=True,
    hide_index=True,
    disabled=["Pet"],
    column_config={
        "Pet": st.column_config.TextColumn("Pet", width="medium"),
        "Current Level": st.column_config.NumberColumn(
            "Current Level",
            min_value=0, max_value=100, step=1, default=0,
        ),
    },
    key="pet_levels_editor",
)

st.caption(
    f"**XP per spirit at Wisdom {wisdom}:** {current_xps:,.1f} XP · "
    f"**Cost per spirit:** {format_coins(spirit_cost_per_unit)} · "
    f"**Batch of 64:** {format_coins(spirit_cost_per_64)}"
)

# ----------------------------------------------------------------------
# 3. MAIN TABLE — PER-PET COSTS
# ----------------------------------------------------------------------
st.divider()
st.subheader(f"Cost to Reach Level {target_level} & Level 100")

rows = []
sum_spirits_tgt = 0
sum_spirits_100 = 0
sum_cost_tgt = 0
sum_cost_100 = 0

for pet, current in zip(edited["Pet"], edited["Current Level"]):
    # Pets start at level 1. Input 0 = treat as level 1 (fresh pet).
    cur = max(int(current), 1)

    xp_tgt = xp_to_level(cur, target_level)
    s_tgt = math.ceil(xp_tgt / current_xps) if current_xps > 0 else 0
    b_tgt = math.ceil(s_tgt / BATCH_SIZE)
    c_tgt = b_tgt * spirit_cost_per_64

    xp_100 = xp_to_level(cur, 100)
    s_100 = math.ceil(xp_100 / current_xps) if current_xps > 0 else 0
    b_100 = math.ceil(s_100 / BATCH_SIZE)
    c_100 = b_100 * spirit_cost_per_64

    sum_spirits_tgt += s_tgt
    sum_spirits_100 += s_100
    sum_cost_tgt += c_tgt
    sum_cost_100 += c_100

    rows.append(
        {
            "Pet": pet,
            "Lvl": cur,
            "XP to T": xp_tgt,
            "Spirits to T": s_tgt,
            "Cost to T": format_coins(c_tgt),
            "XP to 100": xp_100,
            "Spirits to 100": s_100,
            "Cost to 100": format_coins(c_100),
        }
    )

main_df = pd.DataFrame(rows)

st.dataframe(
    main_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Pet": st.column_config.TextColumn("Pet", width="medium"),
        "Lvl": st.column_config.NumberColumn("Lvl", width="small"),
        "XP to T": st.column_config.NumberColumn(
            f"XP to {target_level}", format="%,d"
        ),
        "Spirits to T": st.column_config.NumberColumn(
            f"Spirits to {target_level}", format="%,d"
        ),
        "Cost to T": st.column_config.TextColumn(
            f"Cost to {target_level}", width="small"
        ),
        "XP to 100": st.column_config.NumberColumn(
            "XP to 100", format="%,d"
        ),
        "Spirits to 100": st.column_config.NumberColumn(
            "Spirits to 100", format="%,d"
        ),
        "Cost to 100": st.column_config.TextColumn(
            "Cost to 100", width="small"
        ),
    },
)

st.caption(
    f"**Totals across all pets · "
    f"to Level {target_level}:** {sum_spirits_tgt:,} spirits "
    f"({format_coins(sum_cost_tgt)}) · "
    f"**to Level 100:** {sum_spirits_100:,} spirits "
    f"({format_coins(sum_cost_100)})"
)

# ----------------------------------------------------------------------
# 4. SPIRIT WISDOM PAY-OFF TABLE
# ----------------------------------------------------------------------
st.divider()
st.subheader("Spirit Wisdom Pay-off")
st.caption(
    "For each Wisdom level, this shows how many spirits you must use for "
    "the extra XP from the upgrade to fully pay back the cumulative coins "
    "spent on Wisdom."
)

coins_per_xp = spirit_cost_per_unit / BASE_XP_PER_SPIRIT

payoff_rows = []
for L in range(1, 51):
    tot_cost = total_wisdom_cost(L)
    extra_xp = BASE_XP_PER_SPIRIT * L / 100
    value_per_spirit = extra_xp * coins_per_xp
    spirits_to_payoff = (
        math.ceil(tot_cost / value_per_spirit) if value_per_spirit > 0 else 0
    )

    payoff_rows.append(
        {
            "Wisdom": L,
            "Total Cost (fmt)": format_coins(tot_cost),
            "Extra XP / Spirit": extra_xp,
            "Value / Spirit": format_coins(value_per_spirit),
            "Spirits to Break Even": spirits_to_payoff,
        }
    )

payoff_df = pd.DataFrame(payoff_rows)

st.dataframe(
    payoff_df[
        [
            "Wisdom",
            "Total Cost (fmt)",
            "Extra XP / Spirit",
            "Value / Spirit",
            "Spirits to Break Even",
        ]
    ].rename(
        columns={
            "Total Cost (fmt)": "Total Upgrade Cost",
            "Value / Spirit": "Value of Added XP / Spirit",
        }
    ),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Wisdom": st.column_config.NumberColumn(
            "Wisdom Lvl", width="small"
        ),
        "Total Upgrade Cost": st.column_config.TextColumn(
            "Total Upgrade Cost", width="small"
        ),
        "Extra XP / Spirit": st.column_config.NumberColumn(
            "Extra XP / Spirit", format="%,.1f"
        ),
        "Value of Added XP / Spirit": st.column_config.TextColumn(
            "Value of Added XP / Spirit", width="medium"
        ),
        "Spirits to Break Even": st.column_config.NumberColumn(
            "Spirits to Break Even", format="%,d"
        ),
    },
)

if wisdom > 0:
    row = payoff_df[payoff_df["Wisdom"] == wisdom].iloc[0]
    st.caption(
        f"**At your Wisdom level {wisdom}:** total upgrade cost "
        f"**{row['Total Cost (fmt)']}** · extra XP per spirit "
        f"**{row['Extra XP / Spirit']:,.0f}** · break-even after using "
        f"**{row['Spirits to Break Even']:,} spirits**."
    )
else:
    st.caption(
        "Set a Spirit Wisdom level above 0 to see your own break-even"
    )