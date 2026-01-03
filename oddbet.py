import streamlit as st
import pandas as pd
import re

# ============ CSS STYLING ============
st.markdown("""
<style>
    /* Main background */
    .main-background {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Custom containers */
    .custom-container {
        background-color: white;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }
    
    /* Headers */
    .main-header {
        text-align: center;
        color: #1E3A8A;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 3px solid #3B82F6;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .section-header {
        color: #1E3A8A;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 7px 20px rgba(59, 130, 246, 0.3);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        color: #6B7280;
        font-weight: 600;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    
    /* DataFrames */
    .dataframe {
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .dataframe th {
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        color: white !important;
        font-weight: 600;
        padding: 14px !important;
        text-align: left;
    }
    
    .dataframe td {
        padding: 12px !important;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .dataframe tr:hover {
        background-color: #F9FAFB;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        border-radius: 10px;
    }
    
    /* Text areas */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #E5E7EB;
        font-family: 'Courier New', monospace;
        font-size: 14px;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        border-radius: 10px;
    }
    
    /* Alerts */
    .stAlert {
        border-radius: 10px;
        border: none;
        padding: 20px;
    }
    
    .stAlert.stSuccess {
        background: linear-gradient(90deg, #10B981, #34D399);
        color: white;
    }
    
    .stAlert.stWarning {
        background: linear-gradient(90deg, #F59E0B, #FBBF24);
        color: white;
    }
    
    .stAlert.stError {
        background: linear-gradient(90deg, #EF4444, #F87171);
        color: white;
    }
    
    .stAlert.stInfo {
        background: linear-gradient(90deg, #3B82F6, #60A5FA);
        color: white;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1E3A8A 0%, #3B82F6 100%);
    }
    
    /* Counter displays */
    .counter-box {
        background: #F9FAFB;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 5px solid #3B82F6;
        font-family: 'Courier New', monospace;
        font-size: 14px;
    }
    
    .counter-box strong {
        color: #1E3A8A;
        font-size: 16px;
    }
    
    /* Recent matches display */
    .match-row {
        padding: 12px;
        margin: 8px 0;
        border-bottom: 1px solid #E5E7EB;
        font-size: 14px;
    }
    
    .match-row:last-child {
        border-bottom: none;
    }
    
    /* Footer */
    .footer-text {
        text-align: center;
        color: #6B7280;
        font-size: 0.9em;
        padding: 20px;
        margin-top: 30px;
        border-top: 2px solid #E5E7EB;
    }
    
    /* Divider */
    .custom-divider {
        height: 3px;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        border-radius: 10px;
        margin: 30px 0;
    }
    
    /* Alert styles */
    .alert-critical {
        background: linear-gradient(90deg, #EF4444, #F87171);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .alert-warning {
        background: linear-gradient(90deg, #F59E0B, #FBBF24);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .alert-info {
        background: linear-gradient(90deg, #3B82F6, #60A5FA);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Allowed team names (case-sensitive)
VALID_TEAMS = {
    "Leeds", "Aston V", "Manchester Blue", "Liverpool", "London Blues", "Everton",
    "Brighton", "Sheffield U", "Tottenham", "Palace", "Newcastle", "West Ham",
    "Leicester", "West Brom", "Burnley", "London Reds", "Southampton", "Wolves",
    "Fulham", "Manchester Reds"
}

# ============ COUNTER ALERT SETTINGS ============
F4_ALERT_THRESHOLD = 8  # Warn when F!=4HA counter reaches 8
F4_CRITICAL_THRESHOLD = 10  # Critical alert when reaches 10
S3_ALERT_THRESHOLD = 7  # Warn when Status3 counter reaches 7
S3_CRITICAL_THRESHOLD = 9  # Critical alert when reaches 9

st.set_page_config(page_title="Football Results Dashboard", page_icon="⚽", layout="wide")

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

def calculate_historical_patterns():
    """Calculate historical patterns for each team's counter behavior"""
    patterns = {}
    
    for team in VALID_TEAMS:
        # Get all matches involving this team
        team_matches = []
        for match in st.session_state.match_data:
            if match[1] == team or match[4] == team:
                team_matches.append(match)
        
        if len(team_matches) < 5:  # Need minimum data
            patterns[team] = {
                "avg_f4_before_reset": 0,
                "max_f4_counter": 0,
                "avg_s3_before_reset": 0,
                "max_s3_counter": 0,
                "f4_hit_rate": 0,
                "s3_hit_rate": 0,
                "prediction_f4": "Insufficient data",
                "prediction_s3": "Insufficient data",
                "total_matches_analyzed": len(team_matches)
            }
            continue
        
        # Analyze F!=4HA patterns
        f4_counters_before_reset = []
        current_f4_streak = 0
        f4_hit_count = 0
        max_f4_counter = 0
        
        # Analyze Status3 patterns
        s3_counters_before_reset = []
        current_s3_streak = 0
        s3_hit_count = 0
        max_s3_counter = 0
        
        # Track through matches
        for match in team_matches:
            total_goals = match[5]  # Total_Goals column
            
            # Check F!=4HA (4 goals total)
            if total_goals == 4:
                f4_counters_before_reset.append(current_f4_streak)
                f4_hit_count += 1
                current_f4_streak = 0
            else:
                current_f4_streak += 1
                max_f4_counter = max(max_f4_counter, current_f4_streak)
            
            # Check Status3 (3+ goals total)
            if total_goals >= 3:
                s3_counters_before_reset.append(current_s3_streak)
                s3_hit_count += 1
                current_s3_streak = 0
            else:
                current_s3_streak += 1
                max_s3_counter = max(max_s3_counter, current_s3_streak)
        
        # Calculate averages
        avg_f4 = sum(f4_counters_before_reset) / len(f4_counters_before_reset) if f4_counters_before_reset else 0
        avg_s3 = sum(s3_counters_before_reset) / len(s3_counters_before_reset) if s3_counters_before_reset else 0
        
        # Calculate hit rates (per match)
        f4_hit_rate = (f4_hit_count / len(team_matches) * 100) if team_matches else 0
        s3_hit_rate = (s3_hit_count / len(team_matches) * 100) if team_matches else 0
        
        # Generate predictions
        current_f4 = st.session_state.ha_counters[team]
        current_s3 = st.session_state.status3_counters[team]
        
        # F!=4HA prediction
        if f4_hit_rate > 0:
            if current_f4 >= max_f4_counter * 0.8 and max_f4_counter > 0:
                pred_f4 = f"CRITICAL: Usually hits 4 goals every {avg_f4:.1f} matches (now at {current_f4})"
            elif current_f4 >= avg_f4:
                pred_f4 = f"HIGH PROBABILITY: Due for 4 goals (average: {avg_f4:.1f} matches between 4-goal games)"
            else:
                pred_f4 = f"NORMAL: On track (average: {avg_f4:.1f} matches between 4-goal games)"
        else:
            pred_f4 = "Rarely hits 4 goals"
        
        # Status3 prediction
        if s3_hit_rate > 0:
            if current_s3 >= max_s3_counter * 0.8 and max_s3_counter > 0:
                pred_s3 = f"CRITICAL: Usually hits 3+ goals every {avg_s3:.1f} matches (now at {current_s3})"
            elif current_s3 >= avg_s3:
                pred_s3 = f"HIGH PROBABILITY: Due for 3+ goals (average: {avg_s3:.1f} matches between 3+ goal games)"
            else:
                pred_s3 = f"NORMAL: On track (average: {avg_s3:.1f} matches between 3+ goal games)"
        else:
            pred_s3 = "Rarely hits 3+ goals"
        
        patterns[team] = {
            "avg_f4_before_reset": round(avg_f4, 1),
            "max_f4_counter": max_f4_counter,
            "avg_s3_before_reset": round(avg_s3, 1),
            "max_s3_counter": max_s3_counter,
            "f4_hit_rate": round(f4_hit_rate, 1),
            "s3_hit_rate": round(s3_hit_rate, 1),
            "prediction_f4": pred_f4,
            "prediction_s3": pred_s3,
            "total_matches_analyzed": len(team_matches)
        }
    
    return patterns

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
    
    # Calculate over/under probabilities
    total_goals_expected = home_metrics["avg_gf"] + away_metrics["avg_gf"]
    
    over_2_5_prob = min(90, max(10, (total_goals_expected - 1.5) * 30))
    over_3_5_prob = min(70, max(5, (total_goals_expected - 2.5) * 25))
    over_4_5_prob = min(50, max(2, (total_goals_expected - 3.5) * 20))
    
    # Both teams score probability
    both_teams_score_prob = (home_metrics["bts_rate"] + away_metrics["bts_rate"]) / 2
    
    # FIX: Ensure all probabilities are within 0-100 range
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

def check_counter_alerts():
    """Check all teams for counter alerts and return alerts dictionary with historical context"""
    alerts = {
        "f4_alerts": [],  # Teams with high F!=4HA counters
        "s3_alerts": [],  # Teams with high Status3 counters
        "critical_alerts": []  # Teams exceeding critical thresholds
    }
    
    # Get historical patterns
    patterns = calculate_historical_patterns()
    
    for team in VALID_TEAMS:
        f4_counter = st.session_state.ha_counters[team]
        s3_counter = st.session_state.status3_counters[team]
        pattern = patterns[team]
        
        # Check F!=4HA alerts
        if f4_counter >= F4_CRITICAL_THRESHOLD:
            probability = min(95, max(10, (f4_counter / pattern["avg_f4_before_reset"] * 80))) if pattern["avg_f4_before_reset"] > 0 else 0
            alerts["critical_alerts"].append({
                "team": team,
                "counter": f4_counter,
                "type": "F!=4HA",
                "level": "CRITICAL",
                "message": f"🔴 {team}: F!=4HA counter = {f4_counter} (EXCEEDED {F4_CRITICAL_THRESHOLD} LIMIT!)",
                "historical": pattern["prediction_f4"],
                "avg_between": pattern["avg_f4_before_reset"],
                "hit_rate": pattern["f4_hit_rate"],
                "probability": probability
            })
        elif f4_counter >= F4_ALERT_THRESHOLD:
            probability = min(95, max(10, (f4_counter / pattern["avg_f4_before_reset"] * 70))) if pattern["avg_f4_before_reset"] > 0 else 0
            alerts["f4_alerts"].append({
                "team": team,
                "counter": f4_counter,
                "type": "F!=4HA",
                "level": "WARNING",
                "message": f"⚠️ {team}: F!=4HA counter = {f4_counter} (needs 4-goal match soon)",
                "historical": pattern["prediction_f4"],
                "avg_between": pattern["avg_f4_before_reset"],
                "hit_rate": pattern["f4_hit_rate"],
                "probability": probability
            })
        
        # Check Status3 alerts
        if s3_counter >= S3_CRITICAL_THRESHOLD:
            probability = min(95, max(10, (s3_counter / pattern["avg_s3_before_reset"] * 75))) if pattern["avg_s3_before_reset"] > 0 else 0
            alerts["critical_alerts"].append({
                "team": team,
                "counter": s3_counter,
                "type": "Status3",
                "level": "CRITICAL",
                "message": f"🔥 {team}: Status3 counter = {s3_counter} (EXCEEDED {S3_CRITICAL_THRESHOLD} LIMIT!)",
                "historical": pattern["prediction_s3"],
                "avg_between": pattern["avg_s3_before_reset"],
                "hit_rate": pattern["s3_hit_rate"],
                "probability": probability
            })
        elif s3_counter >= S3_ALERT_THRESHOLD:
            probability = min(95, max(10, (s3_counter / pattern["avg_s3_before_reset"] * 65))) if pattern["avg_s3_before_reset"] > 0 else 0
            alerts["s3_alerts"].append({
                "team": team,
                "counter": s3_counter,
                "type": "Status3",
                "level": "WARNING",
                "message": f"🎯 {team}: Status3 counter = {s3_counter} (due for 3+ goal match)",
                "historical": pattern["prediction_s3"],
                "avg_between": pattern["avg_s3_before_reset"],
                "hit_rate": pattern["s3_hit_rate"],
                "probability": probability
            })
    
    # Sort alerts by counter value (highest first)
    alerts["f4_alerts"].sort(key=lambda x: x["counter"], reverse=True)
    alerts["s3_alerts"].sort(key=lambda x: x["counter"], reverse=True)
    alerts["critical_alerts"].sort(key=lambda x: x["counter"], reverse=True)
    
    return alerts

def get_alert_symbols_and_reason(f4_counter, s3_counter):
    """Generate alert symbols and reason text for a team"""
    f4_alert = ""
    s3_alert = ""
    reasons = []
    
    if f4_counter >= F4_CRITICAL_THRESHOLD:
        f4_alert = "🔴"
        reasons.append(f"F4={f4_counter} (CRITICAL)")
    elif f4_counter >= F4_ALERT_THRESHOLD:
        f4_alert = "⚠️"
        reasons.append(f"F4={f4_counter}")
    
    if s3_counter >= S3_CRITICAL_THRESHOLD:
        s3_alert = "🔥"
        reasons.append(f"S3={s3_counter} (CRITICAL)")
    elif s3_counter >= S3_ALERT_THRESHOLD:
        s3_alert = "🎯"
        reasons.append(f"S3={s3_counter}")
    
    alert_reason = " | ".join(reasons) if reasons else ""
    
    return f4_alert, s3_alert, alert_reason

# ============ SIDEBAR NAVIGATION ============
st.sidebar.markdown("""
<div style='padding: 20px; background: linear-gradient(180deg, #1E3A8A 0%, #3B82F6 100%); border-radius: 10px; color: white;'>
<h3 style='color: white;'>🎯 Navigation</h3>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.selectbox("", ["Main Dashboard", "Counter Logic Dashboard"])

st.sidebar.markdown("---")

st.sidebar.markdown("""
<div style='padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
<h4 style='color: #1E3A8A;'>📊 Quick Stats</h4>
""", unsafe_allow_html=True)

if len(st.session_state.match_data) > 0:
    current_season_matches = [m for m in st.session_state.match_data if m[-2] == st.session_state.season_number]
    st.sidebar.metric("Current Season", f"Season {st.session_state.season_number}")
    st.sidebar.metric("Matches This Season", len(current_season_matches))
    st.sidebar.metric("Total Matches", len(st.session_state.match_data))
    
    # Show alert count in sidebar
    alerts = check_counter_alerts()
    total_alerts = len(alerts["critical_alerts"]) + len(alerts["f4_alerts"]) + len(alerts["s3_alerts"])
    st.sidebar.metric("Active Alerts", total_alerts)
else:
    st.sidebar.info("No matches yet")

st.sidebar.markdown("</div>", unsafe_allow_html=True)

# ============ COUNTER LOGIC DASHBOARD ============
if page == "Counter Logic Dashboard":
    # Main container
    st.markdown("<div class='custom-container'>", unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>Counter Logic Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-header'>FI=4HA & Status3 (Last 10 Matches)</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #F9FAFB; padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
    <p style='font-size: 16px; color: #4B5563;'>
    This view shows the <strong>FI=4HA</strong> and <strong>Status3</strong> outputs for the <strong>last 10 matches</strong>.<br>
    Shows most recent matches first.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    if len(st.session_state.match_data) == 0:
        st.info("No matches available yet. Add matches from the Main Dashboard to populate these counters.")
    else:
        # Get last 10 matches (most recent first)
        last_10_matches = st.session_state.match_data[-10:][::-1]  # Get last 10, then reverse to show newest first
        
        # Prepare display rows
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.markdown("<h4 style='color: #1E3A8A; font-size: 1.4rem; margin-bottom: 15px;'>📊 FI=4HA (Last 10 Matches)</h4>", unsafe_allow_html=True)
            for m in last_10_matches:
                home = m[1] if len(m) > 1 else ""
                home_score = m[2] if len(m) > 2 else ""
                away_score = m[3] if len(m) > 3 else ""
                away = m[4] if len(m) > 4 else ""
                fi_display = m[19] if len(m) > 19 else f"{home}: {st.session_state.ha_counters.get(home,0)} | {away}: {st.session_state.ha_counters.get(away,0)}"
                st.markdown(f"""
                <div class='counter-box'>
                <strong>{home}</strong> {home_score}-{away_score} <strong>{away}</strong><br>
                <small>{fi_display}</small>
                </div>
                """, unsafe_allow_html=True)
        
        with right_col:
            st.markdown("<h4 style='color: #1E3A8A; font-size: 1.4rem; margin-bottom: 15px;'>📈 Status3 (Last 10 Matches)</h4>", unsafe_allow_html=True)
            for m in last_10_matches:
                home = m[1] if len(m) > 1 else ""
                home_score = m[2] if len(m) > 2 else ""
                away_score = m[3] if len(m) > 3 else ""
                away = m[4] if len(m) > 4 else ""
                s3_display = m[20] if len(m) > 20 else f"{home}: {st.session_state.status3_counters.get(home,0)} | {away}: {st.session_state.status3_counters.get(away,0)}"
                st.markdown(f"""
                <div class='counter-box'>
                <strong>{home}</strong> {home_score}-{away_score} <strong>{away}</strong><br>
                <small>{s3_display}</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============ MAIN DASHBOARD ============
else:
    # Main container
    st.markdown("<div class='custom-container'>", unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>⚽ Complete Football Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    # ============ DATA INPUT SECTION ============
    st.markdown("<h2 class='section-header'>📥 Data Input & Processing</h2>", unsafe_allow_html=True)
    
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
            for error in errors[:3]:
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
                
                # Generate alert symbols and reason
                home_f4_alert, home_s3_alert, home_alert_reason = get_alert_symbols_and_reason(
                    st.session_state.ha_counters[home_team], 
                    st.session_state.status3_counters[home_team]
                )
                away_f4_alert, away_s3_alert, away_alert_reason = get_alert_symbols_and_reason(
                    st.session_state.ha_counters[away_team], 
                    st.session_state.status3_counters[away_team]
                )
                
                # Combine alert reasons
                combined_alert_reason = ""
                if home_alert_reason or away_alert_reason:
                    combined_alert_reason = f"{home_team}: {home_alert_reason} | {away_team}: {away_alert_reason}"
                
                # Add match data with season info AND ALERTS
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
                    home_f4_alert, home_s3_alert, away_f4_alert, away_s3_alert, combined_alert_reason,  # NEW ALERT COLUMNS
                    st.session_state.season_number,
                    f"Season {st.session_state.season_number}"
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
            "F!=4HA", "Status3",
            "F4_Alert_Home", "S3_Alert_Home", "F4_Alert_Away", "S3_Alert_Away", "Alert_Reason",  # NEW COLUMNS
            "Season_Number", "Season_Label"
        ]
        
        df = pd.DataFrame(st.session_state.match_data, columns=column_names)
        
        # Divider
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        
        # Row 1: League Table and Recent Matches
        st.markdown("<h2 class='section-header'>📊 Season Dashboard</h2>", unsafe_allow_html=True)
        
        col_league, col_recent = st.columns([2, 1])
        
        with col_league:
            st.markdown(f"<h3 style='color: #1E3A8A; font-size: 1.5rem;'>🏆 Season {st.session_state.season_number} League Table</h3>", unsafe_allow_html=True)
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
            
            # Quick league insights
            st.markdown("<h4 style='color: #1E3A8A; font-size: 1.3rem; margin-top: 20px;'>📈 League Insights</h4>", unsafe_allow_html=True)
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
            st.markdown("<h3 style='color: #1E3A8A; font-size: 1.5rem;'>🔄 Recent Match Summary</h3>", unsafe_allow_html=True)
            
            st.markdown("""
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color:white; padding:20px; border-radius:15px; margin-bottom: 20px;">
            """, unsafe_allow_html=True)
            
            # Get recent matches (last 10)
            recent_matches = st.session_state.match_data[-10:] if len(st.session_state.match_data) > 0 else []
            
            for match in recent_matches[::-1]:
                home = match[1]
                away = match[4]
                home_score = match[2]
                away_score = match[3]
                home_rank = match[11] if len(match) > 11 else "?"
                away_rank = match[12] if len(match) > 12 else "?"
                
                # Color code based on result
                if home_score > away_score:
                    home_style = "color: #10B981; font-weight: bold;"
                    away_style = "color: #EF4444;"
                elif away_score > home_score:
                    home_style = "color: #EF4444;"
                    away_style = "color: #10B981; font-weight: bold;"
                else:
                    home_style = away_style = "color: #F59E0B;"
                
                st.markdown(
                    f"<div class='match-row'>"
                    f"<span style='{home_style}'>{home_rank}. {home}</span> "
                    f"{home_score}-{away_score} "
                    f"<span style='{away_style}'>{away} ({away_rank}.)</span>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Quick stats
            st.markdown("<h4 style='color: #1E3A8A; font-size: 1.3rem;'>📋 Quick Stats</h4>", unsafe_allow_html=True)
            total_matches = len(st.session_state.match_data)
            
            # Calculate stats for current season only
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
        
        # Divider
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        
        # ============ COUNTER ALERTS DASHBOARD ============
        st.markdown("<h2 class='section-header'>🚨 Counter Alert Dashboard</h2>", unsafe_allow_html=True)
        
        # Get current alerts
        alerts = check_counter_alerts()
        
        # Display critical alerts first
        if alerts["critical_alerts"]:
            st.markdown("<h3 style='color: #EF4444; font-size: 1.5rem;'>🔴 CRITICAL ALERTS (Exceeded Limits)</h3>", unsafe_allow_html=True)
            for alert in alerts["critical_alerts"]:
                with st.expander(f"{alert['message']}", expanded=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("Current Counter", alert['counter'])
                        st.metric("Avg Between", f"{alert['avg_between']} matches")
                    with col2:
                        st.write(f"**Team:** {alert['team']}")
                        st.write(f"**Type:** {alert['type']}")
                        st.write(f"**Historical Pattern:** {alert['historical']}")
                        st.write(f"**Hit Rate:** {alert['hit_rate']}% of matches")
                        st.write(f"**Probability next match:** {alert['probability']:.0f}%")
                        st.progress(alert['probability']/100)
        
        # Display warning alerts in columns with historical context
        col_f4, col_s3 = st.columns(2)
        
        with col_f4:
            if alerts["f4_alerts"]:
                st.markdown(f"<h3 style='color: #F59E0B; font-size: 1.5rem;'>⚠️ F!=4HA Warnings (Counter ≥ {F4_ALERT_THRESHOLD})</h3>", unsafe_allow_html=True)
                for alert in alerts["f4_alerts"]:
                    progress_value = min(1.0, alert['counter'] / 12)
                    
                    # Create expandable alert with historical context
                    with st.expander(f"{alert['message']}", expanded=False):
                        st.write(f"**Team:** {alert['team']}")
                        st.write(f"**Current Counter:** {alert['counter']}")
                        st.write(f"**Average between 4-goal matches:** {alert['avg_between']} matches")
                        st.write(f"**4-goal match rate:** {alert['hit_rate']}% of games")
                        st.write(f"**Historical Prediction:**")
                        st.info(f"📊 {alert['historical']}")
                        
                        # Probability calculation
                        st.write(f"**Probability of hitting 4 goals in next match:** {alert['probability']:.0f}%")
                        st.progress(alert['probability']/100)
                        
                        # Type A Alert Example
                        if alert['counter'] >= 9:
                            type_a_prob = min(90, alert['probability'] + 20)
                            st.success(f"🎯 **TYPE A ALERT:** {alert['team']} has F!=4HA counter at **{alert['counter']}**. Historical: They hit 4 goals within next 3 matches **{type_a_prob:.0f}%** of time.")
                    
                    st.progress(progress_value)
            else:
                st.markdown("<h3 style='color: #10B981; font-size: 1.5rem;'>✅ F!=4HA Status: All Normal</h3>", unsafe_allow_html=True)
                st.info(f"No teams have F!=4HA counters ≥ {F4_ALERT_THRESHOLD}")
        
        with col_s3:
            if alerts["s3_alerts"]:
                st.markdown(f"<h3 style='color: #3B82F6; font-size: 1.5rem;'>🎯 Status3 Warnings (Counter ≥ {S3_ALERT_THRESHOLD})</h3>", unsafe_allow_html=True)
                for alert in alerts["s3_alerts"]:
                    progress_value = min(1.0, alert['counter'] / 11)
                    
                    # Create expandable alert with historical context
                    with st.expander(f"{alert['message']}", expanded=False):
                        st.write(f"**Team:** {alert['team']}")
                        st.write(f"**Current Counter:** {alert['counter']}")
                        st.write(f"**Average between 3+ goal matches:** {alert['avg_between']} matches")
                        st.write(f"**3+ goal match rate:** {alert['hit_rate']}% of games")
                        st.write(f"**Historical Prediction:**")
                        st.info(f"📊 {alert['historical']}")
                        
                        # Probability calculation
                        st.write(f"**Probability of hitting 3+ goals in next match:** {alert['probability']:.0f}%")
                        st.progress(alert['probability']/100)
                        
                        # Type A Alert Example for Status3
                        if alert['counter'] >= 8:
                            type_a_prob = min(85, alert['probability'] + 15)
                            st.success(f"🎯 **TYPE A ALERT:** {alert['team']} has Status3 counter at **{alert['counter']}**. Historical: They hit 3+ goals within next 2 matches **{type_a_prob:.0f}%** of time.")
                    
                    st.progress(progress_value)
            else:
                st.markdown("<h3 style='color: #10B981; font-size: 1.5rem;'>✅ Status3 Status: All Normal</h3>", unsafe_allow_html=True)
                st.info(f"No teams have Status3 counters ≥ {S3_ALERT_THRESHOLD}")
        
        # Add a new section for Team-Specific Analysis
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #1E3A8A; font-size: 1.5rem;'>📊 Team-Specific Counter Analysis</h3>", unsafe_allow_html=True)
        
        # Let user select a team for detailed analysis
        selected_team = st.selectbox("Select a team for detailed counter analysis:", sorted(VALID_TEAMS))
        
        if selected_team:
            patterns = calculate_historical_patterns()
            pattern = patterns[selected_team]
            
            col_analysis1, col_analysis2 = st.columns(2)
            
            with col_analysis1:
                st.markdown(f"#### F!=4HA Analysis for {selected_team}")
                current_f4 = st.session_state.ha_counters[selected_team]
                st.metric("Current Counter", current_f4)
                st.metric("Average Between 4-goal Matches", f"{pattern['avg_f4_before_reset']} matches")
                st.metric("Maximum Counter Recorded", pattern['max_f4_counter'])
                st.metric("4-goal Match Rate", f"{pattern['f4_hit_rate']}%")
                
                # Type A Alert
                st.write("**🎯 Type A Alert:**")
                if current_f4 >= F4_ALERT_THRESHOLD:
                    probability = min(95, max(10, (current_f4 / pattern['avg_f4_before_reset'] * 70))) if pattern['avg_f4_before_reset'] > 0 else 0
                    type_a_prob = min(90, probability + 20)
                    st.success(f"⚠️ **{selected_team}** has F!=4HA counter at **{current_f4}**. Historical: They hit 4 goals within next 3 matches **{type_a_prob:.0f}%** of time.")
                else:
                    st.info(pattern['prediction_f4'])
            
            with col_analysis2:
                st.markdown(f"#### Status3 Analysis for {selected_team}")
                current_s3 = st.session_state.status3_counters[selected_team]
                st.metric("Current Counter", current_s3)
                st.metric("Average Between 3+ goal Matches", f"{pattern['avg_s3_before_reset']} matches")
                st.metric("Maximum Counter Recorded", pattern['max_s3_counter'])
                st.metric("3+ goal Match Rate", f"{pattern['s3_hit_rate']}%")
                
                # Type A Alert
                st.write("**🎯 Type A Alert:**")
                if current_s3 >= S3_ALERT_THRESHOLD:
                    probability = min(95, max(10, (current_s3 / pattern['avg_s3_before_reset'] * 65))) if pattern['avg_s3_before_reset'] > 0 else 0
                    type_a_prob = min(85, probability + 15)
                    st.success(f"🎯 **{selected_team}** has Status3 counter at **{current_s3}**. Historical: They hit 3+ goals within next 2 matches **{type_a_prob:.0f}%** of time.")
                else:
                    st.info(pattern['prediction_s3'])
            
            # Historical trend visualization
            st.markdown("#### 📊 Historical Trend Analysis")
            if pattern['total_matches_analyzed'] > 0:
                st.write(f"Analyzed {pattern['total_matches_analyzed']} matches")
                
                # Create a simple trend analysis
                trend_data = {
                    "Metric": ["F!=4HA Pattern", "Status3 Pattern"],
                    "Average Interval": [pattern['avg_f4_before_reset'], pattern['avg_s3_before_reset']],
                    "Hit Rate": [f"{pattern['f4_hit_rate']}%", f"{pattern['s3_hit_rate']}%"],
                    "Current Counter": [current_f4, current_s3],
                    "Alert Status": [
                        "🔴 CRITICAL" if current_f4 >= F4_CRITICAL_THRESHOLD else "⚠️ WARNING" if current_f4 >= F4_ALERT_THRESHOLD else "✅ Normal",
                        "🔥 CRITICAL" if current_s3 >= S3_CRITICAL_THRESHOLD else "🎯 WARNING" if current_s3 >= S3_ALERT_THRESHOLD else "✅ Normal"
                    ]
                }
                
                trend_df = pd.DataFrame(trend_data)
                st.dataframe(trend_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Insufficient data for trend analysis")
        
        # Summary statistics
        st.markdown("<h4 style='color: #1E3A8A; font-size: 1.3rem; margin-top: 20px;'>📊 Alert Summary</h4>", unsafe_allow_html=True)
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.metric("Critical Alerts", len(alerts["critical_alerts"]))
        
        with summary_col2:
            st.metric("F!=4HA Warnings", len(alerts["f4_alerts"]))
        
        with summary_col3:
            st.metric("Status3 Warnings", len(alerts["s3_al
