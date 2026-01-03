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
    
    /* Type A Alert Boxes */
    .type-a-alert {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #FF8C00;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .type-a-alert-critical {
        background: linear-gradient(135deg, #FF0000 0%, #DC143C 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #8B0000;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .type-a-alert-status3 {
        background: linear-gradient(135deg, #4169E1 0%, #1E90FF 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #000080;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
    
    /* Divider */
    .custom-divider {
        height: 3px;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        border-radius: 10px;
        margin: 30px 0;
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
    st.session_state.team_stats = {
        team: {
            "P": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0, "Form": []
        }
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
        
        bts_matches = 0
        for match in st.session_state.match_data:
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
        team_matches = []
        for match in st.session_state.match_data:
            if match[1] == team or match[4] == team:
                team_matches.append(match)
        
        if len(team_matches) < 3:
            patterns[team] = {
                "avg_f4_before_reset": 0,
                "max_f4_counter": 0,
                "avg_s3_before_reset": 0,
                "max_s3_counter": 0,
                "f4_hit_rate": 0,
                "s3_hit_rate": 0,
                "total_matches": len(team_matches)
            }
            continue
        
        f4_counters_before_reset = []
        current_f4_streak = 0
        f4_hit_count = 0
        max_f4_counter = 0
        
        s3_counters_before_reset = []
        current_s3_streak = 0
        s3_hit_count = 0
        max_s3_counter = 0
        
        for match in team_matches:
            total_goals = match[5]
            
            if total_goals == 4:
                f4_counters_before_reset.append(current_f4_streak)
                f4_hit_count += 1
                current_f4_streak = 0
            else:
                current_f4_streak += 1
                max_f4_counter = max(max_f4_counter, current_f4_streak)
            
            if total_goals >= 3:
                s3_counters_before_reset.append(current_s3_streak)
                s3_hit_count += 1
                current_s3_streak = 0
            else:
                current_s3_streak += 1
                max_s3_counter = max(max_s3_counter, current_s3_streak)
        
        avg_f4 = sum(f4_counters_before_reset) / len(f4_counters_before_reset) if f4_counters_before_reset else 0
        avg_s3 = sum(s3_counters_before_reset) / len(s3_counters_before_reset) if s3_counters_before_reset else 0
        
        f4_hit_rate = (f4_hit_count / len(team_matches) * 100) if team_matches else 0
        s3_hit_rate = (s3_hit_count / len(team_matches) * 100) if team_matches else 0
        
        patterns[team] = {
            "avg_f4_before_reset": round(avg_f4, 1),
            "max_f4_counter": max_f4_counter,
            "avg_s3_before_reset": round(avg_s3, 1),
            "max_s3_counter": max_s3_counter,
            "f4_hit_rate": round(f4_hit_rate, 1),
            "s3_hit_rate": round(s3_hit_rate, 1),
            "total_matches": len(team_matches)
        }
    
    return patterns

def get_type_a_alerts():
    """Get Type A alerts for all teams"""
    alerts = {
        "f4_critical": [],
        "f4_warning": [],
        "s3_critical": [],
        "s3_warning": []
    }
    
    patterns = calculate_historical_patterns()
    
    for team in VALID_TEAMS:
        f4_counter = st.session_state.ha_counters[team]
        s3_counter = st.session_state.status3_counters[team]
        pattern = patterns[team]
        
        # F!=4HA Alerts
        if f4_counter >= F4_CRITICAL_THRESHOLD:
            probability = min(95, max(10, (f4_counter / pattern['avg_f4_before_reset'] * 85))) if pattern['avg_f4_before_reset'] > 0 else 90
            alerts["f4_critical"].append({
                "team": team,
                "counter": f4_counter,
                "probability": probability,
                "avg_between": pattern['avg_f4_before_reset'],
                "message": f"🔴 **{team}**: F!=4HA counter = **{f4_counter}** (EXCEEDED {F4_CRITICAL_THRESHOLD} LIMIT!) | Historical: Hits 4 goals within next match **{probability}%** of time"
            })
        elif f4_counter >= F4_ALERT_THRESHOLD:
            probability = min(90, max(15, (f4_counter / pattern['avg_f4_before_reset'] * 75))) if pattern['avg_f4_before_reset'] > 0 else 70
            alerts["f4_warning"].append({
                "team": team,
                "counter": f4_counter,
                "probability": probability,
                "avg_between": pattern['avg_f4_before_reset'],
                "message": f"⚠️ **{team}**: F!=4HA counter = **{f4_counter}** | Historical: Hits 4 goals within next 3 matches **{probability}%** of time"
            })
        
        # Status3 Alerts
        if s3_counter >= S3_CRITICAL_THRESHOLD:
            probability = min(95, max(10, (s3_counter / pattern['avg_s3_before_reset'] * 80))) if pattern['avg_s3_before_reset'] > 0 else 85
            alerts["s3_critical"].append({
                "team": team,
                "counter": s3_counter,
                "probability": probability,
                "avg_between": pattern['avg_s3_before_reset'],
                "message": f"🔥 **{team}**: Status3 counter = **{s3_counter}** (EXCEEDED {S3_CRITICAL_THRESHOLD} LIMIT!) | Historical: Hits 3+ goals within next match **{probability}%** of time"
            })
        elif s3_counter >= S3_ALERT_THRESHOLD:
            probability = min(90, max(15, (s3_counter / pattern['avg_s3_before_reset'] * 70))) if pattern['avg_s3_before_reset'] > 0 else 65
            alerts["s3_warning"].append({
                "team": team,
                "counter": s3_counter,
                "probability": probability,
                "avg_between": pattern['avg_s3_before_reset'],
                "message": f"🎯 **{team}**: Status3 counter = **{s3_counter}** | Historical: Hits 3+ goals within next 2 matches **{probability}%** of time"
            })
    
    # Sort by counter value (highest first)
    for key in alerts:
        alerts[key].sort(key=lambda x: x["counter"], reverse=True)
    
    return alerts

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

# ============ SIDEBAR ============
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
    
    # Get alert count
    alerts = get_type_a_alerts()
    total_alerts = len(alerts["f4_critical"]) + len(alerts["f4_warning"]) + len(alerts["s3_critical"]) + len(alerts["s3_warning"])
    st.sidebar.metric("Type A Alerts", total_alerts)
else:
    st.sidebar.info("No matches yet")

st.sidebar.markdown("</div>", unsafe_allow_html=True)

# ============ MAIN DASHBOARD ============
st.markdown("<div class='custom-container'>", unsafe_allow_html=True)

if page == "Counter Logic Dashboard":
    st.markdown("<h1 class='main-header'>Counter Logic Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-header'>FI=4HA & Status3 (Last 10 Matches)</h3>", unsafe_allow_html=True)
    
    if len(st.session_state.match_data) == 0:
        st.info("No matches available yet.")
    else:
        last_10_matches = st.session_state.match_data[-10:][::-1]
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.markdown("<h4 style='color: #1E3A8A;'>📊 FI=4HA (Last 10 Matches)</h4>", unsafe_allow_html=True)
            for m in last_10_matches:
                home = m[1]
                away = m[4]
                home_score = m[2]
                away_score = m[3]
                fi_display = m[19] if len(m) > 19 else ""
                st.markdown(f"**{home}** {home_score}-{away_score} **{away}**<br><small>{fi_display}</small>", unsafe_allow_html=True)
        
        with right_col:
            st.markdown("<h4 style='color: #1E3A8A;'>📈 Status3 (Last 10 Matches)</h4>", unsafe_allow_html=True)
            for m in last_10_matches:
                home = m[1]
                away = m[4]
                home_score = m[2]
                away_score = m[3]
                s3_display = m[20] if len(m) > 20 else ""
                st.markdown(f"**{home}** {home_score}-{away_score} **{away}**<br><small>{s3_display}</small>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ============ MAIN DASHBOARD LAYOUT ============
st.markdown("<h1 class='main-header'>⚽ Football Analytics Dashboard</h1>", unsafe_allow_html=True)

# 1. 📥 DATA INPUT & PROCESSING
st.markdown("<h2 class='section-header'>1. 📥 Data Input & Processing</h2>", unsafe_allow_html=True)

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
    max_matches = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS]) if st.session_state.team_stats else 0
    st.metric("📅 Current Season", f"Season {st.session_state.season_number}", f"{max_matches}/38 matches")
    
    if st.button("🔄 Manual Reset", use_container_width=True):
        reset_league_for_new_season()
        st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
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
    
    if new_matches:
        needs_reset = False
        for home_team, home_score, away_score, away_team in new_matches:
            if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                needs_reset = True
                break
        
        if needs_reset:
            check_and_reset_season()
        
        processed_count = 0
        for home_team, home_score, away_score, away_team in new_matches:
            if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                check_and_reset_season()
            
            match_id = st.session_state.match_counter
            st.session_state.match_counter += 1
            
            total_goals = home_score + away_score
            total_g_display = "Won" if total_goals == 4 else "3 ✔" if total_goals == 3 else str(total_goals)
            
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
            
            if len(st.session_state.team_stats[home_team]["Form"]) > 5:
                st.session_state.team_stats[home_team]["Form"].pop(0)
            if len(st.session_state.team_stats[away_team]["Form"]) > 5:
                st.session_state.team_stats[away_team]["Form"].pop(0)
            
            home_rank = get_team_position(home_team)
            away_rank = get_team_position(away_team)
            
            # Generate alert symbols
            home_f4_alert, home_s3_alert, home_alert_reason = get_alert_symbols_and_reason(
                st.session_state.ha_counters[home_team], 
                st.session_state.status3_counters[home_team]
            )
            away_f4_alert, away_s3_alert, away_alert_reason = get_alert_symbols_and_reason(
                st.session_state.ha_counters[away_team], 
                st.session_state.status3_counters[away_team]
            )
            
            combined_alert_reason = ""
            if home_alert_reason or away_alert_reason:
                combined_alert_reason = f"{home_team}: {home_alert_reason} | {away_team}: {away_alert_reason}"
            
            # Add match data
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
                home_f4_alert, home_s3_alert, away_f4_alert, away_s3_alert, combined_alert_reason,
                st.session_state.season_number,
                f"Season {st.session_state.season_number}"
            ])
            
            processed_count += 1
        
        st.success(f"✅ Added {processed_count} matches to Season {st.session_state.season_number}")
        st.rerun()
    else:
        st.warning("⚠️ No valid matches found in the input")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# 2. 📊 SEASON DASHBOARD (LEAGUE TABLE)
st.markdown("<h2 class='section-header'>2. 📊 Season Dashboard (League Table)</h2>", unsafe_allow_html=True)

if len(st.session_state.match_data) > 0:
    column_names = [
        "Match_ID", "Home_Team", "Home_Score", "Away_Score", "Away_Team",
        "Total_Goals", "Total-G", "Match_Result", "Goal_Difference", 
        "Both_Teams_Scored", "Over_Under", "Home_Rank", "Away_Rank",
        "Games_Since_Last_Won_Home", "Games_Since_Last_Won_Away",
        "Games_Since_Last_Won_Combined_Home", "Games_Since_Last_Won_Combined_Away",
        "Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away",
        "F!=4HA", "Status3",
        "F4_Alert_Home", "S3_Alert_Home", "F4_Alert_Away", "S3_Alert_Away", "Alert_Reason",
        "Season_Number", "Season_Label"
    ]
    
    df = pd.DataFrame(st.session_state.match_data, columns=column_names)
    
    col_league, col_recent = st.columns([2, 1])
    
    with col_league:
        st.markdown(f"<h3 style='color: #1E3A8A;'>🏆 Season {st.session_state.season_number} League Table</h3>", unsafe_allow_html=True)
        rankings = calculate_rankings()
        
        table_data = []
        for pos, (team, stats) in enumerate(rankings, 1):
            table_data.append([
                pos, team, stats["P"], stats["W"], stats["D"], stats["L"],
                stats["GF"], stats["GA"], stats["GD"], stats["Pts"], 
                " ".join(stats["Form"][-5:]) if stats["Form"] else ""
            ])
        
        league_df = pd.DataFrame(
            table_data,
            columns=["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"]
        )
        
        st.dataframe(league_df, use_container_width=True, height=400)
    
    with col_recent:
        st.markdown("<h3 style='color: #1E3A8A;'>🔄 Recent Matches</h3>", unsafe_allow_html=True)
        recent_matches = st.session_state.match_data[-5:] if len(st.session_state.match_data) > 0 else []
        
        for match in recent_matches[::-1]:
            home = match[1]
            away = match[4]
            home_score = match[2]
            away_score = match[3]
            
            if home_score > away_score:
                home_style = "color: #10B981; font-weight: bold;"
                away_style = "color: #EF4444;"
            elif away_score > home_score:
                home_style = "color: #EF4444;"
                away_style = "color: #10B981; font-weight: bold;"
            else:
                home_style = away_style = "color: #F59E0B;"
            
            st.markdown(
                f"<div style='padding: 10px; margin: 5px 0; border-bottom: 1px solid #E5E7EB;'>"
                f"<span style='{home_style}'>{home}</span> "
                f"{home_score}-{away_score} "
                f"<span style='{away_style}'>{away}</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
        
        # Quick stats
        current_season_matches = [m for m in st.session_state.match_data if m[-2] == st.session_state.season_number]
        current_df = pd.DataFrame(current_season_matches, columns=column_names) if current_season_matches else pd.DataFrame()
        
        if len(current_df) > 0:
            avg_goals = current_df["Total_Goals"].mean()
            home_wins = len(current_df[current_df["Match_Result"] == "Home Win"])
            away_wins = len(current_df[current_df["Match_Result"] == "Away Win"])
            draws = len(current_df[current_df["Match_Result"] == "Draw"])
            
            st.metric("Season Matches", len(current_season_matches))
            st.metric("Avg Goals", round(avg_goals, 2))
            st.metric("Results", f"{home_wins}/{draws}/{away_wins}")
else:
    st.info("No matches yet. Add match data above to see the league table.")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# 3. 🚨 COUNTER ALERT DASHBOARD - TYPE A ALERTS
st.markdown("<h2 class='section-header'>3. 🚨 Counter Alert Dashboard ←────── HERE!</h2>", unsafe_allow_html=True)

if len(st.session_state.match_data) > 0:
    # Get Type A alerts
    alerts = get_type_a_alerts()
    
    # 🔴 CRITICAL ALERTS
    if alerts["f4_critical"] or alerts["s3_critical"]:
        st.markdown("<h3 style='color: #EF4444;'>🔴 CRITICAL ALERTS</h3>", unsafe_allow_html=True)
        
        # F!=4HA Critical Alerts
        for alert in alerts["f4_critical"]:
            st.markdown(f"""
            <div class='type-a-alert-critical'>
            {alert['message']}
            </div>
            """, unsafe_allow_html=True)
        
        # Status3 Critical Alerts
        for alert in alerts["s3_critical"]:
            st.markdown(f"""
            <div class='type-a-alert-critical'>
            {alert['message']}
            </div>
            """, unsafe_allow_html=True)
    
    # ⚠️ F!=4HA WARNINGS
    if alerts["f4_warning"]:
        st.markdown(f"<h3 style='color: #F59E0B;'>⚠️ F!=4HA Warnings (Counter ≥ {F4_ALERT_THRESHOLD})</h3>", unsafe_allow_html=True)
        
        for alert in alerts["f4_warning"]:
            st.markdown(f"""
            <div class='type-a-alert'>
            {alert['message']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"No F!=4HA warnings (counters < {F4_ALERT_THRESHOLD})")
    
    # 🎯 Status3 WARNINGS
    if alerts["s3_warning"]:
        st.markdown(f"<h3 style='color: #3B82F6;'>🎯 Status3 Warnings (Counter ≥ {S3_ALERT_THRESHOLD})</h3>", unsafe_allow_html=True)
        
        for alert in alerts["s3_warning"]:
            st.markdown(f"""
            <div class='type-a-alert-status3'>
            {alert['message']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"No Status3 warnings (counters < {S3_ALERT_THRESHOLD})")
    
    # 📊 ALERT SUMMARY
    st.markdown("<h4 style='color: #1E3A8A;'>📊 Alert Summary</h4>", unsafe_allow_html=True)
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.metric("F!=4HA Critical", len(alerts["f4_critical"]))
    
    with summary_col2:
        st.metric("F!=4HA Warnings", len(alerts["f4_warning"]))
    
    with summary_col3:
        st.metric("Status3 Critical", len(alerts["s3_critical"]))
    
    with summary_col4:
        st.metric("Status3 Warnings", len(alerts["s3_warning"]))
    
    # Alert settings
    with st.expander("⚙️ Alert Settings"):
        st.write(f"**F!=4HA Alerts:** Warning at counter ≥ {F4_ALERT_THRESHOLD}, Critical at ≥ {F4_CRITICAL_THRESHOLD}")
        st.write(f"**Status3 Alerts:** Warning at counter ≥ {S3_ALERT_THRESHOLD}, Critical at ≥ {S3_CRITICAL_THRESHOLD}")
        st.write("**Type A Format:** 'Team: Counter = X | Historical: Hits target within next Y matches Z% of time'")
else:
    st.info("No match data yet. Type A alerts will appear here when counters reach threshold levels.")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# 4. 📊 TEAM-SPECIFIC COUNTER ANALYSIS
st.markdown("<h2 class='section-header'>4. 📊 Team-Specific Counter Analysis</h2>", unsafe_allow_html=True)

if len(st.session_state.match_data) > 0:
    selected_team = st.selectbox("Select a team for detailed counter analysis:", sorted(VALID_TEAMS))
    
    if selected_team:
        patterns = calculate_historical_patterns()
        pattern = patterns[selected_team]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### F!=4HA Analysis for {selected_team}")
            current_f4 = st.session_state.ha_counters[selected_team]
            st.metric("Current Counter", current_f4)
            st.metric("Average Between", f"{pattern['avg_f4_before_reset']} matches")
            st.metric("4-goal Rate", f"{pattern['f4_hit_rate']}%")
            
            if current_f4 >= F4_CRITICAL_THRESHOLD:
                st.error(f"🔴 CRITICAL: Exceeded {F4_CRITICAL_THRESHOLD} limit!")
            elif current_f4 >= F4_ALERT_THRESHOLD:
                st.warning(f"⚠️ WARNING: Counter ≥ {F4_ALERT_THRESHOLD}")
            else:
                st.success(f"✅ Normal: Counter < {F4_ALERT_THRESHOLD}")
        
        with col2:
            st.markdown(f"#### Status3 Analysis for {selected_team}")
            current_s3 = st.session_state.status3_counters[selected_team]
            st.metric("Current Counter", current_s3)
            st.metric("Average Between", f"{pattern['avg_s3_before_reset']} matches")
            st.metric("3+ goal Rate", f"{pattern['s3_hit_rate']}%")
            
            if current_s3 >= S3_CRITICAL_THRESHOLD:
                st.error(f"🔥 CRITICAL: Exceeded {S3_CRITICAL_THRESHOLD} limit!")
            elif current_s3 >= S3_ALERT_THRESHOLD:
                st.warning(f"🎯 WARNING: Counter ≥ {S3_ALERT_THRESHOLD}")
            else:
                st.success(f"✅ Normal: Counter < {S3_ALERT_THRESHOLD}")
        
        # Type A alert for this team
        st.markdown("#### 🎯 Type A Alert Preview")
        if current_f4 >= F4_ALERT_THRESHOLD:
            probability = min(90, max(15, (current_f4 / pattern['avg_f4_before_reset'] * 75))) if pattern['avg_f4_before_reset'] > 0 else 70
            st.markdown(f"""
            <div class='type-a-alert'>
            ⚠️ **{selected_team}**: F!=4HA counter = **{current_f4}** | Historical: Hits 4 goals within next 3 matches **{probability}%** of time
            </div>
            """, unsafe_allow_html=True)
        
        if current_s3 >= S3_ALERT_THRESHOLD:
            probability = min(90, max(15, (current_s3 / pattern['avg_s3_before_reset'] * 70))) if pattern['avg_s3_before_reset'] > 0 else 65
            st.markdown(f"""
            <div class='type-a-alert-status3'>
            🎯 **{selected_team}**: Status3 counter = **{current_s3}** | Historical: Hits 3+ goals within next 2 matches **{probability}%** of time
            </div>
            """, unsafe_allow_html=True)
        
        if current_f4 < F4_ALERT_THRESHOLD and current_s3 < S3_ALERT_THRESHOLD:
            st.info(f"{selected_team} has no active Type A alerts (counters below threshold)")
else:
    st.info("Add match data to see team-specific analysis")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# 5. 🎯 MATCH PREDICTOR & ANALYTICS
st.markdown("<h2 class='section-header'>5. 🎯 Match Predictor & Analytics</h2>", unsafe_allow_html=True)

if len(st.session_state.match_data) > 0:
    pred_col1, pred_col2 = st.columns(2)
    
    with pred_col1:
        home_team = st.selectbox("**Home Team**", sorted(VALID_TEAMS), key="home_select")
    
    with pred_col2:
        away_team = st.selectbox("**Away Team**", sorted(VALID_TEAMS), key="away_select")
    
    if home_team == away_team:
        st.warning("Please select two different teams")
    else:
        st.info(f"Match Prediction: **{home_team}** vs **{away_team}**")
        
        # Show counters for both teams
        col_home, col_away = st.columns(2)
        
        with col_home:
            st.metric(f"{home_team} F!=4HA", st.session_state.ha_counters[home_team])
            st.metric(f"{home_team} Status3", st.session_state.status3_counters[home_team])
        
        with col_away:
            st.metric(f"{away_team} F!=4HA", st.session_state.ha_counters[away_team])
            st.metric(f"{away_team} Status3", st.session_state.status3_counters[away_team])
        
        # Check if this match might trigger alerts
        home_f4 = st.session_state.ha_counters[home_team]
        home_s3 = st.session_state.status3_counters[home_team]
        away_f4 = st.session_state.ha_counters[away_team]
        away_s3 = st.session_state.status3_counters[away_team]
        
        if home_f4 >= F4_ALERT_THRESHOLD or away_f4 >= F4_ALERT_THRESHOLD:
            st.warning("⚠️ This match could reset F!=4HA counters (4 goals total)")
        
        if home_s3 >= S3_ALERT_THRESHOLD or away_s3 >= S3_ALERT_THRESHOLD:
            st.info("🎯 This match could reset Status3 counters (3+ goals total)")
else:
    st.info("Add match data to use the match predictor")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# 6. 💾 DATA MANAGEMENT & EXPORT
st.markdown("<h2 class='section-header'>6. 💾 Data Management & Export</h2>", unsafe_allow_html=True)

if len(st.session_state.match_data) > 0:
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        csv_full = df.to_csv(index=False)
        st.download_button(
            "📋 Download ALL Match Data",
            data=csv_full,
            file_name=f"football_data_all_seasons.csv",
            mime="text/csv",
            help="Includes ALL matches from ALL seasons with Type A Alerts",
            use_container_width=True
        )
    
    with exp_col2:
        current_season_df = df[df["Season_Number"] == st.session_state.season_number]
        if len(current_season_df) > 0:
            csv_current = current_season_df.to_csv(index=False)
            st.download_button(
                f"🏆 Download Season {st.session_state.season_number} Data",
                data=csv_current,
                file_name=f"season_{st.session_state.season_number}_matches.csv",
                mime="text/csv",
                help=f"Matches from Season {st.session_state.season_number} only",
                use_container_width=True
            )
    
    with exp_col3:
        csv_league = league_df.to_csv(index=False)
        st.download_button(
            "📊 Download League Table",
            data=csv_league,
            file_name=f"season_{st.session_state.season_number}_league_table.csv",
            mime="text/csv",
            help="Current league standings",
            use_container_width=True
        )
    
    # Current status
    total_all_time = len(st.session_state.match_data)
    current_season_count = len([m for m in st.session_state.match_data if m[-2] == st.session_state.season_number])
    
    st.info(f"📈 **Data Summary**: {total_all_time} total matches | {current_season_count} in Season {st.session_state.season_number}")
else:
    st.info("No data to export yet")

# Footer
st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align: center; color: #6B7280; font-size: 0.9em; padding: 20px; margin-top: 30px; border-top: 2px solid #E5E7EB;'>
⚽ <strong>Football Analytics Dashboard</strong> • Season {st.session_state.season_number} • Type A Alerts Active • F!=4HA≥{F4_ALERT_THRESHOLD}/{F4_CRITICAL_THRESHOLD} • Status3≥{S3_ALERT_THRESHOLD}/{S3_CRITICAL_THRESHOLD}
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
