import streamlit as st

FCRADAR_API_KEY = st.secrets.get("FCRADAR_API_KEY", "")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# ページ設定
# ==========================================
st.set_page_config(
    page_title="EA FC27 × Transfermarkt + 監督キャリア",
    page_icon="⚽",
    layout="wide"
)

st.title("サッカー移籍金予測AI")
st.caption("EA FC27能力値 × Transfermarkt市場価値")

# ==========================================
# データ読み込み
# ==========================================
@st.cache_data
def load_data():

    ea = pd.read_csv("EAFC27-Men(1).csv")
    tm = pd.read_csv("players_small(1).csv")

    ea.columns = ea.columns.str.strip()
    tm.columns = tm.columns.str.strip()

    return ea, tm


ea, tm = load_data()
# ==========================================
# ページ切り替え
# ==========================================

# ==========================================
# 監督キャリア機能（career_mode.pyを別に置かなくても動く統合版）
# ==========================================

import random
import pandas as pd
import streamlit as st

try:
    from streamlit_sortables import sort_items
    SORTABLES_AVAILABLE = True
except ImportError:
    SORTABLES_AVAILABLE = False

# FC27 Career Mode
# Player card images use EA FC ratings image URLs when an ID is available.
# Budgets / transfer values are game estimates, not official financial data.

CLUB_BUDGETS_EUR = {
    "Real Madrid": 180_000_000, "Manchester City": 160_000_000,
    "Paris Saint-Germain": 150_000_000, "Liverpool": 120_000_000,
    "Arsenal": 110_000_000, "Chelsea": 100_000_000,
    "Manchester United": 100_000_000, "Bayern Munich": 100_000_000,
    "FC Barcelona": 90_000_000, "Tottenham Hotspur": 80_000_000,
    "Newcastle United": 75_000_000, "Inter": 70_000_000,
    "Juventus": 65_000_000, "AC Milan": 60_000_000,
    "Atlético Madrid": 60_000_000, "Borussia Dortmund": 55_000_000,
    "Napoli": 50_000_000,
}
STAT_COLS = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
TACTIC_HELP = {
    "ポゼッション": "パスをつないで試合を支配。PASが高い選手と相性がよい。",
    "カウンター": "奪って素早く攻める。PACが高い選手と相性がよい。",
    "ハイプレス": "前線から積極的に守備。PHYが高い選手と相性がよい。",
}
RISK_HELP = {
    "守備重視": "失点を抑えやすいが、得点は少なめ。",
    "バランス": "攻守のバランスを取る標準設定。",
    "攻撃重視": "得点を狙いやすいが、失点も増えやすい。",
}
FORMATIONS = {
    "4-3-3": {"GK": 1, "DF": 4, "MF": 3, "FW": 3},
    "4-2-3-1": {"GK": 1, "DF": 4, "MF": 5, "FW": 1},
    "4-4-2": {"GK": 1, "DF": 4, "MF": 4, "FW": 2},
    "3-5-2": {"GK": 1, "DF": 3, "MF": 5, "FW": 2},
    "5-3-2": {"GK": 1, "DF": 5, "MF": 3, "FW": 2},
}
ZONE_NAMES = ["GK", "DF", "MF", "FW", "控え"]

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
    base = max(150_000, max(40, ovr - 45) ** 3 * 65)
    age_factor = 1.25 if age <= 21 else 1.12 if age <= 24 else 1.0 if age <= 28 else 0.72 if age <= 31 else 0.42
    return int(base * age_factor / 10_000) * 10_000

def _image_url(row):
    player_id = row.get("ID")

    if pd.notna(player_id):
        try:
            player_id = int(float(player_id))

            # FC27の画像URL
            return (
                f"https://ratings-images-prod.pulse.ea.com/"
                f"FC27/components/items/{player_id}_en.webp"
            )
        except (TypeError, ValueError):
            pass

    return None

def _clean_players(ea):
    df = ea.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in ["Name", "Team", "OVR", "League"] if c not in df.columns]
    if missing:
        st.error("選手データに必要な列がありません: " + ", ".join(missing))
        st.caption("EAFC27-Men(1).csv に Name・Team・OVR・League の列があるか確認してください。")
        return pd.DataFrame()
    for col in ["Name", "Team", "League"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["OVR"] = pd.to_numeric(df["OVR"], errors="coerce")
    df = df[(df["Name"] != "") & (df["Team"] != "") & (df["League"] != "") & df["OVR"].notna()].copy()
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
    avg = _num(squad["OVR"].mean(), 70) if not squad.empty else 70
    return 70_000_000 if avg >= 82 else 35_000_000 if avg >= 77 else 15_000_000 if avg >= 72 else 5_000_000

def _new_state(club, league, players):
    squad = players[(players["Team"] == club) & (players["League"] == league)].copy()
    budget = _club_budget(club, squad)
    return {
        "club": club, "league": league, "squad": squad, "budget": budget,
        "initial_budget": budget, "played": 0, "wins": 0, "draws": 0,
        "losses": 0, "gf": 0, "ga": 0, "points": 0, "history": [],
        "season": 1, "last_result": None, "lineup": {}, "formation": "4-3-3",
    }

def _team_strength(squad, tactic="バランス", formation="4-3-3", selected_names=None):
    if squad.empty:
        return 55.0
    starters = squad[squad["Name"].isin(selected_names)] if selected_names else squad.sort_values("OVR", ascending=False).head(11)
    if starters.empty:
        starters = squad.sort_values("OVR", ascending=False).head(11)
    base = _num(starters["OVR"].mean(), 65)
    if tactic == "ポゼッション":
        base += (_num(starters["PAS"].mean(), 65) - 70) * 0.10
    elif tactic == "カウンター":
        base += (_num(starters["PAC"].mean(), 65) - 70) * 0.10
    elif tactic == "ハイプレス":
        base += (_num(starters["PHY"].mean(), 65) - 70) * 0.08
    return max(45.0, min(95.0, base))

def _play_match(state, opponent, tactic, formation, opponent_strength, starters, subs, risk):
    squad = state["squad"]
    active = squad[squad["Name"].isin(starters)].copy()
    if active.empty:
        active = squad.sort_values("OVR", ascending=False).head(11).copy()
    strength = _team_strength(active, tactic, formation)
    bench = squad[squad["Name"].isin(subs)]
    strength += min(1.8, len(bench) * 0.25 + max(0, _num(bench["OVR"].mean(), 0) - 75) * 0.04) if not bench.empty else 0
    risk_for = {"守備重視": -0.30, "バランス": 0.0, "攻撃重視": 0.45}[risk]
    risk_against = {"守備重視": -0.25, "バランス": 0.0, "攻撃重視": 0.30}[risk]
    tactic_bonus = {"ポゼッション": 0.10, "カウンター": 0.30, "ハイプレス": 0.20}[tactic]
    diff = (strength - opponent_strength) / 10
    expected_for = max(0.3, min(3.2, 1.25 + diff * 0.40 + tactic_bonus + risk_for + 0.20))
    expected_against = max(0.2, min(3.0, 1.10 - diff * 0.30 + risk_against))
    goals_for = sum(random.random() < min(0.85, expected_for / 5) for _ in range(5))
    goals_against = sum(random.random() < min(0.85, expected_against / 5) for _ in range(5))
    if goals_for > goals_against:
        result, points = "勝利", 3
        state["wins"] += 1
    elif goals_for == goals_against:
        result, points = "引き分け", 1
        state["draws"] += 1
    else:
        result, points = "敗戦", 0
        state["losses"] += 1
    state["played"] += 1
    state["points"] += points
    state["gf"] += goals_for
    state["ga"] += goals_against
    record = {
        "節": state["played"], "対戦相手": opponent,
        "スコア": f"{goals_for} - {goals_against}", "結果": result,
        "戦術": tactic, "フォーメーション": formation, "試合運び": risk,
        "交代候補": ", ".join(subs) if subs else "使用なし",
    }
    state["history"].append(record)
    state["last_result"] = record
    return record

def _yen_eur(amount):
    return f"€{amount / 1_000_000:.1f}M"

def _player_label(row):
    return f"{row['Name']}  |  OVR {int(_num(row.get('OVR'), 0))}  |  {row.get('Position', 'CM')}"

def _make_lineup_defaults(squad, formation):
    groups = FORMATIONS[formation]
    # Assign by role where possible; then fill empty positions by overall rating.
    role_candidates = {
        "GK": squad[squad["Position"].str.contains("GK", na=False)].sort_values("OVR", ascending=False),
        "DF": squad[squad["Position"].str.contains(r"CB|LB|RB|LWB|RWB", na=False)].sort_values("OVR", ascending=False),
        "MF": squad[squad["Position"].str.contains(r"CDM|CM|CAM|LM|RM", na=False)].sort_values("OVR", ascending=False),
        "FW": squad[squad["Position"].str.contains(r"LW|RW|ST|CF", na=False)].sort_values("OVR", ascending=False),
    }
    chosen = {}
    used = set()
    for zone in ["GK", "DF", "MF", "FW"]:
        names = []
        for _, row in role_candidates[zone].iterrows():
            if row["Name"] not in used and len(names) < groups[zone]:
                names.append(row["Name"])
                used.add(row["Name"])
        if len(names) < groups[zone]:
            for _, row in squad.sort_values("OVR", ascending=False).iterrows():
                if row["Name"] not in used and len(names) < groups[zone]:
                    names.append(row["Name"])
                    used.add(row["Name"])
        chosen[zone] = names
    chosen["控え"] = [n for n in squad.sort_values("OVR", ascending=False)["Name"].tolist() if n not in used]
    return chosen

def _render_player_cards(squad, names, max_cards=11):
    rows = squad[squad["Name"].isin(names)].drop_duplicates("Name")
    if rows.empty:
        st.caption("選手が選択されていません。")
        return
    cols = st.columns(min(4, max(1, len(rows.head(max_cards)))))
    for i, (_, row) in enumerate(rows.head(max_cards).iterrows()):
        with cols[i % len(cols)]:
            img = _image_url(row)
            if img:
                st.image(img, use_container_width=True)
            st.markdown(f"**{row['Name']}**")
            st.caption(f"{row.get('Position', '—')} · OVR {int(row['OVR'])}")

def render_career_mode(ea):
    st.header("⚽ 監督キャリア")
    st.caption("クラブを選び、選手カードを並べてフォーメーションを作り、同じリーグの相手と対戦しよう。")
    st.info("**遊び方：** ①クラブを選ぶ → ②フォーメーションを選ぶ → ③選手をドラッグして配置 → ④同じリーグの相手と試合。")
    players = _clean_players(ea)
    if players.empty:
        return
    teams = sorted(players["Team"].dropna().unique().tolist())
    league_by_team = players.groupby("Team")["League"].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]).to_dict()
    if len(teams) < 2:
        st.warning("CSVから2つ以上のクラブを読み取れませんでした。")
        return
    preferred = [t for t in CLUB_BUDGETS_EUR if t in teams]
    options = preferred + [t for t in teams if t not in preferred]
    if "career_state" not in st.session_state:
        st.session_state.career_state = None

    state = st.session_state.career_state
    default_club = state["club"] if state and state["club"] in options else options[0]
    chosen = st.selectbox("🏟️ 監督するクラブ", options, index=options.index(default_club), key="career_easy_club")
    chosen_league = league_by_team.get(chosen, "")
    st.caption(f"所属リーグ：**{chosen_league}**")
    a, b = st.columns([1, 2])
    with a:
        if st.button("🚀 キャリア開始 / 選び直す", type="primary", use_container_width=True):
            st.session_state.career_state = _new_state(chosen, chosen_league, players)
            st.session_state.career_state["lineup"] = _make_lineup_defaults(st.session_state.career_state["squad"], "4-3-3")
            st.rerun()
    with b:
        st.caption("クラブを選び直して開始すると、現在のセーブは置き換わります。")

    state = st.session_state.career_state
    if state is None:
        st.subheader("まずはクラブを選んでキャリアを始めよう")
        return
    if state["club"] != chosen:
        st.warning("別のクラブを選択中です。切り替える場合は「キャリア開始 / 選び直す」を押してください。")
    squad = state["squad"]
    if squad.empty:
        st.error("このクラブの選手データがありません。Team列とLeague列を確認してください。")
        return

    # Make sure the selected club's league is fixed for the whole save.
    league = state.get("league", chosen_league)
    league_teams = sorted(players.loc[players["League"] == league, "Team"].dropna().unique().tolist())
    opponents = [t for t in league_teams if t != state["club"]]
    st.subheader(f"🏆 {state['club']}  ·  {league}  ·  シーズン {state['season']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 移籍予算", _yen_eur(state["budget"]))
    c2.metric("⚽ 試合数", str(state["played"]))
    c3.metric("⭐ 勝ち点", str(state["points"]))
    c4.metric("📊 戦績", f"{state['wins']}勝 {state['draws']}分 {state['losses']}敗")
    tab_home, tab_squad, tab_transfer, tab_match, tab_results = st.tabs(
        ["🏠 ホーム", "🧩 フォーメーション", "🔄 移籍市場", "⚽ 試合", "📅 戦績"]
    )

    with tab_home:
        x, y, z = st.columns(3)
        x.metric("登録選手", f"{squad['Name'].nunique()}人")
        y.metric("平均OVR", f"{_num(squad['OVR'].mean(), 0):.1f}")
        z.metric("得失点差", f"{state['gf'] - state['ga']:+d}")
        st.markdown("### 🌟 主力選手")
        _render_player_cards(squad, squad.sort_values("OVR", ascending=False)["Name"].tolist(), 5)
        if state["last_result"]:
            r = state["last_result"]
            st.success(f"直近の試合：{r['結果']}　|　{state['club']} {r['スコア']} {r['対戦相手']}")
        else:
            st.info("まだ試合をしていません。「試合」タブから最初の試合を始めよう。")
        st.caption("※カード画像が表示されない場合、EA側に画像がない選手の可能性があります。予算・移籍金はゲーム用推定値です。")

    with tab_squad:
        st.markdown("### 🧩 フォーメーションを組もう")
        formation = st.selectbox("フォーメーション", list(FORMATIONS), index=list(FORMATIONS).index(state.get("formation", "4-3-3")), key="career_easy_formation")
        if formation != state.get("formation"):
            state["formation"] = formation
            state["lineup"] = _make_lineup_defaults(squad, formation)
            st.session_state.career_state = state
        groups = FORMATIONS[formation]
        st.caption(f"{formation}：GK {groups['GK']}人 / DF {groups['DF']}人 / MF {groups['MF']}人 / FW {groups['FW']}人")
        st.markdown("**下の選手カードをドラッグして、GK・DF・MF・FW・控えのエリアに移動してください。**")
        st.caption("各エリア内の順番もドラッグで変更できます。試合にはGK 1人・DF/MF/FWは選んだフォーメーションの人数が反映されます。")
        if SORTABLES_AVAILABLE:
            current_lineup = state.get("lineup") or _make_lineup_defaults(squad, formation)
            valid_names = set(squad["Name"].tolist())
            items = []
            for zone in ZONE_NAMES:
                names = [n for n in current_lineup.get(zone, []) if n in valid_names]
                items.append({
                    "header": zone,
                    "items": [
                        _player_label(squad[squad["Name"] == n].iloc[0])
                        for n in names
                    ]
                })

            # Sortable component returns the contents of each drag-and-drop zone.
            sorted_items = sort_items(
                items,
                multi_containers=True,
                direction="vertical",
                key="career_drag_lineup"
            )
            sorted_items = sort_items(
                items,
                multi_containers=True,
                direction="vertical",
                key="career_drag_lineup_v2"
            )
            label_to_name = {}
            for _, row in squad.drop_duplicates("Name").iterrows():
                label_to_name[_player_label(row)] = row["Name"]
            new_lineup = {zone: [] for zone in ZONE_NAMES}

            for container in sorted_items:
                zone = container.get("header")
                labels = container.get("items", [])

                if zone not in new_lineup:
                    continue

                for label in labels:
                    if label in label_to_name:
                        new_lineup[zone].append(label_to_name[label])
            # Avoid accidental duplicate placement.
            seen = set()
            for zone in ZONE_NAMES:
                unique = []
                for name in new_lineup[zone]:
                    if name not in seen:
                        unique.append(name)
                        seen.add(name)
                new_lineup[zone] = unique
            for _, row in squad.sort_values("OVR", ascending=False).iterrows():
                if row["Name"] not in seen:
                    new_lineup["控え"].append(row["Name"])
                    seen.add(row["Name"])
            state["lineup"] = new_lineup
            st.session_state.career_state = state
            if len(new_lineup["GK"]) != groups["GK"] or len(new_lineup["DF"]) != groups["DF"] or len(new_lineup["MF"]) != groups["MF"] or len(new_lineup["FW"]) != groups["FW"]:
                st.warning("人数がフォーメーションと一致していません。GK・DF・MF・FWの各エリアに必要人数を配置してください。")
            st.markdown("### 📸 配置中の選手カード")
            _render_player_cards(squad, new_lineup["GK"] + new_lineup["DF"] + new_lineup["MF"] + new_lineup["FW"], 11)
        else:
            st.error("ドラッグ＆ドロップ機能の準備が必要です。次の手順で requirements.txt を更新してください。")
            st.code("streamlit-sortables>=0.3.1", language="text")
            st.caption("GitHubリポジトリの requirements.txt に上の1行を追加し、アプリを再起動してください。")
            names = squad["Name"].drop_duplicates().tolist()
            current = state.get("lineup") or _make_lineup_defaults(squad, formation)
            for zone in ["GK", "DF", "MF", "FW"]:
                state["lineup"][zone] = st.multiselect(f"{zone} の選手", names, default=[n for n in current.get(zone, []) if n in names], key=f"career_fallback_{zone}")
            state["lineup"]["控え"] = [n for n in names if n not in sum([state["lineup"].get(z, []) for z in ["GK", "DF", "MF", "FW"]], [])]
        starters = state.get("lineup", {})
        starters_flat = starters.get("GK", []) + starters.get("DF", []) + starters.get("MF", []) + starters.get("FW", [])
        st.metric("配置したスタメン", f"{len(starters_flat)} / 11 人")
        st.session_state.career_state = state

    with tab_transfer:
        st.markdown("### 🔄 移籍市場")
        st.caption("選手を検索して獲得できます。獲得した選手は自クラブの選手として登録されます。")
        search = st.text_input("選手名で検索", key="career_easy_transfer_search")
        pool = players[(players["League"] == league) & (~players["Name"].isin(squad["Name"]))].copy()
        if search:
            pool = pool[pool["Name"].str.contains(search, case=False, na=False)]
        pool = pool.sort_values("OVR", ascending=False)
        if pool.empty:
            st.info("同じリーグ内に条件に合う選手がいません。")
        else:
            candidates = pool.head(300)
            label_map = {f"{r['Name']}｜{r['Team']}｜OVR {int(r['OVR'])}": idx for idx, r in candidates.iterrows()}
            picked_label = st.selectbox("獲得候補（同じリーグ）", list(label_map), key="career_easy_transfer_pick")
            target = candidates.loc[label_map[picked_label]]
            fee = int(target["EstimatedValue"] * (1.15 if _num(target["Age"], 27) < 24 else 1.0))
            x, y, z = st.columns(3)
            x.metric("OVR", int(target["OVR"]))
            y.metric("年齢", f"{int(target['Age'])}歳")
            z.metric("推定移籍金", _yen_eur(fee))
            _render_player_cards(candidates, [target["Name"]], 1)
            st.write(f"所属：**{target['Team']}**　｜　ポジション：**{target['Position']}**")
            if fee > state["budget"]:
                st.warning("現在の予算では獲得できません。")
            if st.button("✅ この選手を獲得", disabled=fee > state["budget"], key="career_easy_buy"):
                new_row = target.copy()
                new_row["Team"] = state["club"]
                new_row["League"] = league
                state["squad"] = pd.concat([state["squad"], new_row.to_frame().T], ignore_index=True)
                state["budget"] -= fee
                state["lineup"] = _make_lineup_defaults(state["squad"], state.get("formation", "4-3-3"))
                st.session_state.career_state = state
                st.rerun()
        st.divider()
        st.markdown("### 選手を放出")
        if len(squad) <= 11:
            st.caption("登録選手が11人以下のため、放出できません。")
        else:
            release = st.selectbox("放出する選手", ["選択してください"] + squad["Name"].tolist(), key="career_easy_release")
            if release != "選択してください":
                row = squad[squad["Name"] == release].iloc[0]
                fee_back = int(_num(row.get("EstimatedValue"), 0) * 0.65)
                st.caption(f"放出すると予算が約{_yen_eur(fee_back)}増えます。")
                if st.button("選手を放出", key="career_easy_sell"):
                    state["budget"] += fee_back
                    state["squad"] = state["squad"][state["squad"]["Name"] != release].copy()
                    state["lineup"] = _make_lineup_defaults(state["squad"], state.get("formation", "4-3-3"))
                    st.session_state.career_state = state
                    st.rerun()

    with tab_match:
        st.markdown("### ⚽ 次の試合")
        if not opponents:
            st.warning("このクラブと同じリーグの別クラブが見つかりません。League列の値を確認してください。")
        else:
            opponent = st.selectbox("対戦相手（所属リーグ内のみ）", opponents, key="career_easy_opponent")
            opp_rows = players[(players["Team"] == opponent) & (players["League"] == league)]
            opp_strength = _num(opp_rows.sort_values("OVR", ascending=False).head(11)["OVR"].mean(), 68)
            lineup = state.get("lineup") or _make_lineup_defaults(squad, state.get("formation", "4-3-3"))
            starters = lineup.get("GK", []) + lineup.get("DF", []) + lineup.get("MF", []) + lineup.get("FW", [])
            subs = lineup.get("控え", [])[:5]
            f1, f2 = st.columns(2)
            with f1:
                tactic = st.selectbox("チーム戦術", list(TACTIC_HELP), key="career_easy_tactic")
                st.info(TACTIC_HELP[tactic])
            with f2:
                risk = st.selectbox("試合運び", list(RISK_HELP), key="career_easy_risk")
                st.info(RISK_HELP[risk])
                st.metric("相手の推定チーム力", f"{opp_strength:.1f} OVR")
                st.metric("配置したスタメン", f"{len(starters)} / 11 人")
            required = FORMATIONS.get(state.get("formation", "4-3-3"), FORMATIONS["4-3-3"])
            correct = len(lineup.get("GK", [])) == required["GK"] and len(lineup.get("DF", [])) == required["DF"] and len(lineup.get("MF", [])) == required["MF"] and len(lineup.get("FW", [])) == required["FW"]
            if not correct:
                st.warning("先に「フォーメーション」タブで各エリアの人数を合わせてください。")
            if st.button("⚽ 試合開始", type="primary", key="career_easy_play", disabled=(not correct or len(starters) != 11)):
                _play_match(state, opponent, tactic, state.get("formation", "4-3-3"), opp_strength, starters, subs, risk)
                st.session_state.career_state = state
                st.rerun()
        if state.get("last_result"):
            r = state["last_result"]
            st.divider()
            st.markdown("### 🏁 直近の試合結果")
            st.subheader(f"{state['club']}　{r['スコア']}　{r['対戦相手']}")
            if r["結果"] == "勝利":
                st.success("勝利！ 勝ち点3を獲得しました。")
            elif r["結果"] == "引き分け":
                st.info("引き分け。勝ち点1を獲得しました。")
            else:
                st.warning("敗戦。次の試合で立て直そう。")
            st.write(f"戦術：{r['戦術']}　｜　フォーメーション：{r['フォーメーション']}　｜　試合運び：{r['試合運び']}")
            st.write("交代候補：" + r["交代候補"])

    with tab_results:
        st.markdown("### 📅 シーズン成績")
        played = state["played"]
        x, y, z = st.columns(3)
        x.metric("勝率", f"{state['wins'] / played * 100:.1f}%" if played else "—")
        y.metric("得失点差", f"{state['gf'] - state['ga']:+d}")
        z.metric("1試合平均勝ち点", f"{state['points'] / played:.2f}" if played else "—")
        if state["history"]:
            st.dataframe(pd.DataFrame(state["history"]).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("まだ試合結果がありません。")
        st.divider()
        st.caption("次のシーズンに進むと、現在のシーズン成績がリセットされます。")
        if st.button("⏭️ 次のシーズンへ", key="career_easy_next_season", disabled=played == 0):
            state["season"] += 1
            state["played"] = state["wins"] = state["draws"] = state["losses"] = 0
            state["gf"] = state["ga"] = state["points"] = 0
            state["history"] = []
            state["last_result"] = None
            state["budget"] += max(2_000_000, int(state["initial_budget"] * 0.08))
            st.session_state.career_state = state
            st.rerun()


page = st.sidebar.radio("🏠 メニュー",
[
    "ホーム",
    "選手分析",
    "ランキング",
    "データ閲覧",
    "監督キャリア"
]
)

if page == "監督キャリア":
    render_career_mode(ea)
    st.stop()

# ==========================================
# ホーム画面
# ==========================================

if page == "ホーム":

    st.title("⚽ EA FC27 × Transfermarkt")
    st.subheader("選手分析システム")

    st.write("""
このアプリでは、EA FC27とTransfermarktのデータを使って
世界中のサッカー選手を分析できます。
""")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("EA FC27登録選手数", len(ea))

    with col2:
        st.metric("Transfermarkt登録選手数", len(tm))

    st.divider()

    st.markdown("### 🚀 このアプリでできること")
    st.write("✅ 選手能力分析")
    st.write("✅ レーダーチャート")
    st.write("✅ 市場価値分析")
    st.write("✅ AIスカウトレポート")
    st.write("✅ 選手比較")
    st.write("✅ ランキング表示")

    st.info("👈 左のメニューから『選手分析』を選んで始めてください。")
    

# ==========================================
# クラブ日本語辞書
# ==========================================
club_dict = {
    "Real Madrid":"レアル・マドリード",
    "FC Barcelona":"FCバルセロナ",
    "Manchester City":"マンチェスター・シティ",
    "Liverpool":"リヴァプール",
    "Arsenal":"アーセナル",
    "Chelsea":"チェルシー",
    "Manchester United":"マンチェスター・ユナイテッド",
    "Tottenham Hotspur":"トッテナム",
    "Bayern Munich":"バイエルン・ミュンヘン",
    "Borussia Dortmund":"ドルトムント",
    "Paris Saint-Germain":"パリ・サンジェルマン",
    "Inter":"インテル",
    "AC Milan":"ACミラン",
    "Juventus":"ユヴェントス",
    "Napoli":"ナポリ",
    "Atlético Madrid":"アトレティコ・マドリード"
}

# ==========================================
# 検索
# ==========================================
st.sidebar.header("🔍 選手検索")

player = st.sidebar.text_input("選手名")

player_list = sorted(ea["Name"].dropna().astype(str).unique())

selected = st.sidebar.selectbox(
    "一覧から選択",
    [""] + player_list
)

if selected != "":
    player = selected

# ==========================================
# 選手表示
# ==========================================
if page == "選手分析":

    result = ea[
        ea["Name"]
        .astype(str)
        .str.contains(player, case=False, na=False)
    ]

    if result.empty:

        st.error("選手が見つかりません。")
        st.stop()

    row = result.iloc[0]

    st.header(f"⭐ {row['Name']}")
# ==========================================
# 選手カード
# ==========================================

    photo_col, info_col = st.columns([1, 2])

    with photo_col:
        card_url = row.get("card", "")
        if pd.notna(card_url) and str(card_url).strip():
            st.image(str(card_url), width=180)
        else:
            st.info("この選手のカード画像はCSVに登録されていません。")
    with info_col:
        st.header(f"⭐ {row['Name']}")
        st.metric("OVR", row["OVR"])

        if "Position" in row.index:
            st.write(f"**ポジション：** {row['Position']}")

        if "Team" in row.index:
            st.write(f"**クラブ：** {row['Team']}")

        if "Nation" in row.index:
            st.write(f"**国籍：** {row['Nation']}")

    st.divider()

    st.subheader("⚡ 能力値")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("PAC", row["PAC"])
        st.metric("DRI", row["DRI"])

    with c2:
        st.metric("SHO", row["SHO"])
        st.metric("DEF", row["DEF"])

    with c3:
        st.metric("PAS", row["PAS"])
        st.metric("PHY", row["PHY"])


# ==========================================
# 移籍市場シミュレーター
# ==========================================

    st.divider()
    st.subheader("💰 移籍市場シミュレーター")
# ==========================================
# Transfermarktデータ取得
# ==========================================

    tm_result = tm[
        tm["name"]
        .astype(str)
        .str.contains(player, case=False, na=False)
    ]

    if not tm_result.empty:
        info = tm_result.iloc[0]
        market = info["market_value_in_eur"]
    else:
        market = 0

    ovr = row["OVR"]
    age = row["Age"]
    
    if ovr >= 90:
        evaluation = "🔥 ワールドクラス"
    elif ovr >= 85:
        evaluation = "⭐ トップ選手"
    elif ovr >= 80:
        evaluation = "👍 優秀な選手"
    else:
        evaluation = "📈 成長期待"

    st.write("評価：", evaluation)

    if age <= 23:
        age_text = "若手で将来性あり"
    elif age <= 29:
        age_text = "全盛期"
    else:
        age_text = "ベテランによる価値低下あり" 

    st.write("年齢評価：", age_text)

    if market / 1_000_000 >= 100:
        price_text = "高額選手"
    else:
        price_text = "手頃な価格帯"

    st.write("市場価値評価：", price_text)
# ==========================================
# レーダーチャート
# ==========================================

if player != "" and 'row' in locals():
    st.divider()

    st.subheader("📊 能力レーダーチャート")
    
    radar_stats = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
    
    values = [float(row[s]) for s in radar_stats]
    
    values += values[:1]

    angles = np.linspace(

        0,

        2*np.pi,

        len(radar_stats),

        endpoint=False

    ).tolist()

    angles += angles[:1]

    fig = plt.figure(figsize=(6,6))

    ax = plt.subplot(111, polar=True)

    ax.plot(

        angles,

        values,

        linewidth=2

    )

    ax.fill(

        angles,

        values,

        alpha=0.25

    )

    ax.set_xticks(angles[:-1])

    ax.set_xticklabels(radar_stats)

    ax.set_ylim(0,100)

    st.pyplot(fig)

# ==========================================
# 能力値グラフ
# ==========================================

if player != "" and 'row' in locals():
    st.divider()
    st.subheader("📈 能力値グラフ")

    graph = pd.DataFrame({
    "能力": radar_stats,
    "数値": [row[s] for s in radar_stats]
    })

    st.bar_chart(
    graph.set_index("能力")
    )


# ==========================================
# EAFC27 基本情報
# ==========================================

if player != "" and 'row' in locals():
    st.divider()
    st.subheader("📋 EAFC27 基本情報")

    base_info = [
    ("年齢", "Age"),
    ("身長", "Height"),
    ("体重", "Weight"),
    ("利き足", "Preferred foot"),
    ("逆足", "Weak foot"),
    ("スキル", "Skill moves"),
    ("ポジション", "Position"),
    ("国籍", "Nation"),
    ("リーグ", "League"),
    ("チーム", "Team")
    ]

    for title, col in base_info:
        if col in ea.columns:
            st.write(f"**{title}：** {row[col]}")



# ==========================================
# GK能力（GKのみ表示）
# ==========================================

gk_stats = [
    "GK Diving",
    "GK Handling",
    "GK Kicking",
    "GK Positioning",
    "GK Reflexes"
]
if player != "" and 'row' in locals():
    if all(col in ea.columns for col in gk_stats):

        if row["Position"] == "GK":

            st.divider()
            st.subheader("🧤 GK能力")

            gk_df = pd.DataFrame({
                "能力": gk_stats,
                "数値": [row[s] for s in gk_stats]
            })

            st.bar_chart(
                gk_df.set_index("能力")
            )
if page == "選手分析":
# ==========================================
# 2選手比較
# ==========================================

    st.divider()
    st.header("👥 2選手比較")

    players = sorted(
        ea["Name"].dropna().astype(str).unique()
    )

    col1, col2 = st.columns(2)

    with col1:
        player1 = st.selectbox(
            "選手①",
            players,
            key="player1"
        )

    with col2:
        player2 = st.selectbox(
            "選手②",
            players,
            index=1 if len(players) > 1 else 0,
            key="player2"
        )

    if player1 != "" and player2 != "":

        p1 = ea[ea["Name"] == player1].iloc[0]
        p2 = ea[ea["Name"] == player2].iloc[0]

        compare_stats = [
            "PAC",
            "SHO",
            "PAS",
            "DRI",
            "DEF",
            "PHY"
        ]

        compare_df = pd.DataFrame(
            {
                player1: [p1[s] for s in compare_stats],
                player2: [p2[s] for s in compare_stats]
            },
            index=compare_stats
        )

        st.dataframe(compare_df)

        st.bar_chart(compare_df.T)
    
if page == "ランキング":

# ==========================================
# 市場価値ランキング TOP20
# ==========================================
    st.divider()
    st.header("💶 市場価値ランキング TOP20")

    ranking = (
        tm.sort_values(
            "market_value_in_eur",
            ascending=False
        )
        .head(20)
        .copy()
    )

    ranking["current_club_name"] = ranking["current_club_name"].map(
        lambda x: club_dict.get(x, x)
    )

    ranking = ranking.rename(
        columns={
            "name": "選手名",
            "current_club_name": "クラブ",
            "market_value_in_eur": "市場価値 (€)"
        }
    )

    st.dataframe(
        ranking[
        [
            "選手名",
            "クラブ",
            "市場価値 (€)"
        ]
        ],
        use_container_width=True
    )

# ==========================================
# 市場価値 TOP10 グラフ
# ==========================================

    st.divider()
    st.header("📊 市場価値 TOP10")

    top10 = (
        tm.sort_values(
            "market_value_in_eur",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top10["市場価値(M€)"] = (
        top10["market_value_in_eur"] / 1_000_000
    )

    chart = top10.set_index("name")["市場価値(M€)"]

    st.bar_chart(chart)
if page == "データ閲覧":
# ==========================================
# Transfermarkt 基本情報
# ==========================================

    st.divider()
    st.subheader("🌍 Transfermarktデータ")

    st.metric(
        "登録選手数",
        len(tm)
    )

    st.metric(
        "EAFC27登録選手数",
        len(ea)
    )
# ==========================================
# CSV閲覧
# ==========================================

    st.divider()
    st.header("📄 データ閲覧")

    with st.expander("EAFC27 データを見る"):
        st.dataframe(
            ea,
            use_container_width=True
        )

    with st.expander("Transfermarkt データを見る"):
        st.dataframe(
            tm,
            use_container_width=True
        )
if page == "データ閲覧":
# ==========================================
# CSVダウンロード
# ==========================================

    st.divider()
    st.header("📥 CSVダウンロード")

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            label="EAFC27 CSV",
            data=ea.to_csv(index=False).encode("utf-8-sig"),
            file_name="EAFC27_export.csv",
            mime="text/csv"
        )

    with col2:

        st.download_button(
            label="Transfermarkt CSV",
            data=tm.to_csv(index=False).encode("utf-8-sig"),
            file_name="Transfermarkt_export.csv",
            mime="text/csv"
        )

# ==========================================
# データ件数
# ==========================================

    st.divider()
    st.header("📊 データ件数")

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "EAFC26選手数",
            len(ea)
        )

    with c2:
        st.metric(
            "Transfermarkt選手数",
            len(tm)
        )

# ==========================================
# 列名確認（デバッグ用）
# ==========================================

    with st.expander("🛠 デバッグ情報"):

        st.write("EAFC27 Columns")
        st.write(list(ea.columns))

        st.write("Transfermarkt Columns")
        st.write(list(tm.columns))

# ==========================================
# フッター
# ==========================================

st.divider()

st.caption("⚽ EA FC27 × Transfermarkt + 監督キャリア")

st.caption("Created with Streamlit")

st.success("✅ 読み込み完了")
