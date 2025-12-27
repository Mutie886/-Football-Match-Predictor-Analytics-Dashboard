import streamlit as st
import pandas as pd
import re

# Allowed team names (case-sensitive)
VALID_TEAMS = {
    "Leeds", "Aston V", "Manchester Blue", "Liverpool", "London Blues", "Everton",
    "Brighton", "Sheffield U", "Tottenham", "Palace", "Newcastle", "West Ham",
    "Leicester", "West Brom", "Burnley", "London Reds", "Southampton", "Wolves",
    "Fulham", "Manchester Reds"
}

st.set_page_config(page_title="Football Results Dashboard", page_icon="⚽", layout="wide")
st.title("⚽ Complete Football Analytics Dashboard")

# ============ SESSION STATE INITIALIZATION ============
if "match_data" not in st.session_state:
    st.session_state.match_data = []
if "home_counters" not in st.session_state:
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
if "away_counters" not in st.session_state:
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
if "ha_counters" not in st.session_state:
    st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
if "status3_counters" not in st.session_state:
    st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
if "team_stats" not in st.session_state:
    st.session_state.team_stats = {
        team: {
            "P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, 
            "GD": 0, "Pts": 0, "Form": []
        }
        for team in VALID_TEAMS
    }
if "match_counter" not in st.session_state:
    st.session_state.match_counter = 1
if "season_number" not in st.session_state:
    st.session_state.season_number = 1

# ============ HELPER FUNCTIONS ============
def reset_league_for_new_season():
    """Reset team statistics for a new season while preserving match history"""
    # Reset team stats (current season only) - KEEP match_data for CSV exports
    st.session_state.team_stats = {
        team: {
            "P": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0, "Form": []
        }
        for team in VALID_TEAMS
    }
    
    # Reset counters for new season
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
    
    # Increment season number
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
            # Check if this team was involved and both teams scored
            if (match[1] == team and match[2] > 0 and match[3] > 0) or \
               (match[4] == team and match[2] > 0 and match[3] > 0):
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
    
    # Adjust for home advantage - FIXED to be more realistic
    # Calculate dynamic home advantage based on team strength
    home_strength = home_metrics["points_per_game"]
    away_strength = away_metrics["points_per_game"]
    strength_diff = home_strength - away_strength
    
    # Smart home advantage: stronger teams get more advantage
    if strength_diff > 1.0:  # Home team is much stronger
        home_advantage = 20  # +20%
    elif strength_diff > 0.5:  # Home team is stronger
        home_advantage = 15  # +15%
    elif strength_diff > 0:  # Home team is slightly stronger
        home_advantage = 12  # +12%
    elif strength_diff > -0.5:  # Teams are evenly matched
        home_advantage = 10  # +10%
    elif strength_diff > -1.0:  # Away team is stronger
        home_advantage = 7  # +7%
    else:  # Away team is much stronger
        home_advantage = 4  # Only +4% for weak home teams
    
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
    
    # Calculate over/under probabilities
    total_goals_expected = home_metrics["avg_gf"] + away_metrics["avg_gf"]
    
    over_2_5_prob = min(90, max(10, (total_goals_expected - 1.5) * 30))
    over_3_5_prob = min(70, max(5, (total_goals_expected - 2.5) * 25))
    over_4_5_prob = min(50, max(2, (total_goals_expected - 3.5) * 20))
    
    # Both teams score probability
    both_teams_score_prob = (home_metrics["bts_rate"] + away_metrics["bts_rate"]) / 2
    
    # Ensure all probabilities are within 0-100 range
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
        if (match[1] == home_team and match[4] == away_team) or \
           (match[1] == away_team and match[4] == home_team):
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
    
    recommendations = {
        "best_bets": [],
        "avoid_bets": [],
        "insights": []
    }
    
    # 1. Both Teams to Score analysis
    bts_prob = predictions['both_teams_score']
    if bts_prob >= 50:
        reason = f"{home_team} leaks goals ({home_metrics['avg_ga']} GA/game) | "
        reason += f"{away_team} can score ({away_metrics['avg_gf']} GF/game)"
        if h2h_stats and h2h_stats['both_teams_score_pct'] >= 70:
            reason += f" | Historical: {h2h_stats['both_teams_score_pct']}% both teams scored"
        recommendations["best_bets"].append(("Both Teams to Score: YES", reason))
    else:
        recommendations["avoid_bets"].append("Both Teams to Score")
    
    # 2. Double Chance (Home Win or Draw)
    home_win_or_draw = predictions['home_win'] + predictions['draw']
    if home_win_or_draw >= 65:
        reason = f"{home_win_or_draw}% probability | Covers both likely outcomes"
        recommendations["best_bets"].append((f"{home_team} or Draw (Double Chance)", reason))
    
    # 3. Under/Over markets
    if predictions['over_2_5'] < 50:
        under_prob = 100 - predictions['over_2_5']
        reason = f"{under_prob}% probability | "
        reason += f"{away_team}'s defense ({away_metrics['avg_ga']} GA) considered"
        recommendations["best_bets"].append(("Under 2.5 Goals", reason))
    else:
        reason = f"{predictions['over_2_5']}% probability | High expected goals ({predictions['expected_goals']})"
        recommendations["best_bets"].append(("Over 2.5 Goals", reason))
    
    # 4. Clean Sheet analysis
    if home_metrics['avg_ga'] > 1.4:
        reason = f"Poor defense ({home_metrics['avg_ga']} GA/game) | Rarely keeps clean sheets"
        recommendations["avoid_bets"].append(f"{home_team} to Win to Nil (Clean Sheet)")
    
    # 5. High over markets
    if predictions['over_3_5'] < 25:
        reason = f"Only {predictions['over_3_5']}% probability | Low scoring teams"
        recommendations["avoid_bets"].append("Over 3.5 Goals")
    
    if predictions['over_4_5'] < 10:
        recommendations["avoid_bets"].append("Over 4.5 Goals")
    
    # Add insights
    if home_metrics['avg_gf'] > away_metrics['avg_gf']:
        recommendations["insights"].append(f"{home_team} has better attack ({home_metrics['avg_gf']} vs {away_metrics['avg_gf']} GF/game)")
    else:
        recommendations["insights"].append(f"{away_team} has better attack ({away_metrics['avg_gf']} vs {home_metrics['avg_gf']} GF/game)")
    
    if away_metrics['avg_ga'] < home_metrics['avg_ga']:
        recommendations["insights"].append(f"{away_team} has better defense ({away_metrics['avg_ga']} vs {home_metrics['avg_ga']} GA/game)")
    else:
        recommendations["insights"].append(f"{home_team} has better defense ({home_metrics['avg_ga']} vs {away_metrics['avg_ga']} GA/game)")
    
    if h2h_stats and h2h_stats['total_matches'] > 0:
        if h2h_stats['home_wins'] == 0 and h2h_stats['away_wins'] == 0:
            recommendations["insights"].append(f"Historical trend: {h2h_stats['draws']}/{h2h_stats['total_matches']} matches ended in draw")
        elif h2h_stats['home_wins'] > h2h_stats['away_wins'] * 2:
            recommendations["insights"].append(f"Strong historical advantage for {home_team}")
        elif h2h_stats['away_wins'] > h2h_stats['home_wins'] * 2:
            recommendations["insights"].append(f"Strong historical advantage for {away_team}")
    
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

# ============ MAIN DASHBOARD LAYOUT ============

# Top section: Data Input
st.header("📥 Data Input & Processing")
col1, col2 = st.columns([2, 1])

with col1:
    raw_input = st.text_area(
        "**Paste match data** (with dates/times - will be cleaned automatically)", 
        height=150,
        placeholder="Paste your messy data here, e.g.:\nAston V\n1\n2\nSheffield U\nEnglish League WEEK 17 - #2025122312\n3:58 pm\nSouthampton\n2\n0\nEverton\n..."
    )
    
    parse_clicked = st.button("🚀 Parse and Add Matches", type="primary", use_container_width=True)

with col2:
    st.markdown("### 🛠️ Quick Actions")
    
    # Season info
    max_matches = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS]) if st.session_state.team_stats else 0
    st.metric("📅 Current Season", f"Season {st.session_state.season_number}", 
              f"{max_matches}/38 matches")
    
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("🔄 Manual Reset", help="Reset stats for new season", use_container_width=True):
            reset_league_for_new_season()
            st.rerun()
    
    with action_col2:
        if st.button("🗑️ Clear All", help="Clear all match data", use_container_width=True):
            st.session_state.match_data = []
            reset_league_for_new_season()
            st.rerun()

# Process input data
if parse_clicked and raw_input.strip():
    new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)
    
    if errors:
        st.error(f"❌ Found {len(errors)} parsing errors")
        for error in errors[:3]:  # Show first 3 errors
            st.write(f"- {error}")
        if len(errors) > 3:
            st.write(f"- ... and {len(errors) - 3} more errors")
    
    if new_matches:
        # Check if we need to reset season before adding new matches
        needs_reset = False
        for home_team, home_score, away_score, away_team in new_matches:
            if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                needs_reset = True
                break
        
        if needs_reset:
            check_and_reset_season()
        
        # Process each match
        processed_count = 0
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
            
            # Update counters
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
            
            # Add match data with season info - EXACTLY AS IN CSV
            st.session_state.match_data.append([
                match_id, home_team, home_score, away_score, away_team,
                total_goals, total_g_display, result,
                home_score - away_score,
                "Yes" if home_score > 0 and away_score > 0 else "No",
                "Over 2.5" if total_goals > 2.5 else "Under 2.5",
                home_rank, away_rank,
                st.session_state.home_counters[home_team],
                st.session_state.away_counters[away_team],
                st.session_state.ha_counters[home_team],
                st.session_state.ha_counters[away_team],
                st.session_state.status3_counters[home_team],
                st.session_state.status3_counters[away_team],
                f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}",
                f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}",
                st.session_state.season_number,  # Season number
                f"Season {st.session_state.season_number}"  # Season label
            ])
            
            processed_count += 1
        
        st.success(f"✅ Added {processed_count} matches to Season {st.session_state.season_number}")
        st.rerun()
    else:
        st.warning("⚠️ No valid matches found in the input")

# ============ MAIN DASHBOARD SECTIONS ============
if len(st.session_state.match_data) > 0:
    column_names = [
        "Match_ID", "Home_Team", "Home_Score", "Away_Score", "Away_Team",
        "Total_Goals", "Total-G", "Match_Result", "Goal_Difference", 
        "Both_Teams_Scored", "Over_Under", "Home_Rank", "Away_Rank",
        "Games_Since_Last_Won_Home", "Games_Since_Last_Won_Away",
        "Games_Since_Last_Won_Combined_Home", "Games_Since_Last_Won_Combined_Away",
        "Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away",
        "F!=4HA", "Status3", "Season_Number", "Season_Label"
    ]
    
    df = pd.DataFrame(st.session_state.match_data, columns=column_names)
    
    st.markdown("---")
    st.header(f"📊 Season {st.session_state.season_number} Dashboard")
    
    # Three columns layout
    col_league, col_recent = st.columns([1.5, 1])
    
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
        
        st.dataframe(league_df, use_container_width=True, height=500)
        
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
        
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)
        
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
        
        # ============ STATUS3 OUTPUT - EXACTLY AS IN CSV ============
        st.subheader("📊 Status3 Summary")
        
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)
        
        # Get all matches for Status3 display
        all_matches = st.session_state.match_data if len(st.session_state.match_data) > 0 else []
        
        # Display Status3 data EXACTLY as stored in column 21 (index 20)
        for match in all_matches:
            if len(match) > 20:  # Check if Status3 data exists at index 20
                status3_string = match[20]  # This is the F!=4HA column
                st.markdown(
                    f"<div style='font-size:14px; margin-bottom:5px;'>{status3_string}</div>", 
                    unsafe_allow_html=True
                )
        
        # Also show the actual Status3 column (index 21)
        st.markdown("<hr style='border-color:#
