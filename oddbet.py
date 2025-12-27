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

# ============ FIXED PARSING FUNCTION ============
def parse_matches(text: str):
    """Robust parsing function that handles various input formats"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches, errors = [], []
    
    i = 0
    while i < len(lines):
        # Try to find a valid match starting from position i
        found_match = False
        
        # Look ahead up to 10 lines to find a valid match pattern
        for look_ahead in range(min(10, len(lines) - i)):
            # Check if we have a potential match pattern: Team, Score, Score, Team
            if i + look_ahead + 3 < len(lines):
                potential_home = lines[i + look_ahead]
                potential_home_score = lines[i + look_ahead + 1]
                potential_away_score = lines[i + look_ahead + 2]
                potential_away = lines[i + look_ahead + 3]
                
                # Check if this looks like a valid match
                is_home_team = potential_home in VALID_TEAMS
                is_away_team = potential_away in VALID_TEAMS
                is_home_score = potential_home_score.isdigit() and 0 <= int(potential_home_score) <= 20
                is_away_score = potential_away_score.isdigit() and 0 <= int(potential_away_score) <= 20
                
                if is_home_team and is_away_team and is_home_score and is_away_score:
                    # Found a valid match!
                    matches.append([
                        potential_home, 
                        int(potential_home_score), 
                        int(potential_away_score), 
                        potential_away
                    ])
                    i += look_ahead + 4  # Skip past this match
                    found_match = True
                    break
        
        if not found_match:
            # Skip this line and continue
            i += 1
    
    # Reverse order so bottom match is processed first
    matches.reverse()
    
    if not matches and text.strip():
        errors.append("No valid matches found. Please check format: Home Team, Home Score, Away Score, Away Team")
    
    return matches, errors

# ============ MAIN DASHBOARD LAYOUT ============

# Top section: Data Input
st.header("📥 Data Input & Processing")
col1, col2 = st.columns([2, 1])

with col1:
    raw_input = st.text_area(
        "**Paste match data**", 
        height=150,
        placeholder="Home Team\nHome Score\nAway Score\nAway Team\n...\n\nExample:\nManchester Blue\n2\n1\nLiverpool\nLondon Reds\n0\n0\nEverton"
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
            
            # Update counters (EXACTLY LIKE YOUR SECOND CODE)
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

            # Create strings EXACTLY like in your second code - OPTION A FORMAT
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
            
            # Add match data with ALL the columns you need
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
                f_ne_4_ha_str,  # F!=4HA at index 20
                status3_str,  # Status3 at index 21 (THIS IS WHAT YOU WANT - OPTION A FORMAT)
                st.session_state.season_number,
                f"Season {st.session_state.season_number}"
            ])
            
            processed_count += 1
        
        st.success(f"✅ Added {len(new_matches)} new matches to Season {st.session_state.season_number}")
        st.rerun()
    else:
        st.warning("⚠️ No valid matches found in the input")

# ============ DISPLAY SECTIONS ============
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
    
    # Create three main columns for the dashboard
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
        
        st.dataframe(league_df, use_container_width=True, height=500)
        
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
        
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)
        
        # Get recent matches (last 10)
        recent_matches = st.session_state.match_data[-10:] if len(st.session_state.match_data) > 0 else []
        
        for match in recent_matches[::-1]:  # Reverse to show newest first
            home = match[1]
            away = match[4]
            home_score = match[2]
            away_score = match[3]
            home_rank = match[11] if len(match) > 11 else "?"
            away_rank = match[12] if len(match) > 12 else "?"
            
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
                f"<span style='{home_style}'>{home_rank}. {home}</span> "
                f"{home_score}-{away_score} "
                f"<span style='{away_style}'>{away} ({away_rank}.)</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # ============ STATUS3 OUTPUT - OPTION A FORMAT ============
        st.subheader("📊 Status3 Summary")
        
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)
        
        # Get the last 15 matches for Status3 display
        recent_matches_for_status3 = st.session_state.match_data[-15:] if len(st.session_state.match_data) > 0 else []
        
        # Display Status3 in OPTION A FORMAT: "Team1: X | Team2: Y"
        for match in recent_matches_for_status3[::-1]:  # Reverse to show newest first
            if len(match) > 21:  # Check if Status3 data exists at index 21
                status3_string = match[21]  # Status3 is at index 21
                # Display it exactly as stored: "Team1: X | Team2: Y" - OPTION A FORMAT
                st.markdown(
                    f"<div style='font-size:14px; margin-bottom:5px;'>{status3_string}</div>", 
                    unsafe_allow_html=True
                )
        
        if len(recent_matches_for_status3) == 0:
            st.markdown("<div style='color:#888; text-align:center;'>No matches yet</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Download button
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📋 Download Full CSV", 
            data=csv_data,
            file_name="football_results.csv", 
            mime="text/csv",
            use_container_width=True
        )
        
        # Clear button
        if st.button("🗑️ Clear all data", use_container_width=True):
            st.session_state.match_data = []
            reset_league_for_new_season()
            st.rerun()
        
        # Quick stats
        st.subheader("📋 Quick Stats")
        total_matches = len(st.session_state.match_data)
        
        if total_matches > 0:
            # Calculate average goals
            total_goals = sum(match[2] + match[3] for match in st.session_state.match_data)
            avg_goals = total_goals / total_matches
            
            # Count results
            home_wins = sum(1 for match in st.session_state.match_data if match[2] > match[3])
            away_wins = sum(1 for match in st.session_state.match_data if match[3] > match[2])
            draws = sum(1 for match in st.session_state.match_data if match[2] == match[3])
            
            # Count 3-goal matches
            three_goal_matches = sum(1 for match in st.session_state.match_data if match[2] + match[3] == 3)
            
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
    st.subheader("🚀 Getting Started")
    
    col_welcome1, col_welcome2 = st.columns(2)
    
    with col_welcome1:
        st.markdown("""
        ### 📝 How to use this dashboard:
        1. **Paste match data** in the text area above
        2. Click **"Parse and Add Matches"** to process
        3. View **live league table** and statistics
        4. See **Status3 summary** in the right column
        
        ### 🔄 Automatic Season Management:
        - League resets automatically after 38 matches
        - **Match history is preserved** for CSV exports
        - Only season stats reset for new season
        - Manual reset button available
        """)
    
    with col_welcome2:
        st.markdown("""
        ### 📊 What you'll see:
        - **Live League Table** with rankings
        - **Status3 Tracking** (games since last 3-goal match)
        - **Data Export** options
        
        ### 💡 Tips:
        - Use consistent team names from the list
        - Data format: Team, Score, Score, Team
        - Example input:
        ```
        Manchester Blue
        2
        1
        Liverpool
        London Reds
        0
        0
        Everton
        ```
        """)

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 0.9em;'>"
    f"⚽ Football Analytics Dashboard • Season {st.session_state.season_number} • Status3 Display: Team Counters Format"
    f"</div>",
    unsafe_allow_html=True
)
