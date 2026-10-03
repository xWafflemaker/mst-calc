import streamlit as st

st.set_page_config(
    page_title="Tycoon Calculators",
    page_icon="⛏️",
    layout="wide",
)

pages = [
    st.Page(
        "views/profit_calculator.py",
        title="⛏️ Profit Calculator",
        default=True,
    ),
    st.Page(
        "views/pve_calculator.py",
        title="⚔️  PVE Calculator",
    ),
    st.Page(
        "views/pet_xp_calculator.py",
        title="🐾 Pet XP Calculator",
    ),
    st.Page(
        "views/talisman_calculator.py",
        title="💎 Talisman and Fortune Calculator",
    ),
    st.Page(
        "views/sea_crate_calcuator.py",
        title="🦑 Sea Creature Crate Calculator",
    ),
    st.Page(
        "views/lucky_block_calculator.py",
        title="🎁 Lucky Block Calculator",
    ),
]

pg = st.navigation(pages)
pg.run()