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
    """Reset team statistics for a new season while preserving match history"""
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

def check_and_reset_season():
    """Check if any team has reached 38 matches and reset if needed"""
    for team in VALID_TEAMS:
        if st.session_state.team_stats[team]["P"] >= 38:
            st.warning(f"⚠️ **Season {st.session_state.season_number} Complete!** {team} has played 38 matches. Starting Season {st.session_state.season_number + 1}...")
            reset_league_for_new_season()
            return True
    return False

def calculate_rankings():
    """Calculate team rankings based on current stats"""
    sorted_teams = sorted(
        st.session_state.team_stats.items(),
        key=lambda x: (x[1]["Pts"], x[1]["GD"], x[1]["GF"]),
        reverse=True
    )
    return sorted_teams

def get_team_position(team_name):
    """Get current ranking position for a team"""
    rankings = calculate_rankings()
    for pos, (team, _) in enumerate(rankings, 1):
        if team == team_name:
            return pos
    return None

def calculate_team_metrics():
    """Calculate detailed metrics for each team"""
    metrics = {}
    for team in VALID_TEAMS:
        stats = st.session_state.team_stats[team]
        total_matches = stats["P"]
        win_rate = (stats["W"] / total_matches * 100) if total_matches > 0 else 0
        draw_rate = (stats["D"] / total_matches * 100) if total_matches > 0 else 0
        loss_rate = (stats["L"] / total_matches * 100) if total_matches > 0 else 0
        avg_gf = stats["GF"] / total_matches if total_matches > 0 else 0
        avg_ga = stats["GA"] / total_matches if total_matches > 0 else 0

        # Calculate actual Both Teams Scored rate from match data
        bts_matches = 0
        for match in st.session_state.match_data:
            if (match[1] == team or match[4] == team) and (match[2] > 0 and match[3] > 0):
                bts_matches += 1

        bts_rate = (bts_matches / total_matches * 100) if total_matches > 0 else 0

        metrics[team] = {
            "win_rate": round(win_rate, 1),
            "draw_rate": round(draw_rate, 1),
            "loss_rate": round(loss_rate, 1),
            "avg_gf": round(avg_gf, 2),
            "avg_ga": round(avg_ga, 2),
            "bts_rate": round(bts_rate, 1),
            "form": stats["Form"][-5:] if len(stats["Form"]) >= 5 else stats["Form"],
            "points_per_game": round(stats["Pts"] / total_matches, 2) if total_matches > 0 else 0,
        }
    return metrics

def predict_match_outcome(home_team, away_team, team_metrics):
    """Predict match outcome probabilities"""
    home_metrics = team_metrics[home_team]
    away_metrics = team_metrics[away_team]

    # Base probabilities from win rates
    home_win_prob = home_metrics["win_rate"] * (1 - away_metrics["win_rate"] / 100)
    away_win_prob = away_metrics["win_rate"] * (1 - home_metrics["win_rate"] / 100)
    draw_prob = (home_metrics["draw_rate"] + away_metrics["draw_rate"]) / 2

    # Adjust for home advantage
    home_advantage = 15  # percentage points
    home_win_prob += home_advantage
    away_win_prob = max(0, away_win_prob - home_advantage * 0.5)

    # Normalize to 100%
    total = home_win_prob + away_win_prob + draw_prob
    if total > 0:
        home_win_prob = (home_win_prob / total * 100)
        away_win_prob = (away_win_prob / total * 100)
        draw_prob = (draw_prob / total * 100)
    else:
        home_win_prob = draw_prob = away_win_prob = 33.3

    # Calculate over/under probabilities (heuristic)
    total_goals_expected = home_metrics["avg_gf"] + away_metrics["avg_gf"]
    over_2_5_prob = min(90, max(10, (total_goals_expected - 1.5) * 30))
    over_3_5_prob = min(70, max(5, (total_goals_expected - 2.5) * 25))
    over_4_5_prob = min(50, max(2, (total_goals_expected - 3.5) * 20))

    # Both teams score probability
    both_teams_score_prob = (home_metrics["bts_rate"] + away_metrics["bts_rate"]) / 2

    # Clamp probabilities
    home_win_prob = max(0, min(100, home_win_prob))
    away_win_prob = max(0, min(100, away_win_prob))
    draw_prob = max(0, min(100, draw_prob))
    over_2_5_prob = max(0, min(100, over_2_5_prob))
    over_3_5_prob = max(0, min(100, over_3_5_prob))
    over_4_5_prob = max(0, min(100, over_4_5_prob))
    both_teams_score_prob = max(0, min(100, both_teams_score_prob))

    return {
        "home_win": round(home_win_prob, 1),
        "away_win": round(away_win_prob, 1),
        "draw": round(draw_prob, 1),
        "over_2_5": round(over_2_5_prob, 1),
        "over_3_5": round(over_3_5_prob, 1),
        "over_4_5": round(over_4_5_prob, 1),
        "both_teams_score": round(both_teams_score_prob, 1),
        "expected_goals": round(total_goals_expected, 2),
        "predicted_score": f"{round(home_metrics['avg_gf'], 1)}-{round(away_metrics['avg_gf'], 1)}"
    }

def create_head_to_head_stats(home_team, away_team):
    """Calculate head-to-head statistics"""
    if len(st.session_state.match_data) == 0:
        return None

    h2h_matches = []
    for match in st.session_state.match_data:
        if (match[1] == home_team and match[4] == away_team) or (match[1] == away_team and match[4] == home_team):
            h2h_matches.append(match)

    if not h2h_matches:
        return None

    stats = {
        "total_matches": len(h2h_matches),
        "home_wins": 0,
        "away_wins": 0,
        "draws": 0,
        "avg_goals": 0,
        "over_2_5": 0,
        "over_3_5": 0,
        "both_teams_score": 0
    }

    total_goals = 0
    for match in h2h_matches:
        home_score = match[2]
        away_score = match[3]
        total_goals += home_score + away_score

        if match[1] == home_team:
            if home_score > away_score:
                stats["home_wins"] += 1
            elif away_score > home_score:
                stats["away_wins"] += 1
            else:
                stats["draws"] += 1
        else:
            if away_score > home_score:
                stats["home_wins"] += 1
            elif home_score > away_score:
                stats["away_wins"] += 1
            else:
                stats["draws"] += 1

        if home_score + away_score > 2.5:
            stats["over_2_5"] += 1
        if home_score + away_score > 3.5:
            stats["over_3_5"] += 1
        if home_score > 0 and away_score > 0:
            stats["both_teams_score"] += 1

    stats["avg_goals"] = round(total_goals / len(h2h_matches), 2)
    stats["over_2_5_pct"] = round(stats["over_2_5"] / len(h2h_matches) * 100, 1)
    stats["over_3_5_pct"] = round(stats["over_3_5"] / len(h2h_matches) * 100, 1)
    stats["both_teams_score_pct"] = round(stats["both_teams_score"] / len(h2h_matches) * 100, 1)

    return stats

def generate_betting_recommendations(home_team, away_team, predictions, team_metrics, h2h_stats):
    """Generate betting recommendations based on analysis"""
    home_metrics = team_metrics[home_team]
    away_metrics = team_metrics[away_team]

    recommendations = {"best_bets": [], "avoid_bets": [], "insights": []}

    # Both Teams to Score
    bts_prob = predictions['both_teams_score']
    if bts_prob >= 50:
        reason = f"{home_team} leaks goals ({home_metrics['avg_ga']} GA/game) | {away_team} can score ({away_metrics['avg_gf']} GF/game)"
        if h2h_stats and h2h_stats.get('both_teams_score_pct', 0) >= 70:
            reason += f" | Historical: {h2h_stats['both_teams_score_pct']}% both teams scored"
        recommendations["best_bets"].append(("Both Teams to Score: YES", reason))
    else:
        recommendations["avoid_bets"].append("Both Teams to Score")

    # Double Chance (Home Win or Draw)
    home_win_or_draw = predictions['home_win'] + predictions['draw']
    if home_win_or_draw >= 65:
        reason = f"{home_win_or_draw}% probability | Covers both likely outcomes"
        recommendations["best_bets"].append((f"{home_team} or Draw (Double Chance)", reason))

    # Under/Over markets
    if predictions['over_2_5'] < 50:
        under_prob = 100 - predictions['over_2_5']
        reason = f"{under_prob}% probability | {away_team}'s defense ({away_metrics['avg_ga']} GA) considered"
        recommendations["best_bets"].append(("Under 2.5 Goals", reason))
    else:
        reason = f"{predictions['over_2_5']}% probability | High expected goals ({predictions['expected_goals']})"
        recommendations["best_bets"].append(("Over 2.5 Goals", reason))

    # Clean Sheet analysis
    if home_metrics['avg_ga'] > 1.4:
        reason = f"Poor defense ({home_metrics['avg_ga']} GA/game) | Rarely keeps clean sheets"
        recommendations["avoid_bets"].append(f"{home_team} to Win to Nil (Clean Sheet)")

    # High over markets
    if predictions['over_3_5'] < 25:
        reason = f"Only {predictions['over_3_5']}% probability | Low scoring teams"
        recommendations["avoid_bets"].append("Over 3.5 Goals")
    if predictions['over_4_5'] < 10:
        recommendations["avoid_bets"].append("Over 4.5 Goals")

    # Insights on attack/defense
    if home_metrics['avg_gf'] > away_metrics['avg_gf']:
        recommendations["insights"].append(f"{home_team} has better attack ({home_metrics['avg_gf']} vs {away_metrics['avg_gf']} GF/game)")
    else:
        recommendations["insights"].append(f"{away_team} has better attack ({away_metrics['avg_gf']} vs {home_metrics['avg_gf']} GF/game)")

    if away_metrics['avg_ga'] < home_metrics['avg_ga']:
        recommendations["insights"].append(f"{away_team} has better defense ({away_metrics['avg_ga']} vs {home_metrics['avg_ga']} GA/game)")
    else:
        recommendations["insights"].append(f"{home_team} has better defense ({home_metrics['avg_ga']} vs {away_metrics['avg_ga']} GA/game)")

    if h2h_stats and h2h_stats.get('total_matches', 0) > 0:
        if h2h_stats['home_wins'] == 0 and h2h_stats['away_wins'] == 0:
            recommendations["insights"].append(f"Historical trend: {h2h_stats['draws']}/{h2h_stats['total_matches']} matches ended in draw")
        elif h2h_stats['home_wins'] > h2h_stats['away_wins'] * 2:
            recommendations["insights"].append(f"Strong historical advantage for home side")
        elif h2h_stats['away_wins'] > h2h_stats['home_wins'] * 2:
            recommendations["insights"].append(f"Strong historical advantage for away side")

    return recommendations

def clean_and_parse_matches(text: str):
    """Clean messy input data and parse matches"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_lines = []
    for line in lines:
        skip_patterns = [
            r'WEEK \d+',
            r'English League',
            r'\d{1,2}:\d{2}\s*(?:am|pm)',
            r'#\d+',
            r'^\d{8,}$',
        ]
        is_team = line in VALID_TEAMS
        is_score = line.isdigit() and 0 <= int(line) <= 20
        if is_team or is_score:
            cleaned_lines.append(line)
        else:
            skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    skip = True
                    break
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

        home_team = cleaned_lines[i]
        home_score_raw = cleaned_lines[i+1]
        away_score_raw = cleaned_lines[i+2]
        away_team = cleaned_lines[i+3]

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
page = st.sidebar.selectbox("Select page", ["Main Dashboard", "Counter Logic Dashboard"])

# -------------------------
# Page: Counter Logic Dashboard
# -------------------------
if page == "Counter Logic Dashboard":
    st.title("🧮 Counter Logic Dashboard — FI=4HA & Status3 (Last 10 Unique Matches)")

    st.markdown(
        """
        This view shows the **FI=4HA** and **Status3** outputs for the **last 10 unique match pairs**.
        Duplicate pairings (same two teams, regardless of home/away order) are shown only once — the most recent occurrence is used.
        """
    )

    if len(st.session_state.match_data) == 0:
        st.info("No matches available yet. Add matches from the Main Dashboard to populate these counters.")
    else:
        # Build mapping from unordered pair -> latest match (by Match_ID)
        latest_by_pair = {}
        for m in st.session_state.match_data:
            # Defensive extraction
            match_id = m[0] if len(m) > 0 else 0
            home = m[1] if len(m) > 1 else ""
            away = m[4] if len(m) > 4 else ""
            pair_key = frozenset([home, away])
            # Keep the match with the highest match_id (most recent)
            if pair_key:
                existing = latest_by_pair.get(pair_key)
                if existing is None or (isinstance(existing, list) and match_id >= existing[0]):
                    latest_by_pair[pair_key] = [match_id, m]

        # Extract latest matches, sort by match_id descending (most recent first)
        latest_matches = sorted([v for v in latest_by_pair.values()], key=lambda x: x[0], reverse=True)
        # Take top 10 most recent unique pairs
        latest_10 = [item[1] for item in latest_matches[:10]]

        # Prepare display rows (show newest first)
        # We'll display them in newest -> oldest order for clarity
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("FI=4HA (Last 10 Unique Matches)")
            for m in latest_10:
                home = m[1] if len(m) > 1 else ""
                home_score = m[2] if len(m) > 2 else ""
                away_score = m[3] if len(m) > 3 else ""
                away = m[4] if len(m) > 4 else ""
                # FI display stored at index 19 or fallback to counters
                fi_display = m[19] if len(m) > 19 else f"{home}: {st.session_state.ha_counters.get(home,0)} | {away}: {st.session_state.ha_counters.get(away,0)}"
                st.markdown(f"**{home}**: {home_score}  |  **{away}**: {away_score}  —  {fi_display}")

        with right_col:
            st.subheader("Status3 (Last 10 Unique Matches)")
            for m in latest_10:
                home = m[1] if len(m) > 1 else ""
                home_score = m[2] if len(m) > 2 else ""
                away_score = m[3] if len(m) > 3 else ""
                away = m[4] if len(m) > 4 else ""
                s3_display = m[20] if len(m) > 20 else f"{home}: {st.session_state.status3_counters.get(home,0)} | {away}: {st.session_state.status3_counters.get(away,0)}"
                st.markdown(f"**{home}**: {home_score}  |  **{away}**: {away_score}  —  {s3_display}")

        st.markdown("---")
        st.subheader("Status3 Summary (Home team Status3 values for these last 10 unique matches)")

        # For the same latest_10 list, extract the home team's Status3 numeric value (index 17) or parse from display
        status3_values = []
        for m in latest_10:
            if len(m) > 17:
                status3_values.append(m[17])
            else:
                display = m[20] if len(m) > 20 else ""
                found = re.findall(r'\b(\d+)\b', str(display))
                status3_values.append(int(found[0]) if found else 0)

        # Print one value per line (newest first)
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
            # If any team already at 38, reset before adding new matches
            needs_reset = any(st.session_state.team_stats[m[0]]["P"] >= 38 or st.session_state.team_stats[m[3]]["P"] >= 38 for m in new_matches)
            if needs_reset:
                check_and_reset_season()

            for home_team, home_score, away_score, away_team in new_matches:
                # Double-check season reset for each match
                if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                    check_and_reset_season()

                match_id = st.session_state.match_counter
                st.session_state.match_counter += 1

                total_goals = home_score + away_score

                # Determine Total-G display
                if total_goals == 4:
                    total_g_display = "Won"
                elif total_goals == 3:
                    total_g_display = "3 ✔"
                else:
                    total_g_display = str(total_goals)

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
                    match_id,                # 0 Match_ID
                    home_team,               # 1 Home_Team
                    home_score,              # 2 Home_Score
                    away_score,              # 3 Away_Score
                    away_team,               # 4 Away_Team
                    total_goals,             # 5 Total_Goals
                    total_g_display,         # 6 Total-G
                    result,                  # 7 Match_Result
                    home_score - away_score, # 8 Goal_Difference
                    "Yes" if home_score > 0 and away_score > 0 else "No",  # 9 Both_Teams_Scored
                    "Over 2.5" if total_goals > 2.5 else "Under 2.5",      # 10 Over_Under
                    home_rank,               # 11 Home_Rank
                    away_rank,               # 12 Away_Rank
                    st.session_state.home_counters[home_team],  # 13 Games_Since_Last_Won_Home
                    st.session_state.away_counters[away_team],  # 14 Games_Since_Last_Won_Away
                    st.session_state.ha_counters[home_team],    # 15 Games_Since_Last_4Goals_Home (F!=4HA)
                    st.session_state.ha_counters[away_team],    # 16 Games_Since_Last_4Goals_Away (F!=4HA)
                    st.session_state.status3_counters[home_team],# 17 Games_Since_Last_3Goals_Home
                    st.session_state.status3_counters[away_team],# 18 Games_Since_Last_3Goals_Away
                    fi_display,                                 # 19 F!=4HA display
                    s3_display,                                 # 20 Status3 display
                    st.session_state.season_number,             # 21 Season_Number
                    f"Season {st.session_state.season_number}"  # 22 Season_Label
                ])

                processed_count += 1

            st.success(f"✅ Added {processed_count} matches to Season {st.session_state.season_number}")
            st.experimental_rerun()
        else:
            st.warning("⚠️ No valid matches found in the input")

    # Display dashboard only if we have match data
    if len(st.session_state.match_data) > 0:
        column_names = [
            "Match_ID", "Home_Team", "Home_Score", "Away_Score", "Away_Team",
            "Total_Goals", "Total-G", "Match_Result", "Goal_Difference",
            "Both_Teams_Scored", "Over_Under", "Home_Rank", "Away_Rank",
            "Games_Since_Last_Won_Home", "Games_Since_Last_Won_Away",
            "Games_Since_Last_4Goals_Home", "Games_Since_Last_4Goals_Away",
            "Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away",
            "F!=4HA", "Status3", "Season_Number", "Season_Label"
        ]

        df = pd.DataFrame(st.session_state.match_data, columns=column_names)

        st.markdown("---")
        st.header(f"📊 Season {st.session_state.season_number} Dashboard")

        # Row 1: League Table and Recent Matches
        col_league, col_recent = st.columns([2, 1])

        with col_league:
            st.subheader(f"🏆 Season {st.session_state.season_number} League Table")
            rankings = calculate_rankings()

            table_data = []
            for pos, (team, stats) in enumerate(rankings, 1):
                table_data.append([
                    pos, team, stats["P"], stats["W"], stats["D"], stats["L"],
                    stats["GF"], stats["GA"], stats["GD"], stats["Pts"],
                    " ".join(stats["Form"][-5:]) if stats["Form"] else "No matches"
                ])

            league_df = pd.DataFrame(
                table_data,
                columns=["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"]
            )

            st.dataframe(league_df, use_container_width=True, height=420)

            # Quick league insights
            st.subheader("📈 League Insights")
            insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)

            with insight_col1:
                if len(league_df) > 0:
                    best_attack = league_df.loc[league_df['GF'].idxmax()]
                    st.metric("Best Attack", best_attack['Team'], f"{best_attack['GF']} GF")

            with insight_col2:
                if len(league_df) > 0:
                    best_defense = league_df.loc[league_df['GA'].idxmin()]
                    st.metric("Best Defense", best_defense['Team'], f"{best_defense['GA']} GA")

            with insight_col3:
                if len(league_df) > 0:
                    best_gd = league_df.loc[league_df['GD'].idxmax()]
                    st.metric("Best GD", best_gd['Team'], f"+{best_gd['GD']}")

            with insight_col4:
                if len(league_df) > 0:
                    top_scorer = league_df.loc[league_df['Pts'].idxmax()]
                    st.metric("League Leader", top_scorer['Team'], f"{top_scorer['Pts']} Pts")

        with col_recent:
            st.subheader("🔄 Recent Match Summary")
            st.markdown("<div style='background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;'>", unsafe_allow_html=True)

            recent_matches = st.session_state.match_data[-10:] if len(st.session_state.match_data) > 0 else []
            for match in recent_matches[::-1]:
                home = match[1]
                away = match[4]
                home_score = match[2]
                away_score = match[3]
                home_rank = match[11] if len(match) > 11 else "?"
                away_rank = match[12] if len(match) > 12 else "?"

                if home_score > away_score:
                    home_style = "color: #4CAF50; font-weight: bold;"
                    away_style = "color: #FF6B6B;"
                elif away_score > home_score:
                    home_style = "color: #FF6B6B;"
                    away_style = "color: #4CAF50; font-weight: bold;"
                else:
                    home_style = away_style = "color: #FFD700;"

                st.markdown(
                    f"<div style='font-size:14px; margin-bottom:8px; padding:5px; border-bottom:1px solid #333;'>"
                    f"<span style='{home_style}'>{home_rank}. {home}</span> "
                    f"{home_score}-{away_score} "
                    f"<span style='{away_style}'>{away} ({away_rank}.)</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

            # Quick stats
            st.subheader("📋 Quick Stats")
            total_matches = len(st.session_state.match_data)
            current_season_matches = [m for m in st.session_state.match_data if m[-2] == st.session_state.season_number]
            current_df = pd.DataFrame(current_season_matches, columns=column_names) if current_season_matches else pd.DataFrame()

            if len(current_df) > 0:
                avg_goals = current_df["Total_Goals"].mean()
                home_wins = len(current_df[current_df["Match_Result"] == "Home Win"])
                away_wins = len(current_df[current_df["Match_Result"] == "Away Win"])
                draws = len(current_df[current_df["Match_Result"] == "Draw"])

                st.metric("Season Matches", len(current_season_matches))
                st.metric("Avg Goals/Match", round(avg_goals, 2))
                st.metric("Home/Draw/Away", f"{home_wins}/{draws}/{away_wins}")
            else:
                st.metric("Total Matches", total_matches)
                st.metric("All-time Matches", total_matches)

        # Row 2: Match Predictor
        st.markdown("---")
        st.header("🎯 Match Predictor & Analytics")

        pred_col1, pred_col2 = st.columns(2)
        with pred_col1:
            home_team = st.selectbox("**Select Home Team**", sorted(VALID_TEAMS), key="home_select")
        with pred_col2:
            away_team = st.selectbox("**Select Away Team**", sorted(VALID_TEAMS), key="away_select")

        if home_team == away_team:
            st.warning("⚠️ Please select two different teams")
        else:
            team_metrics = calculate_team_metrics()
            predictions = predict_match_outcome(home_team, away_team, team_metrics)
            h2h_stats = create_head_to_head_stats(home_team, away_team)
            recommendations = generate_betting_recommendations(home_team, away_team, predictions, team_metrics, h2h_stats)

            st.subheader("📈 Match Predictions")
            outcome_col1, outcome_col2, outcome_col3 = st.columns(3)
            with outcome_col1:
                st.metric("🏠 Home Win", f"{predictions['home_win']}%")
                st.metric("⚽ Expected Goals", predictions["expected_goals"])
            with outcome_col2:
                st.metric("🔁 Draw", f"{predictions['draw']}%")
                st.metric("🔁 Predicted Score", predictions["predicted_score"])
            with outcome_col3:
                st.metric("🏁 Away Win", f"{predictions['away_win']}%")
                st.metric("⚽ BTS", f"{predictions['both_teams_score']}%")

            st.markdown("### 🔢 Over/Under Probabilities")
            ou_col1, ou_col2, ou_col3 = st.columns(3)
            with ou_col1:
                st.metric("Over 2.5", f"{predictions['over_2_5']}%")
            with ou_col2:
                st.metric("Over 3.5", f"{predictions['over_3_5']}%")
            with ou_col3:
                st.metric("Over 4.5", f"{predictions['over_4_5']}%")

            st.markdown("### 🧾 Betting Recommendations")
            st.write("**Best Bets**")
            for bet, reason in recommendations["best_bets"]:
                st.write(f"- **{bet}** — {reason}")

            st.write("**Avoid Bets**")
            for bet in recommendations["avoid_bets"]:
                st.write(f"- {bet}")

            st.write("**Insights**")
            for insight in recommendations["insights"]:
                st.write(f"- {insight}")

    else:
        st.info("No matches added yet. Paste match data in the input area above and click 'Parse and Add Matches'.")
