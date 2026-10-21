import random
import math
import pandas as pd
import streamlit as st

# FC27 Career Mode simulation module.
# Import and call render_career_mode(ea) from app.py.
# Budgets and transfer values are game estimates, not official club financial data.

CLUB_BUDGETS_EUR = {
    "Real Madrid": 180_000_000,
    "Manchester City": 160_000_000,
    "Paris Saint-Germain": 150_000_000,
    "Liverpool": 120_000_000,
    "Arsenal": 110_000_000,
    "Chelsea": 100_000_000,
    "Manchester United": 100_000_000,
    "Bayern Munich": 100_000_000,
    "FC Barcelona": 90_000_000,
    "Tottenham Hotspur": 80_000_000,
    "Newcastle United": 75_000_000,
    "Inter": 70_000_000,
    "Juventus": 65_000_000,
    "AC Milan": 60_000_000,
    "Atlético Madrid": 60_000_000,
    "Borussia Dortmund": 55_000_000,
    "Napoli": 50_000_000,
}
CLUB_STRENGTHS = {
    "Real Madrid": 86, "Manchester City": 86, "Paris Saint-Germain": 85,
    "Liverpool": 85, "Arsenal": 84, "Bayern Munich": 85,
    "FC Barcelona": 84, "Chelsea": 82, "Manchester United": 82,
    "Inter": 84, "Atlético Madrid": 83, "Juventus": 82,
    "AC Milan": 82, "Borussia Dortmund": 82, "Tottenham Hotspur": 81,
    "Newcastle United": 81, "Napoli": 81,
}
STAT_COLS = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
POSITION_GROUPS = {
    "GK": "GK",
    "CB": "DEF", "LB": "DEF", "RB": "DEF", "LWB": "DEF", "RWB": "DEF",
    "CDM": "MID", "CM": "MID", "CAM": "MID", "LM": "MID", "RM": "MID",
    "LW": "ATT", "RW": "ATT", "ST": "ATT", "CF": "ATT",
}

def _num(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def _estimate_value(row):
    ovr = _num(row.get("OVR"), 60)
    age = _num(row.get("Age"), 27)
    # Simple in-game estimate, not an official market value.
    base = max(150_000, (max(40, ovr - 45) ** 3) * 65)
    age_factor = 1.25 if age <= 21 else 1.12 if age <= 24 else 1.0 if age <= 28 else 0.72 if age <= 31 else 0.42
    return int(base * age_factor / 10_000) * 10_000

def _clean_players(ea):
    df = ea.copy()
    df.columns = [str(c).strip() for c in df.columns]
    required = ["Name", "Team", "OVR"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("選手CSVに必要な列がありません: " + ", ".join(missing))
        st.caption("必要な列: Name, Team, OVR。CSVの列名を確認してください。")
        return pd.DataFrame()
    for col in ["Name", "Team"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["OVR"] = pd.to_numeric(df["OVR"], errors="coerce")
    df = df[(df["Name"] != "") & (df["Team"] != "") & df["OVR"].notna()].copy()
    if "Position" not in df.columns:
        df["Position"] = "CM"
    df["Position"] = df["Position"].fillna("CM").astype(str).str.upper().str.strip()
    if "Age" not in df.columns:
        df["Age"] = 27
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(27)
    for col in STAT_COLS:
        if col not in df.columns:
            df[col] = df["OVR"]
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df["OVR"])
    df["EstimatedValue"] = df.apply(_estimate_value, axis=1)
    return df

def _club_budget(club, squad):
    if club in CLUB_BUDGETS_EUR:
        return CLUB_BUDGETS_EUR[club]
    strength = _num(squad["OVR"].mean(), 70) if not squad.empty else 70
    if strength >= 82:
        return 70_000_000
    if strength >= 77:
        return 35_000_000
    if strength >= 72:
        return 15_000_000
    return 5_000_000

def _squad_strength(squad, tactic, formation):
    if squad.empty:
        return 55.0
    starters = squad.sort_values("OVR", ascending=False).head(11)
    base = _num(starters["OVR"].mean(), 65)
    pos = starters["Position"].map(POSITION_GROUPS).value_counts()
    if tactic == "ポゼッション":
        base += min(2.0, (_num(starters["PAS"].mean(), 65) - 70) * 0.10)
    elif tactic == "カウンター":
        base += min(2.0, (_num(starters["PAC"].mean(), 65) - 70) * 0.10)
    elif tactic == "ハイプレス":
        base += min(1.5, (_num(starters["PHY"].mean(), 65) - 70) * 0.08)
    if formation == "4-3-3":
        base += 0.6 if pos.get("ATT", 0) >= 3 else -0.2
    elif formation == "5-3-2":
        base += 0.5 if pos.get("DEF", 0) >= 4 else -0.3
    return max(45.0, min(95.0, base))

def _new_state(club, players):
    squad = players[players["Team"].str.casefold() == club.casefold()].copy()
    if squad.empty:
        squad = players[players["Team"].str.casefold().str.contains(club.casefold(), na=False)].copy()
    budget = _club_budget(club, squad)
    return {
        "club": club,
        "squad": squad,
        "budget": budget,
        "initial_budget": budget,
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "gf": 0,
        "ga": 0,
        "points": 0,
        "history": [],
        "season": 1,
    }

def _play_match(state, opponent, tactic, formation, opponent_strength, starters, subs, risk):
    squad = state["squad"]
    active = squad[squad["Name"].isin(starters)].copy()
    if active.empty:
        active = squad.sort_values("OVR", ascending=False).head(11).copy()
    user_strength = _squad_strength(active, tactic, formation)
    # Selected substitutes can boost late-game impact; cap it to avoid unrealistic swings.
    sub_rows = squad[squad["Name"].isin(subs)]
    sub_boost = min(2.2, len(sub_rows) * 0.35 + max(0, _num(sub_rows["OVR"].mean(), 0) - 75) * 0.04) if not sub_rows.empty else 0
    user_strength += sub_boost
    tactic_risk = {"守備重視": -0.35, "バランス": 0.0, "攻撃重視": 0.55}[risk]
    # More attacking tactics score more but concede a little more.
    attack_bonus = {"ポゼッション": 0.15, "カウンター": 0.35, "ハイプレス": 0.25}[tactic]
    diff = (user_strength - opponent_strength) / 10
    home_adv = 0.25
    lam_for = max(0.25, min(3.5, 1.25 + diff * 0.42 + home_adv + attack_bonus + tactic_risk))
    lam_against = max(0.2, min(3.4, 1.10 - diff * 0.32 - (0.25 if risk == "守備重視" else 0) + (0.25 if risk == "攻撃重視" else 0)))
    # Poisson-like goal simulation using sums of Bernoulli events.
    goals_for = sum(random.random() < min(0.85, lam_for / 5) for _ in range(5))
    goals_against = sum(random.random() < min(0.85, lam_against / 5) for _ in range(5))
    events = []
    for minute in sorted(random.sample(range(5, 90), k=min(goals_for + goals_against, 8))):
        events.append(f"{minute}' ゴール")
    state["played"] += 1
    state["gf"] += goals_for
    state["ga"] += goals_against
    if goals_for > goals_against:
        state["wins"] += 1
        state["points"] += 3
        result = "勝利"
    elif goals_for == goals_against:
        state["draws"] += 1
        state["points"] += 1
        result = "引き分け"
    else:
        state["losses"] += 1
        result = "敗戦"
    record = {
        "節": state["played"], "対戦相手": opponent,
        "スコア": f"{goals_for} - {goals_against}", "結果": result,
        "戦術": tactic, "フォーメーション": formation,
        "試合運び": risk, "交代選手": ", ".join(subs) if subs else "なし",
    }
    state["history"].append(record)
    return record

def render_career_mode(ea):
    st.header("🏆 監督キャリアモード")
    st.caption("実在クラブを選び、編成・移籍・戦術・交代を決めてシーズンを進めます。予算・移籍金・試合結果はゲーム内推定値です。")
    players = _clean_players(ea)
    if players.empty:
        return

    teams = sorted(t for t in players["Team"].dropna().unique() if t.strip())
    if not teams:
        st.warning("CSVからクラブ名（Team列）を読み取れませんでした。")
        return

    # Prefer recognizable real clubs but also show every real club found in the CSV.
    preferred = [t for t in CLUB_BUDGETS_EUR if t in teams]
    remaining = [t for t in teams if t not in preferred]
    club_options = preferred + remaining
    if "career_state" not in st.session_state:
        st.session_state.career_state = None

    current_club = st.session_state.career_state["club"] if st.session_state.career_state else club_options[0]
    default_index = club_options.index(current_club) if current_club in club_options else 0
    chosen = st.selectbox("監督するクラブ", club_options, index=default_index, key="career_club_choice")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("新しいキャリアを開始 / クラブ変更", type="primary", use_container_width=True):
            st.session_state.career_state = _new_state(chosen, players)
            st.rerun()
    with c2:
        st.caption("クラブを変更すると、現在のセーブデータは新しいキャリアで置き換わります。")

    if st.session_state.career_state is None:
        st.info("クラブを選択し、「新しいキャリアを開始」を押してください。")
        return

    state = st.session_state.career_state
    # Refresh the player pool when the CSV is updated, while retaining saved squad changes.
    if state["club"] != chosen:
        st.warning("選択クラブと進行中のキャリアが異なります。新しいキャリアを開始してください。")
    squad = state["squad"]
    st.subheader(f"🏟️ {state['club']} — シーズン {state['season']}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("移籍予算", f"€{state['budget']/1_000_000:.1f}M")
    m2.metric("試合数", state["played"])
    m3.metric("勝ち点", state["points"])
    m4.metric("戦績", f"{state['wins']}勝 {state['draws']}分 {state['losses']}敗")

    if squad.empty:
        st.warning("このクラブの選手がCSV内にいません。CSVのTeam列にクラブ名があるか確認してください。")
        st.write("CSV内のクラブ例:", ", ".join(teams[:30]))
        return

    st.subheader("👥 チーム編成")
    display_cols = [c for c in ["Name", "Position", "OVR", "Age", "PAC", "SHO", "PAS", "DRI", "DEF", "PHY"] if c in squad.columns]
    st.dataframe(squad.sort_values("OVR", ascending=False)[display_cols], use_container_width=True, hide_index=True)
    names = squad["Name"].drop_duplicates().tolist()
    default_starters = squad.sort_values("OVR", ascending=False)["Name"].drop_duplicates().head(min(11, len(names))).tolist()
    starters = st.multiselect("スタメン（最大11人）", names, default=default_starters[:11], max_selections=11, key="career_starters")
    bench_candidates = [n for n in names if n not in starters]
    subs = st.multiselect("交代で使う候補（最大5人）", bench_candidates, max_selections=5, key="career_subs")

    st.subheader("💼 移籍市場")
    all_players = players[~players["Name"].isin(squad["Name"])].copy()
    all_players = all_players.sort_values("OVR", ascending=False)
    search = st.text_input("獲得したい選手を検索", key="career_transfer_search")
    if search:
        all_players = all_players[all_players["Name"].str.contains(search, case=False, na=False)]
    if not all_players.empty:
        transfer_cols = [c for c in ["Name", "Team", "Position", "OVR", "Age", "EstimatedValue"] if c in all_players.columns]
        pick_options = all_players.head(300)["Name"].drop_duplicates().tolist()
        picked = st.selectbox("獲得候補", pick_options, key="career_transfer_player")
        target = all_players[all_players["Name"] == picked].iloc[0]
        fee = int(target["EstimatedValue"] * (1.15 if _num(target["Age"], 27) < 24 else 1.0))
        st.write(f"所属: {target['Team']} / OVR: {int(target['OVR'])} / 推定移籍金: €{fee:,}")
        if st.button("この選手を獲得", key="career_buy"):
            if fee > state["budget"]:
                st.error("移籍予算が足りません。")
            elif picked in state["squad"]["Name"].values:
                st.warning("この選手はすでに所属しています。")
            else:
                new_row = target.copy()
                new_row["Team"] = state["club"]
                state["squad"] = pd.concat([state["squad"], new_row.to_frame().T], ignore_index=True)
                state["budget"] -= fee
                st.session_state.career_state = state
                st.success(f"{picked}を獲得しました。")
                st.rerun()
        st.caption("選手の推定移籍金はOVR・年齢から計算したゲーム内の目安です。実際の移籍金ではありません。")
    else:
        st.info("検索条件に合う獲得候補がいません。")

    if len(squad) > 11:
        release = st.selectbox("放出する選手（任意）", ["放出しない"] + squad["Name"].tolist(), key="career_release")
        if release != "放出しない" and st.button("選手を放出", key="career_sell"):
            row = state["squad"][state["squad"]["Name"] == release].iloc[0]
            fee = int(_num(row.get("EstimatedValue"), 0) * 0.65)
            state["budget"] += fee
            state["squad"] = state["squad"][state["squad"]["Name"] != release].copy()
            st.session_state.career_state = state
            st.success(f"{release}を放出。€{fee:,}を獲得しました。")
            st.rerun()

    st.subheader("🧠 戦術設定")
    col1, col2, col3 = st.columns(3)
    with col1:
        formation = st.selectbox("フォーメーション", ["4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "5-3-2"], key="career_formation")
    with col2:
        tactic = st.selectbox("チーム戦術", ["ポゼッション", "カウンター", "ハイプレス"], key="career_tactic")
    with col3:
        risk = st.selectbox("試合運び", ["守備重視", "バランス", "攻撃重視"], key="career_risk")

    st.subheader("⚽ 次の試合")
    other_teams = [t for t in teams if t != state["club"]]
    if not other_teams:
        st.warning("対戦相手となる別クラブがCSV内にありません。")
        return
    opponent = st.selectbox("対戦相手", other_teams, key="career_opponent")
    opp_rows = players[players["Team"] == opponent]
    opp_strength = _num(opp_rows.sort_values("OVR", ascending=False).head(11)["OVR"].mean(), 68)
    st.write(f"相手の推定強さ: {opp_strength:.1f} / 自チームのスタメン人数: {len(starters)}人")
    if len(starters) < 7:
        st.warning("試合開始にはスタメンを7人以上選んでください。")
    elif st.button("試合を開始", type="primary", key="career_play_match"):
        record = _play_match(state, opponent, tactic, formation, opp_strength, starters, subs, risk)
        st.session_state.career_state = state
        st.success(f"{record['結果']}！ {state['club']} {record['スコア']} {opponent}")
        st.write(f"戦術: {tactic} / {formation} / {risk}")
        if subs:
            st.write("交代候補として指定: " + ", ".join(subs))
        st.rerun()

    if state["history"]:
        st.subheader("📅 試合結果")
        st.dataframe(pd.DataFrame(state["history"]).iloc[::-1], use_container_width=True, hide_index=True)
        played = state["played"]
        gd = state["gf"] - state["ga"]
        st.write(f"得失点差: {gd:+d} / 勝率: {(state['wins'] / played * 100):.1f}%" if played else "まだ試合をしていません")
        if st.button("シーズンを終了して次のシーズンへ", key="career_next_season"):
            state["season"] += 1
            state["played"] = state["wins"] = state["draws"] = state["losses"] = 0
            state["gf"] = state["ga"] = state["points"] = 0
            state["history"] = []
            state["budget"] += max(2_000_000, int(state["initial_budget"] * 0.08))
            st.session_state.career_state = state
            st.success("次のシーズンを開始しました。新しいシーズン予算を追加しました。")
            st.rerun()
