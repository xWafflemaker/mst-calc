import streamlit as st
import pandas as pd

# ----------------------------------------------------------------------
# 1. PAGE HEADER
# ----------------------------------------------------------------------
st.title("Ore Profit Calculator")
st.caption(
    "Compare Revenue and Profit per hour and per day for every ore "
    "and Fortune Potion tier."
)

# ----------------------------------------------------------------------
# 2. STATIC GAME DATA
# ----------------------------------------------------------------------
TRILLION = 1_000_000_000_000

ORE_DATA = {
    "Basalt": 75_000,
    "Brecca": 40_000,
    "Regolith": 180_000,
    "Amber Rock": 88_000,
    "Amber Crystal": 46_000,
    "Crimson Plasma": 68_000,
    "Cosmic Fiber": 95_000,
}

ORE_BREAK_SPEED = {
    "Basalt":         [1.50, 1.30, 1.20, 1.05, 1.00, 0.90, 0.85],
    "Brecca":         [0.75, 0.70, 0.65, 0.60, 0.55, 0.55, 0.55],
    "Regolith":       [3.30, 2.80, 2.45, 2.20, 2.00, 1.80, 1.70],
    "Amber Rock":     [1.50, 1.30, 1.20, 1.05, 1.00, 0.90, 0.85],
    "Amber Crystal":  [0.75, 0.70, 0.65, 0.60, 0.55, 0.55, 0.55],
    "Crimson Plasma": [0.75, 0.70, 0.65, 0.60, 0.55, 0.55, 0.55],
    "Cosmic Fiber":   [1.50, 1.30, 1.20, 1.05, 1.00, 0.90, 0.85],
}

ORE_HASTE_TYPE = {
    "Basalt": "Moon",
    "Brecca": "Moon",
    "Regolith": "Mars",
    "Amber Rock": "Mars",
    "Amber Crystal": "Mars",
    "Crimson Plasma": "Sun",
    "Cosmic Fiber": "Sun",
}

ORE_DROPS = {
    "Basalt": [
        ("Lunar Fragment", 500),
        ("Chisilite Shard", 1_000),
        ("Basalt Shard", 1_000),
    ],
    "Brecca": [
        ("Lunar Fragment", 500),
        ("Chisilite Shard", 1_000),
        ("Brecca Powder", 2_000),
    ],
    "Regolith": [
        ("Martian Dust", 500),
        ("Rhodnite", 2_500),
    ],
    "Amber Rock": [
        ("Amber Fragment", 500),
        ("Ametrine", 1_000),
        ("Rhodnite", 2_500),
    ],
    "Amber Crystal": [
        ("Amber Fragment", 500),
        ("Ametrine", 1_000),
        ("Rhodnite", 2_500),
    ],
    "Crimson Plasma": [
        ("Sun Fragment", 500),
        ("Plasma Shard", 1_000),
    ],
    "Cosmic Fiber": [
        ("Sun Fragment", 500),
        ("Fiber", 1_000),
    ],
}

DEFAULT_DROP_PRICES_T = {
    "Lunar Fragment": 20.0,
    "Chisilite Shard": 1_000.0,
    "Basalt Shard": 1_000.0,
    "Brecca Powder": 200.0,
    "Martian Dust": 2_000.0,
    "Rhodnite": 1_000.0,
    "Amber Fragment": 250.0,
    "Ametrine": 320.0,
    "Sun Fragment": 400.0,
    "Fiber": 500.0,
    "Plasma Shard": 640.0,
}

POTION_DATA = [
    ("Tier 1", 2.0, 1920, 1 / 27),
    ("Tier 2", 3.0, 2880, 1 / 9),
    ("Tier 3", 4.5, 3840, 1 / 3),
    ("Tier 4", 6.0, 4800, 1.0),
]

ALL_DROP_ITEMS = [
    "Lunar Fragment", "Chisilite Shard", "Basalt Shard", "Brecca Powder",
    "Martian Dust", "Rhodnite",
    "Amber Fragment", "Ametrine",
    "Sun Fragment", "Fiber", "Plasma Shard",
]

TARGET_STACK_TOTAL = 640  # 10 stacks

# ----------------------------------------------------------------------
# 3. THEME DETECTION
# ----------------------------------------------------------------------
def get_theme_base() -> str:
    try:
        return st.context.theme.type
    except Exception:
        pass
    base = st.get_option("theme.base")
    return base if base in ("light", "dark") else "light"


THEME = get_theme_base()

# ----------------------------------------------------------------------
# 4. HELPERS
# ----------------------------------------------------------------------
def format_duration_hours_max(seconds: float) -> str:
    if seconds <= 0:
        return "—"
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    if seconds < 3600:
        return f"{seconds / 60:.1f} min"
    return f"{seconds / 3600:.2f} h"


def highlight_best_row(df: pd.DataFrame, best_potion: str):
    if THEME == "dark":
        bg, fg = "#1b5e20", "white"
    else:
        bg, fg = "#d4edda", "#155724"

    style = f"background-color: {bg}; color: {fg}; font-weight: bold"

    def style_row(row):
        if row.get("Potion") == best_potion:
            return [style] * len(row)
        return [""] * len(row)

    return df.style.apply(style_row, axis=1)


# ----------------------------------------------------------------------
# 5. CALCULATION FUNCTIONS
# ----------------------------------------------------------------------
def calculate_sell_price(base_price, refinery_level, ram_level, has_cash_register):
    refinery_mult = 1 + (refinery_level * 0.025 * (1 + ram_level * 0.02))
    cash_mult = 1.03 if has_cash_register else 1.0
    return base_price * refinery_mult * cash_mult


def calculate_ore_per_hour(fortune, fortune_multiplier, break_time):
    return (3600 / break_time) * (fortune / 100) * fortune_multiplier


def calc_fragment_value(break_time, ore_name, drop_prices, raven_mult=1.0):
    blocks_per_hour = 3600 / break_time
    base_val = 0.0
    raven_bonus = 0.0
    for drop_name, odds in ORE_DROPS.get(ore_name, []):
        base_drops_h = blocks_per_hour / odds
        price_per_64 = drop_prices.get(drop_name, 0.0) * TRILLION
        val_h = base_drops_h * price_per_64 / 64
        base_val += val_h
        raven_bonus += val_h * (raven_mult - 1.0)
    return base_val, raven_bonus


def build_fragment_detail_rows(
    ore_name, break_time, drop_prices, raven_on, raven_level
):
    blocks_per_hour = 3600 / break_time
    raven_mult = (1 + raven_level / 100) if raven_on else 1.0
    rows = []
    for drop_name, odds in ORE_DROPS.get(ore_name, []):
        base_rate = blocks_per_hour / odds
        price_per_64 = drop_prices.get(drop_name, 0.0) * TRILLION
        value_per_drop_T = (price_per_64 / 64) / TRILLION

        hours_base = TARGET_STACK_TOTAL / base_rate if base_rate > 0 else 0

        rows.append({
            "Drop": drop_name,
            "Value / Drop": value_per_drop_T,
            "Drops / Hour": base_rate,
            "Drops / Day": base_rate * 24,
            "Time to 640": format_duration_hours_max(hours_base * 3600),
        })

        if raven_on:
            bonus_rate = base_rate * (raven_mult - 1.0)
            total_rate = base_rate + bonus_rate
            hours_raven = (
                TARGET_STACK_TOTAL / total_rate if total_rate > 0 else 0
            )
            rows.append({
                "Drop": f"🐦 {drop_name}",
                "Value / Drop": None,
                "Drops / Hour": bonus_rate,
                "Drops / Day": bonus_rate * 24,
                "Time to 640": format_duration_hours_max(hours_raven * 3600),
            })
    return rows


# ----------------------------------------------------------------------
# 6. USER INPUTS
# ----------------------------------------------------------------------
st.subheader("Your Setup")

col1, col2, col3 = st.columns(3)
with col1:
    ram = st.number_input(
        "Ram Level", min_value=0, max_value=100, value=50, step=1,
        help="Ranges from 0 to 100. Applies to all ores.",
    )
with col2:
    fortune = st.number_input(
        "Player's Fortune", min_value=0, value=100, step=1,
        help="Base ore gain multiplier is Fortune / 100. "
             "100 = 1x. Multiplied further by potions.",
    )
with col3:
    cash_register = st.toggle(
        "Cash Register", value=False,
        help="Toggle if you own a Cash Register (adds 3%). Applies to all ores.",
    )

st.markdown("##### Haste Levels")
st.caption(
    "Manual Haste input caps at 5. Haste 6 is only reachable by using "
    "Andromeda Squash. Ranges from 0 to 5."
)
h1, h2, h3 = st.columns(3)
with h1:
    moon_haste = st.number_input(
        "Moon Haste", min_value=0, max_value=5, value=0, step=1,
        help="Affects Basalt and Brecca.",
    )
with h2:
    mars_haste = st.number_input(
        "Mars Haste", min_value=0, max_value=5, value=0, step=1,
        help="Affects Regolith, Amber Rock and Amber Crystal.",
    )
with h3:
    sun_haste = st.number_input(
        "Sun Haste", min_value=0, max_value=5, value=0, step=1,
        help="Affects Crimson Plasma and Cosmic Fiber.",
    )

st.markdown("##### Prices")
st.caption("Enter price of a stack in **trillions (T)**.")

t4_price_T = st.number_input(
    "T4 Potion Price (T)", min_value=0.0, value=150.0, step=1.0,
    help="Price of a stack of Tier 4 Potion, in trillions.",
)

st.markdown("##### 🍑 Andromeda Squash")
squash_on = st.toggle(
    "Use Andromeda Squash",
    value=False,
    help="When on, the calculator adds a Squash row (+1 Haste for 1h) "
         "and its cost.",
)
if squash_on:
    squash_price_T = st.number_input(
        "Andromeda Squash Price (T)", min_value=0.0, value=100.0,
        step=1.0,
        help="Price of a single Andromeda Squash, in trillions.",
    )
else:
    squash_price_T = 0.0

st.markdown("##### 🐦 Raven Pet")
raven_on = st.toggle(
    "Own Raven",
    value=False,
    help="Raven grants a % chance (equal to its level) to double any "
         "ore-drop.",
)
if raven_on:
    raven_level = st.number_input(
        "Raven Level", min_value=0, max_value=100, value=0, step=1,
        help="Grants a duplicate chance on fragment drops.",
    )
else:
    raven_level = 0

st.markdown("##### Fragment Details")
fragment_details_on = st.toggle(
    "Show Detailed Ore Drop Tables",
    value=False,
    help="Adds a per-ore table breaking down every fragment drop, "
         "including per-hour/per-day rates, time to gather 640, and "
         "(if Raven is on) the bonus from Raven duplication.",
)

st.markdown("##### Drop Prices (per 64-stack, in T)")
st.caption(
    "Set the value of a full 64-unit stack for each drop item, in "
    "trillions."
)

drop_price_df = pd.DataFrame({
    "Item": ALL_DROP_ITEMS,
    "Price / 64 (T)": [DEFAULT_DROP_PRICES_T.get(i, 0.0) for i in ALL_DROP_ITEMS],
})
edited_prices = st.data_editor(
    drop_price_df,
    use_container_width=True,
    hide_index=True,
    disabled=["Item"],
    column_config={
        "Item": st.column_config.TextColumn("Item", width="medium"),
        "Price / 64 (T)": st.column_config.NumberColumn(
            "Price / 64 (T)", min_value=0.0, step=1.0, format="%.2f"
        ),
    },
    key="drop_prices_editor",
)

st.markdown("##### Refinery Level per Ore")
st.caption("Refinery is an ore-specific upgrade. Set each ore's level (0–10).")

refinery_input_df = pd.DataFrame({
    "Ore": list(ORE_DATA.keys()),
    "Refinery Level": [0] * len(ORE_DATA),
})
edited_refinery = st.data_editor(
    refinery_input_df,
    use_container_width=True,
    hide_index=True,
    disabled=["Ore"],
    column_config={
        "Ore": st.column_config.TextColumn("Ore", width="medium"),
        "Refinery Level": st.column_config.NumberColumn(
            "Refinery Level", min_value=0, max_value=10, step=1, default=0,
        ),
    },
    key="refinery_editor",
)

refinery_by_ore = dict(zip(edited_refinery["Ore"], edited_refinery["Refinery Level"]))
haste_by_type = {"Moon": moon_haste, "Mars": mars_haste, "Sun": sun_haste}
drop_prices = dict(zip(edited_prices["Item"], edited_prices["Price / 64 (T)"]))


# ----------------------------------------------------------------------
# 7. RESULTS
# ----------------------------------------------------------------------
st.divider()
st.subheader("Profit Comparison")
st.caption("All rate values are shown in trillions (T).")

t4_cost = t4_price_T * TRILLION
squash_cost_h = squash_price_T * TRILLION if squash_on else 0.0
raven_mult = (1 + raven_level / 100) if raven_on else 1.0

all_rows = []
best_tier_summary = []

for ore_name, base_price in ORE_DATA.items():
    refinery = int(refinery_by_ore.get(ore_name, 0))
    haste_type = ORE_HASTE_TYPE[ore_name]
    haste_level = haste_by_type[haste_type]
    break_time = ORE_BREAK_SPEED[ore_name][haste_level]

    sell_price = calculate_sell_price(base_price, refinery, ram, cash_register)

    ore_rows = []
    tier_results = []

    for potion_name, fortune_mult, duration, cost_fraction in POTION_DATA:
        ore_per_hour = calculate_ore_per_hour(fortune, fortune_mult, break_time)
        rev_h = ore_per_hour * sell_price
        rev_d = rev_h * 24

        duration_hours = duration / 3600
        cost_h = (t4_cost * cost_fraction) / duration_hours
        prof_h = rev_h - cost_h
        prof_d = prof_h * 24

        tier_results.append({
            "name": potion_name,
            "mult": fortune_mult,
            "rev_h": rev_h,
            "prof_h": prof_h,
            "cost_h": cost_h,
        })

        ore_rows.append({
            "Ore": ore_name,
            "Potion": potion_name,
            "Fortune Multiplier": f"{fortune_mult}x",
            "Revenue / Hour": rev_h / TRILLION,
            "Profit / Hour": prof_h / TRILLION,
            "Revenue / Day": rev_d / TRILLION,
            "Profit / Day": prof_d / TRILLION,
        })

    best = max(tier_results, key=lambda r: r["prof_h"])

    sq_prof_h = None
    boosted_break = None
    if squash_on:
        boosted_haste = min(haste_level + 1, 6)
        boosted_break = ORE_BREAK_SPEED[ore_name][boosted_haste]

        sq_ore_h = calculate_ore_per_hour(fortune, best["mult"], boosted_break)
        sq_rev_h = sq_ore_h * sell_price
        sq_rev_d = sq_rev_h * 24

        sq_prof_h = sq_rev_h - best["cost_h"] - squash_cost_h
        sq_prof_d = sq_prof_h * 24

        ore_rows.append({
            "Ore": ore_name,
            "Potion": f"🍑 Squash + {best['name']}",
            "Fortune Multiplier": f"{best['mult']}x",
            "Revenue / Hour": sq_rev_h / TRILLION,
            "Profit / Hour": sq_prof_h / TRILLION,
            "Revenue / Day": sq_rev_d / TRILLION,
            "Profit / Day": sq_prof_d / TRILLION,
        })

    frag_base, frag_raven = calc_fragment_value(
        break_time, ore_name, drop_prices, raven_mult
    )

    ore_rows.append({
        "Ore": ore_name,
        "Potion": "📦 Fragments",
        "Fortune Multiplier": "—",
        "Revenue / Hour": frag_base / TRILLION,
        "Profit / Hour": frag_base / TRILLION,
        "Revenue / Day": frag_base * 24 / TRILLION,
        "Profit / Day": frag_base * 24 / TRILLION,
    })

    if squash_on:
        frag_base_sq, frag_raven_sq = calc_fragment_value(
            boosted_break, ore_name, drop_prices, raven_mult
        )
        ore_rows.append({
            "Ore": ore_name,
            "Potion": "📦 Fragments (Squash)",
            "Fortune Multiplier": "—",
            "Revenue / Hour": frag_base_sq / TRILLION,
            "Profit / Hour": frag_base_sq / TRILLION,
            "Revenue / Day": frag_base_sq * 24 / TRILLION,
            "Profit / Day": frag_base_sq * 24 / TRILLION,
        })

    if raven_on:
        ore_rows.append({
            "Ore": ore_name,
            "Potion": "🐦 Bonus Fragments",
            "Fortune Multiplier": "—",
            "Revenue / Hour": frag_raven / TRILLION,
            "Profit / Hour": frag_raven / TRILLION,
            "Revenue / Day": frag_raven * 24 / TRILLION,
            "Profit / Day": frag_raven * 24 / TRILLION,
        })
        if squash_on:
            ore_rows.append({
                "Ore": ore_name,
                "Potion": "🐦 Bonus (Squash)",
                "Fortune Multiplier": "—",
                "Revenue / Hour": frag_raven_sq / TRILLION,
                "Profit / Hour": frag_raven_sq / TRILLION,
                "Revenue / Day": frag_raven_sq * 24 / TRILLION,
                "Profit / Day": frag_raven_sq * 24 / TRILLION,
            })

    st.markdown(
        f"### {ore_name} "
        f"<span style='font-size:0.6em;color:gray;'>"
        f"(Refinery {refinery} · {haste_type} Haste {haste_level} · "
        f"Break {break_time}s · Sell Price $ {sell_price:,.0f})"
        f"</span>",
        unsafe_allow_html=True,
    )

    ore_df = pd.DataFrame(ore_rows)
    all_rows.extend(ore_rows)

    display_df = ore_df.drop(columns=["Ore"]).reset_index(drop=True)
    styled_df = highlight_best_row(display_df, best["name"])

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Potion": st.column_config.TextColumn("Potion", width="medium"),
            "Fortune Multiplier": st.column_config.TextColumn(
                "Fortune", width="small"
            ),
            "Revenue / Hour": st.column_config.NumberColumn(
                "Revenue / Hour", format="$ %.2f T"
            ),
            "Profit / Hour": st.column_config.NumberColumn(
                "Profit / Hour", format="$ %.2f T"
            ),
            "Revenue / Day": st.column_config.NumberColumn(
                "Revenue / Day", format="$ %.2f T"
            ),
            "Profit / Day": st.column_config.NumberColumn(
                "Profit / Day", format="$ %.2f T"
            ),
        },
    )

    if fragment_details_on and ORE_DROPS.get(ore_name):
        st.markdown(
            f"##### {ore_name} Ore Drops "
            f"<span style='font-size:0.65em;color:gray;'>"
            f"({haste_type} Haste {haste_level} · Break {break_time}s)"
            f"</span>",
            unsafe_allow_html=True,
        )
        detail_rows = build_fragment_detail_rows(
            ore_name, break_time, drop_prices, raven_on, raven_level
        )
        detail_df = pd.DataFrame(detail_rows)

        st.dataframe(
            detail_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Drop": st.column_config.TextColumn("Drop", width="medium"),
                "Value / Drop": st.column_config.NumberColumn(
                    "Value / Drop", format="$ %.4f T"
                ),
                "Drops / Hour": st.column_config.NumberColumn(
                    "Drops / Hour", format="%,.2f"
                ),
                "Drops / Day": st.column_config.NumberColumn(
                    "Drops / Day", format="%,.2f"
                ),
                "Time to 640": st.column_config.TextColumn(
                    "Time to 640", width="small"
                ),
            },
        )

    if squash_on:
        delta_h = (sq_prof_h - best["prof_h"]) / TRILLION
        if haste_level >= 6:
            st.caption(
                f"🍑 **{ore_name}**: Haste is already at max (6) — "
                f"Squash provides no mining benefit."
            )
        elif sq_prof_h > best["prof_h"]:
            st.caption(
                f"✅ 🍑 **Squash is worth using for {ore_name}** "
                f"(net **+{delta_h:.2f} T**/hour over {best['name']})."
            )
        else:
            st.caption(
                f"❌ 🍑 **Squash is NOT worth using for {ore_name} alone** "
                f"(net **{delta_h:+.2f} T**/hour over {best['name']})."
            )

        best_tier_summary.append({
            "Ore": ore_name,
            "Best Potion": best["name"],
            "Best Profit / Hour": best["prof_h"] / TRILLION,
            "Squash Profit / Hour": sq_prof_h / TRILLION,
            "Net Squash Gain / Hour": delta_h,
            "Use Squash?": "✅ Yes" if sq_prof_h > best["prof_h"] else "❌ No",
        })


# ----------------------------------------------------------------------
# 8. BEST POTION TABLE
# ----------------------------------------------------------------------
st.divider()
st.subheader("Best Potion Tier per Ore")

full_df = pd.DataFrame(all_rows)
potion_only = full_df[~full_df["Potion"].str.startswith(("📦", "🐦", "🍑"))]

best_rows = (
    potion_only.loc[potion_only.groupby("Ore")["Profit / Hour"].idxmax()]
    .sort_values("Profit / Hour", ascending=False)
    .reset_index(drop=True)
)

best_display = best_rows[["Ore", "Potion", "Profit / Hour"]].copy()

st.dataframe(
    best_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Ore": st.column_config.TextColumn("Ore", width="medium"),
        "Potion": st.column_config.TextColumn("Best Potion", width="small"),
        "Profit / Hour": st.column_config.NumberColumn(
            "Profit / Hour", format="$ %.2f T"
        ),
    },
)


# ----------------------------------------------------------------------
# 9. SQUASH SUMMARY
# ----------------------------------------------------------------------
if squash_on:
    st.divider()
    st.subheader("🍑 Andromeda Squash Summary")
    st.caption(
        "Squash grants +1 Haste to **every** planet for 1 hour. The table "
        "below considers each ore in isolation."
    )

    sq_summary_df = pd.DataFrame(best_tier_summary)

    st.dataframe(
        sq_summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ore": st.column_config.TextColumn("Ore", width="medium"),
            "Best Potion": st.column_config.TextColumn(
                "Best Potion", width="small"
            ),
            "Best Profit / Hour": st.column_config.NumberColumn(
                "Profit / H (no squash)", format="$ %.2f T"
            ),
            "Squash Profit / Hour": st.column_config.NumberColumn(
                "Profit / H (with squash)", format="$ %.2f T"
            ),
            "Net Squash Gain / Hour": st.column_config.NumberColumn(
                "Net Squash Gain / H", format="$ %+.2f T"
            ),
            "Use Squash?": st.column_config.TextColumn(
                "Use Squash?", width="small"
            ),
        },
    )