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

# ============ SIMPLE PARSING FUNCTION (LIKE YOUR SECOND CODE) ============
def parse_matches(text: str):
    """Simple parsing like in your second code example"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches, errors = [], []
    
    for i in range(0, len(lines), 4):
        chunk = lines[i:i+4]
        if len(chunk) < 4:
            errors.append(f"Incomplete group at lines {i+1}-{i+len(chunk)}")
            continue
        
        # Handle different possible formats
        if len(chunk) >= 4:
            home_team = chunk[0]
            # Find scores - they should be numeric
            scores = []
            team_names = []
            
            for item in chunk:
                if item.isdigit():
                    scores.append(int(item))
                elif item in VALID_TEAMS:
                    team_names.append(item)
            
            if len(scores) >= 2 and len(team_names) >= 2:
                home_team = team_names[0]
                away_team = team_names[1]
                home_score = scores[0]
                away_score = scores[1]
                
                if home_team not in VALID_TEAMS: 
                    errors.append(f"Invalid home team: {home_team}")
                if away_team not in VALID_TEAMS: 
                    errors.append(f"Invalid away team: {away_team}")
                
                if home_team in VALID_TEAMS and away_team in VALID_TEAMS:
                    matches.append([home_team, home_score, away_score, away_team])
    
    # Reverse order so bottom match is processed first
    matches.reverse()
    return matches, errors

# ============ MAIN DASHBOARD LAYOUT ============

# Two equal columns like in your second code
col1, col2 = st.columns([1, 1])

with col1:
    raw_input = st.text_area("**Paste match data**", height=200,
                             placeholder="Home Team\nHome Score\nAway Score\nAway Team\n...\n\nExample:\nManchester Blue\n2\n1\nLiverpool\nLondon Reds\n0\n0\nEverton")
    parse_clicked = st.button("🚀 Parse and Add Matches", type="primary", use_container_width=True)

with col2:
    st.markdown("### 🛠️ Quick Actions")
    
    max_matches = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS]) if st.session_state.team_stats else 0
    st.metric("📅 Current Season", f"Season {st.session_state.season_number}", f"{max_matches}/38 matches")
    
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
    new_matches, errors = parse_matches(raw_input)
    
    if errors:
        st.error("❌ Input errors detected. No new data added.")
        with st.expander("Details"):
            for e in errors: 
                st.write(f"- {e}")
    elif new_matches:
        # Check if we need to reset season
        needs_reset = False
        for home_team, home_score, away_score, away_team in new_matches:
            if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                needs_reset = True
                break
        
        if needs_reset:
            check_and_reset_season()
        
        # Process each match
        for home_team, home_score, away_score, away_team in new_matches:
            # Double-check season reset
            if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                check_and_reset_season()
            
            total_g_value = home_score + away_score
            
            # Determine Total-G display
            if total_g_value == 4:
                total_g_display = "Won"
            elif total_g_value == 3:
                total_g_display = "3 ✔"
            else:
                total_g_display = str(total_g_value)
            
            # Update counters (EXACTLY LIKE YOUR SECOND CODE)
            if total_g_value == 4:
                st.session_state.home_counters[home_team] = 0
                st.session_state.away_counters[away_team] = 0
                st.session_state.ha_counters[home_team] = 0
                st.session_state.ha_counters[away_team] = 0
            else:
                st.session_state.home_counters[home_team] += 1
                st.session_state.away_counters[away_team] += 1
                st.session_state.ha_counters[home_team] += 1
                st.session_state.ha_counters[away_team] += 1

            if total_g_value == 3:
                st.session_state.status3_counters[home_team] = 0
                st.session_state.status3_counters[away_team] = 0
            else:
                st.session_state.status3_counters[home_team] += 1
                st.session_state.status3_counters[away_team] += 1

            # Create strings EXACTLY like in your second code
            f_ne_4_ha_str = f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}"
            status3_str = f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}"

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

            # Add match data (SIMPLIFIED VERSION LIKE YOUR SECOND CODE)
            st.session_state.match_data.append([
                home_team, home_score, away_score, away_team,
                total_g_display,
                st.session_state.home_counters[home_team],
                st.session_state.away_counters[away_team],
                f_ne_4_ha_str, status3_str,
                st.session_state.season_number,
                f"Season {st.session_state.season_number}"
            ])
        
        st.success(f"✅ Added {len(new_matches)} new matches to Season {st.session_state.season_number}")
        st.rerun()
    else:
        st.warning("⚠️ No valid matches found in the input")

# ============ DISPLAY SECTIONS ============
if st.session_state.match_data:
    # Create DataFrame with appropriate columns
    column_names = [
        "Home Team", "Home Score", "Away Score", "Away Team", "Total-G",
        "F<4H", "F<4A", "F!=4HA", "Status3", "Season_Number", "Season_Label"
    ]
    
    df = pd.DataFrame(st.session_state.match_data, columns=column_names)
    
    # Display in two columns like your second code
    st.markdown("---")
    st.header(f"📊 Season {st.session_state.season_number} Dashboard")
    
    # Create two columns for display
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        st.subheader("🏆 League Table")
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
        
        st.dataframe(league_df, use_container_width=True, height=400)
        
        # Show match data table
        st.subheader("📋 All Match Data")
        st.dataframe(df.tail(20), use_container_width=True, height=300)
    
    with right_col:
        st.subheader("🔄 Recent Match Summary")
        
        # Recent matches frame (BLACK BOX LIKE YOUR SECOND CODE)
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)
        
        # Get recent matches (last 10)
        recent_matches = st.session_state.match_data[-10:] if len(st.session_state.match_data) > 0 else []
        
        for match in recent_matches[::-1]:  # Reverse to show newest first
            home = match[0]
            away = match[3]
            home_score = match[1]
            away_score = match[2]
            
            # Color code based on result
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
                f"<span style='{home_style}'>{home}</span> "
                f"{home_score}-{away_score} "
                f"<span style='{away_style}'>{away}</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
        
        if len(recent_matches) == 0:
            st.markdown("<div style='color:#888; text-align:center;'>No matches yet</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # ============ STATUS3 OUTPUT (EXACTLY LIKE YOUR SECOND CODE) ============
        st.subheader("📊 Status3 Summary")
        
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)
        
        # Get the last 10 matches for Status3 display
        recent_matches_for_status3 = st.session_state.match_data[-10:] if len(st.session_state.match_data) > 0 else []
        
        # Display Status3 EXACTLY like in your second code
        for match in recent_matches_for_status3[::-1]:  # Reverse to show newest first
            if len(match) > 8:  # Check if Status3 data exists
                status3_string = match[8]  # Status3 is at index 8
                st.markdown(
                    f"<div style='font-size:14px; margin-bottom:5px;'>{status3_string}</div>", 
                    unsafe_allow_html=True
                )
        
        if len(recent_matches_for_status3) == 0:
            st.markdown("<div style='color:#888; text-align:center;'>No matches yet</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Download button (LIKE YOUR SECOND CODE)
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📋 Download Full CSV", 
            data=csv_data,
            file_name="football_results.csv", 
            mime="text/csv",
            use_container_width=True
        )
        
        # Clear button (LIKE YOUR SECOND CODE)
        if st.button("🗑️ Clear all data", use_container_width=True):
            st.session_state.match_data = []
            st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.team_stats = {
                team: {
                    "P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, 
                    "GD": 0, "Pts": 0, "Form": []
                }
                for team in VALID_TEAMS
            }
            st.session_state.match_counter = 1
            st.session_state.season_number = 1
            st.rerun()
        
        # Quick stats
        st.subheader("📋 Quick Stats")
        total_matches = len(st.session_state.match_data)
        
        if total_matches > 0:
            # Calculate average goals
            total_goals = sum(match[1] + match[2] for match in st.session_state.match_data)
            avg_goals = total_goals / total_matches
            
            # Count results
            home_wins = sum(1 for match in st.session_state.match_data if match[1] > match[2])
            away_wins = sum(1 for match in st.session_state.match_data if match[2] > match[1])
            draws = sum(1 for match in st.session_state.match_data if match[1] == match[2])
            
            # Count 3-goal matches
            three_goal_matches = sum(1 for match in st.session_state.match_data if match[1] + match[2] == 3)
            
            st.metric("Total Matches", total_matches)
            st.metric("Avg Goals/Match", round(avg_goals, 2))
            st.metric("3-Goal Matches", three_goal_matches, 
                     f"{round(three_goal_matches/total_matches*100, 1)}%")
        else:
            st.metric("Total Matches", 0)
            st.metric("Avg Goals/Match", 0)
            st.metric("3-Goal Matches", 0)

else:
    # Welcome message when no data exists
    st.markdown("---")
    st.info("""
    ### 📝 How to use this dashboard:
    1. **Paste match data** in the text area above
    2. Click **"Parse and Add Matches"** to process
    3. View **live league table** and statistics
    4. See **Status3 summary** in the right column
    
    ### 📊 Data format (simple):
    ```
    Home Team
    Home Score
    Away Score
    Away Team
    ...
    ```
    """)

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 0.9em;'>"
    f"⚽ Football Analytics Dashboard • Season {st.session_state.season_number} • Status3 Display Working"
    f"</div>",
    unsafe_allow_html=True
)
