import streamlit as st
import pandas as pd
import re

# -------------------------
# Configuration and teams
# -------------------------
VALID_TEAMS = {
    "Leeds", "Aston V", "Manchester Blue", "Liverpool", "London Blues", "Everton",
    "Brighton", "Sheffield U", "Tottenham", "Palace", "Newcastle", "West Ham",
    "Leicester", "West Brom", "Burnley", "London Reds", "Southampton", "Wolves",
    "Fulham", "Manchester Reds"
}

st.set_page_config(page_title="Football Results Dashboard", page_icon="⚽", layout="wide")

# -------------------------
# Session state init
# -------------------------
if "match_data" not in st.session_state:
    st.session_state.match_data = []
if "home_counters" not in st.session_state:
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
if "away_counters" not in st.session_state:
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
if "ha_counters" not in st.session_state:
    st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}  # F!=4HA counter
if "status3_counters" not in st.session_state:
    st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
if "team_stats" not in st.session_state:
    st.session_state.team_stats = {
        team: {"P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "Pts": 0, "Form": []}
        for team in VALID_TEAMS
    }
if "match_counter" not in st.session_state:
    st.session_state.match_counter = 1
if "season_number" not in st.session_state:
    st.session_state.season_number = 1

# -------------------------
# Helper functions
# -------------------------
def reset_league_for_new_season():
    st.session_state.team_stats = {
        team: {"P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "Pts": 0, "Form": []}
        for team in VALID_TEAMS
    }
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.season_number += 1
    st.session_state.match_counter = 1
    return True

def calculate_rankings():
    return sorted(
        st.session_state.team_stats.items(),
        key=lambda x: (x[1]["Pts"], x[1]["GD"], x[1]["GF"]),
        reverse=True
    )

def get_team_position(team_name):
    rankings = calculate_rankings()
    for pos, (team, _) in enumerate(rankings, 1):
        if team == team_name:
            return pos
    return None

def clean_and_parse_matches(text: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_lines = []
    for line in lines:
        skip_patterns = [r'WEEK \d+', r'English League', r'\d{1,2}:\d{2}\s*(?:am|pm)', r'#\d+', r'^\d{8,}$']
        is_team = line in VALID_TEAMS
        is_score = line.isdigit() and 0 <= int(line) <= 20
        if is_team or is_score:
            cleaned_lines.append(line)
        else:
            skip = any(re.search(p, line, re.IGNORECASE) for p in skip_patterns)
            if not skip:
                for team in VALID_TEAMS:
                    if team in line:
                        cleaned_lines.append(team)
                        break
    matches, errors = [], []
    i = 0
    while i < len(cleaned_lines):
        if i + 3 >= len(cleaned_lines):
            errors.append(f"Incomplete match at position {i+1}")
            break
        home_team, home_score_raw, away_score_raw, away_team = cleaned_lines[i:i+4]
        if home_team not in VALID_TEAMS:
            errors.append(f"Invalid home team: {home_team}")
        if away_team not in VALID_TEAMS:
            errors.append(f"Invalid away team: {away_team}")
        if not home_score_raw.isdigit():
            errors.append(f"Non-numeric home score: {home_score_raw}")
        if not away_score_raw.isdigit():
            errors.append(f"Non-numeric away score: {away_score_raw}")
        if home_team in VALID_TEAMS and away_team in VALID_TEAMS and home_score_raw.isdigit() and away_score_raw.isdigit():
            matches.append([home_team, int(home_score_raw), int(away_score_raw), away_team])
        i += 4
    matches.reverse()
    return matches, errors, cleaned_lines

# -------------------------
# UI: Sidebar navigation
# -------------------------
page = st.sidebar.selectbox("Select page", ["Main Dashboard", "Counter Logic View"])

# -------------------------
# Page: Counter Logic View (shows FI=4HA and Status3 in the requested format)
# -------------------------
if page == "Counter Logic View":
    st.title("🧮 FI=4HA and Status3 — Detailed View")

    st.markdown(
        """
        This view shows the **FI=4HA** and **Status3** outputs side-by-side as match lines,
        and a simple vertical **Status3 Summary** (one value per line) exactly in the format you requested.
        """
    )

    if len(st.session_state.match_data) == 0:
        st.info("No matches available yet. Add matches from the Main Dashboard to populate these counters.")
    else:
        # Build a DataFrame that contains FI=4HA and Status3 displays per match
        # We expect match_data entries to include the F!=4HA and Status3 display fields at indices 19 and 20
        # If older match_data structure exists, compute fallback values from counters stored in session_state.
        rows = []
        for m in st.session_state.match_data:
            # Defensive indexing and fallback
            match_id = m[0] if len(m) > 0 else ""
            home = m[1] if len(m) > 1 else ""
            home_score = m[2] if len(m) > 2 else ""
            away_score = m[3] if len(m) > 3 else ""
            away = m[4] if len(m) > 4 else ""
            # FI display (index 19) and Status3 display (index 20) if present
            fi_display = m[19] if len(m) > 19 else f"{home}: {st.session_state.ha_counters.get(home,0)} | {away}: {st.session_state.ha_counters.get(away,0)}"
            s3_display = m[20] if len(m) > 20 else f"{home}: {st.session_state.status3_counters.get(home,0)} | {away}: {st.session_state.status3_counters.get(away,0)}"
            rows.append({
                "Match_ID": match_id,
                "Home": home,
                "Home_Score": home_score,
                "Away_Score": away_score,
                "Away": away,
                "FI=4HA": fi_display,
                "Status3": s3_display
            })

        df_pairs = pd.DataFrame(rows)

        # Show side-by-side columns: left FI=4HA, right Status3 (match lines)
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("FI=4HA")
            # Display each match line as "Home: x | Away: y" with scores
            for _, row in df_pairs.iterrows():
                st.markdown(f"**{row['Home']}**: {row['Home_Score']}  |  **{row['Away']}**: {row['Away_Score']}  —  {row['FI=4HA']}")

        with right_col:
            st.subheader("Status3")
            for _, row in df_pairs.iterrows():
                st.markdown(f"**{row['Home']}**: {row['Home_Score']}  |  **{row['Away']}**: {row['Away_Score']}  —  {row['Status3']}")

        st.markdown("---")
        st.subheader("📊 Status3 Summary")

        # Build the simple vertical list of Status3 values (one per line)
        # The user requested the simple format: a heading then a column of numbers (e.g., 1 1 1 ...)
        # We'll extract the right-side numeric values for each match (prefer the home value then away value? show both per match)
        # To match the example you showed, we'll list the Status3 value for the Home team for each match in chronological order (oldest first).
        status3_values = []
        for m in st.session_state.match_data:
            # Prefer structured index 17 (home status3) if present, else parse from display string
            if len(m) > 17:
                status3_values.append(m[17])
            else:
                # parse "Home: X | Away: Y" style
                display = m[20] if len(m) > 20 else ""
                # attempt to extract first integer
                found = re.findall(r'\b(\d+)\b', str(display))
                status3_values.append(int(found[0]) if found else 0)

        # Show the simple vertical list exactly as requested
        for val in status3_values:
            st.write(val)

# -------------------------
# Page: Main Dashboard
# -------------------------
else:
    st.title("⚽ Complete Football Analytics Dashboard")

    # Top: Input area and quick actions
    st.header("📥 Data Input & Processing")
    col1, col2 = st.columns([2, 1])

    with col1:
        raw_input = st.text_area(
            "**Paste match data** (with dates/times - will be cleaned automatically)",
            height=160,
            placeholder="Example:\nAston V\n1\n2\nSheffield U\nEnglish League WEEK 17 - #2025122312\n3:58 pm\nSouthampton\n2\n0\nEverton\n..."
        )
        parse_clicked = st.button("🚀 Parse and Add Matches", type="primary", use_container_width=True)

    with col2:
        st.markdown("### 🛠️ Quick Actions")
        max_matches = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS]) if st.session_state.team_stats else 0
        st.metric("📅 Current Season", f"Season {st.session_state.season_number}", f"{max_matches}/38 matches")

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("🔄 Manual Reset", help="Reset stats for new season", use_container_width=True):
                reset_league_for_new_season()
                st.experimental_rerun()
        with action_col2:
            if st.button("🗑️ Clear All", help="Clear all match data", use_container_width=True):
                st.session_state.match_data = []
                reset_league_for_new_season()
                st.experimental_rerun()

    # Process input
    if parse_clicked and raw_input.strip():
        new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)

        if errors:
            st.error(f"❌ Found {len(errors)} parsing errors")
            for error in errors[:5]:
                st.write(f"- {error}")
            if len(errors) > 5:
                st.write(f"- ... and {len(errors) - 5} more errors")

        if new_matches:
            processed_count = 0
            for home_team, home_score, away_score, away_team in new_matches:
                match_id = st.session_state.match_counter
                st.session_state.match_counter += 1
                total_goals = home_score + away_score

                # Update counters (ha_counters = F!=4HA)
                if total_goals == 4:
                    st.session_state.home_counters[home_team] = 0
                    st.session_state.away_counters[away_team] = 0
                    st.session_state.ha_counters[home_team] = 0
                    st.session_state.ha_counters[away_team] = 0
                else:
                    st.session_state.home_counters[home_team] += 1
                    st.session_state.away_counters[away_team] += 1
                    st.session_state.ha_counters[home_team] += 1
                    st.session_state.ha_counters[away_team] += 1

                if total_goals == 3:
                    st.session_state.status3_counters[home_team] = 0
                    st.session_state.status3_counters[away_team] = 0
                else:
                    st.session_state.status3_counters[home_team] += 1
                    st.session_state.status3_counters[away_team] += 1

                # Update team stats
                st.session_state.team_stats[home_team]["P"] += 1
                st.session_state.team_stats[home_team]["GF"] += home_score
                st.session_state.team_stats[home_team]["GA"] += away_score
                st.session_state.team_stats[home_team]["GD"] = st.session_state.team_stats[home_team]["GF"] - st.session_state.team_stats[home_team]["GA"]

                st.session_state.team_stats[away_team]["P"] += 1
                st.session_state.team_stats[away_team]["GF"] += away_score
                st.session_state.team_stats[away_team]["GA"] += home_score
                st.session_state.team_stats[away_team]["GD"] = st.session_state.team_stats[away_team]["GF"] - st.session_state.team_stats[away_team]["GA"]

                # Update points and results
                if home_score > away_score:
                    st.session_state.team_stats[home_team]["W"] += 1
                    st.session_state.team_stats[home_team]["Pts"] += 3
                    st.session_state.team_stats[home_team]["Form"].append("W")
                    st.session_state.team_stats[away_team]["L"] += 1
                    st.session_state.team_stats[away_team]["Form"].append("L")
                    result = "Home Win"
                elif away_score > home_score:
                    st.session_state.team_stats[away_team]["W"] += 1
                    st.session_state.team_stats[away_team]["Pts"] += 3
                    st.session_state.team_stats[away_team]["Form"].append("W")
                    st.session_state.team_stats[home_team]["L"] += 1
                    st.session_state.team_stats[home_team]["Form"].append("L")
                    result = "Away Win"
                else:
                    st.session_state.team_stats[home_team]["D"] += 1
                    st.session_state.team_stats[home_team]["Pts"] += 1
                    st.session_state.team_stats[home_team]["Form"].append("D")
                    st.session_state.team_stats[away_team]["D"] += 1
                    st.session_state.team_stats[away_team]["Pts"] += 1
                    st.session_state.team_stats[away_team]["Form"].append("D")
                    result = "Draw"

                # Keep only last 5 form results
                if len(st.session_state.team_stats[home_team]["Form"]) > 5:
                    st.session_state.team_stats[home_team]["Form"].pop(0)
                if len(st.session_state.team_stats[away_team]["Form"]) > 5:
                    st.session_state.team_stats[away_team]["Form"].pop(0)

                # Get current rankings
                home_rank = get_team_position(home_team)
                away_rank = get_team_position(away_team)

                # Add match data with season info and displays for FI and Status3
                fi_display = f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}"
                s3_display = f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}"

                st.session_state.match_data.append([
                    match_id, home_team, home_score, away_score, away_team,
                    total_goals, str(total_goals), result, home_score - away_score,
                    "Yes" if home_score > 0 and away_score > 0 else "No",
                    "Over 2.5" if total_goals > 2.5 else "Under 2.5",
                    home_rank, away_rank,
                    st.session_state.home_counters[home_team],
                    st.session_state.away_counters[away_team],
                    st.session_state.ha_counters[home_team],
                    st.session_state.ha_counters[away_team],
                    st.session_state.status3_counters[home_team],
                    st.session_state.status3_counters[away_team],
                    fi_display,
                    s3_display,
                    st.session_state.season_number,
                    f"Season {st.session_state.season_number}"
                ])

                processed_count += 1

            st.success(f"✅ Added {processed_count} matches to Season {st.session_state.season_number}")
            st.experimental_rerun()
        else:
            st.warning("⚠️ No valid matches found in the input")

    # Display a compact league table if matches exist
    if len(st.session_state.match_data) > 0:
        # Build league table
        rankings = calculate_rankings()
        table_data = []
        for pos, (team, stats) in enumerate(rankings, 1):
            table_data.append([pos, team, stats["P"], stats["W"], stats["D"], stats["L"], stats["GF"], stats["GA"], stats["GD"], stats["Pts"], " ".join(stats["Form"][-5:]) if stats["Form"] else "No matches"])
        league_df = pd.DataFrame(table_data, columns=["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"])
        st.subheader("🏆 League Table")
        st.dataframe(league_df, use_container_width=True, height=300)
    else:
        st.info("No matches added yet. Paste match data above and click 'Parse and Add Matches'.")

# End of file
