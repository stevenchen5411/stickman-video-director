"""Widgets, overlays, transitions, caption styles, themes and voice personas (all JSON)."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _items(rows: List[Tuple[str, str, Dict[str, Any]]], fmt: str) -> List[Dict[str, Any]]:
    return [{"id": i, "tags": t.split(), "json": {"id": i, "format": fmt, **d}} for i, t, d in rows]


# =========================================================================== widgets
def widgets() -> List[Dict[str, Any]]:
    W: List[Tuple[str, str, Dict[str, Any]]] = []

    def w(wid, tags, typ, data, style=None):
        W.append((wid, tags, {"type": typ, "data": data, "style": style or {}}))

    # counters
    w("counter_followers", "social_media growth marketing", "counter", {"from": 0, "to": 1000000, "label": "followers", "title": "Followers"})
    w("counter_money", "finance money", "counter", {"from": 0, "to": 1000000, "prefix": "$", "label": "in 5 years", "title": "Net worth"})
    w("counter_percent", "general data", "counter", {"from": 0, "to": 97, "suffix": "%", "label": "of people", "title": "Survey"})
    w("counter_years", "history time", "counter", {"from": 0, "to": 2000, "label": "years ago", "title": "Long ago"})
    w("counter_days_streak", "productivity self_improvement", "counter", {"from": 0, "to": 365, "suffix": " days", "label": "streak", "title": "Habit streak"})
    w("counter_calories", "health fitness food", "counter", {"from": 0, "to": 2400, "suffix": " kcal", "label": "per day", "title": "Calories"})
    w("counter_steps", "fitness health", "counter", {"from": 0, "to": 10000, "label": "steps today", "title": "Steps"})
    w("counter_crypto_price", "crypto finance trading", "counter", {"from": 20000, "to": 100000, "prefix": "$", "label": "per coin", "title": "Price"})
    w("counter_views", "media social_media", "counter", {"from": 0, "to": 25000000, "label": "views", "title": "Viral video"})
    w("counter_temperature", "science weather", "counter", {"from": 20, "to": 100, "suffix": "°C", "label": "boiling point", "title": "Temperature"})
    # progress
    w("progress_goal", "goal productivity", "progress", {"title": "Goal", "items": [{"label": "Progress", "value": 72}]})
    w("progress_skills", "career education", "progress", {"title": "Skills", "items": [{"label": "Coding", "value": 85}, {"label": "Design", "value": 60}, {"label": "Writing", "value": 40}]})
    w("progress_habits", "self_improvement productivity", "progress", {"title": "This week", "items": [{"label": "Sleep", "value": 90}, {"label": "Exercise", "value": 55}, {"label": "Reading", "value": 30}]})
    w("progress_project", "business productivity", "progress", {"title": "Project", "items": [{"label": "Design", "value": 100}, {"label": "Build", "value": 65}, {"label": "Launch", "value": 10}]})
    w("progress_savings", "finance savings", "progress", {"title": "Savings", "items": [{"label": "Emergency fund", "value": 80}, {"label": "Vacation", "value": 35}]})
    w("progress_loading", "tech comedy", "progress", {"title": "Loading...", "items": [{"label": "Brain", "value": 99}]})
    # donuts & pies
    w("donut_percent", "general data", "donut", {"value": 73, "label": "of people agree"})
    w("donut_success_rate", "business data", "donut", {"value": 92, "label": "success rate"})
    w("donut_market_share", "business finance", "donut", {"value": 41, "label": "market share"})
    w("donut_sleep_quality", "health sleep", "donut", {"value": 64, "label": "deep sleep score"})
    w("donut_battery_human", "mental_health productivity", "donut", {"value": 18, "label": "energy left"}, {"color": "theme.danger"})
    w("pie_budget", "finance savings", "pie", {"values": [50, 30, 20], "labels": ["Needs", "Wants", "Save"]})
    w("pie_time_day", "productivity self_improvement", "pie", {"values": [8, 8, 4, 4], "labels": ["Sleep", "Work", "Phone", "Life"]})
    w("pie_portfolio", "crypto investing finance", "pie", {"values": [45, 30, 15, 10], "labels": ["BTC", "ETH", "Stable", "Alt"]})
    w("pie_diet", "food health fitness", "pie", {"values": [40, 30, 30], "labels": ["Carbs", "Protein", "Fat"]})
    w("pie_earth_water", "science environment", "pie", {"values": [71, 29], "labels": ["Water", "Land"]})
    # line charts
    w("line_growth", "business finance growth", "line_chart", {"title": "Growth", "values": [1, 2, 2.5, 4, 3.8, 6, 9], "end_label": "+800%"})
    w("line_decline", "business finance decline", "line_chart", {"title": "Decline", "values": [9, 8, 8.5, 6, 5, 3, 1.5], "end_label": "-80%"})
    w("line_volatile_stock", "trading investing finance", "line_chart", {"title": "Stock", "values": [5, 7, 4, 8, 3, 9, 6, 10]})
    w("line_crypto_pump", "crypto trading", "line_chart", {"title": "Altcoin", "values": [1, 1.1, 1, 1.2, 1.3, 5, 4.2], "end_label": "PUMP"})
    w("line_weight_loss", "fitness health", "line_chart", {"title": "Weight", "values": [92, 90, 89, 86, 85, 82, 80], "end_label": "-12 kg"}, {"color": "#34d399"})
    w("line_population", "history science", "line_chart", {"title": "Population", "values": [1, 1.2, 1.6, 2.5, 4, 6, 8], "end_label": "8B"})
    w("line_temperature_rise", "environment science weather", "line_chart", {"title": "Global temp", "values": [0, 0.1, 0.2, 0.4, 0.7, 1.0, 1.3], "end_label": "+1.3°C"},
      {"color": "theme.danger"})
    # checklists
    w("checklist_morning", "productivity self_improvement", "checklist", {"title": "Morning routine", "items": ["Water", "Stretch", "Plan the day", "No phone"], "checked": [True, True, True, False]})
    w("checklist_study", "education", "checklist", {"title": "Study plan", "items": ["Read chapter", "Practice", "Review notes"]})
    w("checklist_launch", "startup business", "checklist", {"title": "Launch", "items": ["Build", "Test", "Market", "Ship"]})
    w("checklist_pros", "general comparison", "checklist", {"title": "Pros", "items": ["Cheap", "Fast", "Simple"]})
    w("checklist_cons", "general comparison", "checklist", {"title": "Cons", "items": ["Risky", "Slow", "Complex"], "checked": [False, False, False]})
    w("checklist_safety", "safety construction health", "checklist", {"title": "Safety", "items": ["Helmet", "Gloves", "Boots", "Goggles"]})
    w("checklist_symptoms", "health medical", "checklist", {"title": "Symptoms", "items": ["Fever", "Cough", "Fatigue"], "checked": [True, False, True]})
    # timelines & steps
    w("timeline_history", "history education", "timeline", {"events": [{"year": "3000 BC", "label": "Writing"}, {"year": "1440", "label": "Printing"},
                                                                       {"year": "1990", "label": "Web"}, {"year": "Now", "label": "AI"}]})
    w("timeline_startup", "startup business", "timeline", {"events": [{"year": "Day 1", "label": "Idea"}, {"year": "Month 3", "label": "MVP"},
                                                                     {"year": "Year 1", "label": "Users"}, {"year": "Year 3", "label": "Profit"}]})
    w("timeline_life", "self_improvement storytelling", "timeline", {"events": [{"year": "18", "label": "Start"}, {"year": "25", "label": "Struggle"},
                                                                               {"year": "30", "label": "Breakthrough"}]})
    w("timeline_evolution", "science biology history", "timeline", {"events": [{"year": "4B", "label": "Cells"}, {"year": "500M", "label": "Fish"},
                                                                              {"year": "65M", "label": "Dinos end"}, {"year": "300K", "label": "Humans"}]})
    w("timeline_crypto", "crypto history finance", "timeline", {"events": [{"year": "2009", "label": "Genesis"}, {"year": "2015", "label": "Smart contracts"},
                                                                          {"year": "2020", "label": "DeFi"}, {"year": "2024", "label": "ETFs"}]})
    w("timeline_treatment", "health medical storytelling", "timeline", {"events": [{"year": "Week 1", "label": "First dose"}, {"year": "Week 4", "label": "Response"},
                                                                                  {"year": "Month 2", "label": "Shrinking"}, {"year": "Year 6", "label": "Clear"}]})
    w("steps_three_plan", "general productivity", "steps", {"steps": ["Plan", "Act", "Review"]})
    w("steps_process_four", "business process", "steps", {"steps": ["Idea", "Build", "Test", "Launch"]})
    w("steps_recipe", "food cooking", "steps", {"steps": ["Chop", "Cook", "Serve"]})
    w("steps_scientific_method", "science education", "steps", {"steps": ["Ask", "Test", "Analyze", "Share"]})
    w("steps_habit_loop", "psychology self_improvement", "steps", {"steps": ["Cue", "Routine", "Reward"]})
    w("steps_trade_setup", "trading crypto finance", "steps", {"steps": ["Entry", "Stop", "Target"]})
    # versus / ranking / stats
    w("versus_before_after", "self_improvement comparison", "versus", {"left": {"title": "BEFORE", "value": "Tired", "caption": "4h sleep"},
                                                                      "right": {"title": "AFTER", "value": "Sharp", "caption": "8h sleep"}})
    w("versus_save_spend", "finance savings", "versus", {"left": {"title": "SAVE", "value": "$500", "caption": "per month"}, "right": {"title": "SPEND", "value": "$0", "caption": "left over"}})
    w("versus_myth_fact", "education science", "versus", {"left": {"title": "MYTH", "value": "✗"}, "right": {"title": "FACT", "value": "✓"}})
    w("versus_old_new", "tech business", "versus", {"left": {"title": "OLD WAY", "value": "Slow"}, "right": {"title": "NEW WAY", "value": "Fast"}})
    w("versus_cat_dog", "animals pets comedy", "versus", {"left": {"title": "CATS", "value": "48%"}, "right": {"title": "DOGS", "value": "52%"}})
    w("versus_bull_bear", "trading crypto finance", "versus", {"left": {"title": "BULLS", "value": "62%"}, "right": {"title": "BEARS", "value": "38%"}})
    w("ranking_top3", "general", "ranking", {"title": "Top 3", "items": ["First place", "Second place", "Third place"]})
    w("ranking_top5", "general", "ranking", {"title": "Top 5", "items": ["One", "Two", "Three", "Four", "Five"]})
    w("ranking_richest", "finance business history", "ranking", {"title": "Richest", "items": ["Founder A", "Investor B", "Heir C"]})
    w("ranking_best_habits", "self_improvement productivity", "ranking", {"title": "Best habits", "items": ["Sleep", "Walk", "Read"]})
    w("stat_big_number", "general data", "stat_card", {"label": "Did you know?", "value": "1 in 3", "delta": "+12%"})
    w("stat_revenue", "business finance", "stat_card", {"label": "Revenue", "value": "$2.4M", "delta": "+38%"})
    w("stat_users", "startup tech", "stat_card", {"label": "Daily users", "value": "120K", "delta": "+9%"})
    w("stat_heart_rate", "health fitness", "stat_card", {"label": "Heart rate", "value": "142 bpm", "delta": "+40"}, {"color": "theme.danger"})
    w("stat_price_drop", "finance trading crypto", "stat_card", {"label": "Price", "value": "$0.42", "delta": "-63%"}, {"color": "theme.danger"})
    w("stat_light_speed", "science physics space", "stat_card", {"label": "Speed of light", "value": "300,000 km/s"})
    w("stat_tumor_shrink", "health medical", "stat_card", {"label": "Tumor size", "value": "-63%", "delta": "-63%"}, {"color": "#34d399"})
    # quotes
    w("quote_stoic", "stoicism self_improvement", "quote", {"text": "We suffer more in imagination than in reality.", "author": "Seneca"})
    w("quote_motivation", "motivation self_improvement", "quote", {"text": "Small steps every day beat big steps once.", "author": "Unknown"})
    w("quote_science", "science education", "quote", {"text": "Nothing in life is to be feared, only understood.", "author": "Marie Curie"})
    w("quote_customer", "business marketing", "quote", {"text": "This changed how I work. I can't go back.", "author": "A happy customer"})
    # gauges, countdowns, calendars
    w("gauge_risk", "finance trading safety", "gauge", {"value": 85, "label": "Risk level"})
    w("gauge_fear_greed", "crypto trading finance", "gauge", {"value": 78, "label": "Greed index"})
    w("gauge_stress", "mental_health psychology", "gauge", {"value": 70, "label": "Stress"})
    w("gauge_speed", "transport sports", "gauge", {"value": 92, "label": "Speed"})
    w("countdown_ten", "general time", "countdown", {"from": 10, "speed": 4, "label": "Time left"})
    w("countdown_launch", "space startup", "countdown", {"from": 5, "speed": 2.5, "label": "Launch in"})
    w("countdown_last_chance", "marketing shopping", "countdown", {"from": 9, "speed": 3, "label": "Offer ends"})
    w("calendar_deadline", "business productivity", "calendar", {"month": "FRI", "day": 13, "label": "Deadline"})
    w("calendar_new_year", "holiday celebration", "calendar", {"month": "JAN", "day": 1, "label": "New year"})
    w("calendar_monday", "productivity comedy", "calendar", {"month": "MON", "day": 7, "label": "Start on Monday"})
    # money & logic
    w("price_drop_tag", "shopping marketing", "price_tag", {"old": "$99", "new": "$49", "label": "Today only"})
    w("price_hike_tag", "finance economy", "price_tag", {"old": "$3", "new": "$7", "label": "Coffee in 2030"})
    w("equation_habit", "self_improvement productivity", "equation", {"parts": ["Habit", "+", "Time", "=", "Result"]})
    w("equation_money", "finance investing", "equation", {"parts": ["Save", "+", "Invest", "=", "Wealth"]})
    w("equation_energy", "science physics", "equation", {"parts": ["E", "=", "mc²"]})
    w("equation_success", "motivation business", "equation", {"parts": ["Idea", "×", "Action", "=", "$$$"]})
    w("map_trip", "travel adventure", "map_route", {"pins": [{"x": 0.25, "y": 0.55, "label": "Home"}, {"x": 0.75, "y": 0.45, "label": "Dream"}]})
    w("map_delivery", "logistics business", "map_route", {"pins": [{"x": 0.2, "y": 0.4, "label": "Store"}, {"x": 0.8, "y": 0.6, "label": "You"}]})
    w("map_migration", "history animals nature", "map_route", {"pins": [{"x": 0.3, "y": 0.35, "label": "North"}, {"x": 0.62, "y": 0.75, "label": "South"}]})
    w("battery_draining", "mental_health productivity", "battery", {"value": 8, "drain": True, "label": "Social battery"})
    w("battery_charging_up", "productivity energy", "battery", {"value": 100, "label": "Recharged"})
    w("battery_phone_low", "tech comedy", "battery", {"value": 3, "drain": True, "label": "1% left"})
    w("scale_work_life", "self_improvement career", "balance_scale", {"left": "Work", "right": "Life", "tilt_deg": -14})
    w("scale_risk_reward", "trading investing finance", "balance_scale", {"left": "Risk", "right": "Reward", "tilt_deg": 12})
    w("scale_justice", "law", "balance_scale", {"left": "Facts", "right": "Feelings", "tilt_deg": -8})
    # more of the classic types
    w("bar_growth_five", "business growth data", "bar_chart", {"labels": ["2021", "2022", "2023", "2024", "2025"], "values": [2, 3, 5, 8, 13]}, {"show_values": True})
    w("bar_survey", "general data", "bar_chart", {"labels": ["Yes", "No", "Maybe"], "values": [62, 23, 15]})
    w("bar_quarters", "business finance", "bar_chart", {"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [4, 6, 3, 9]})
    w("bar_sleep_hours", "health sleep", "bar_chart", {"labels": ["Mon", "Tue", "Wed", "Thu", "Fri"], "values": [6, 5, 7, 4, 8]})
    W.append(("comparison_rich_poor_habits", "finance self_improvement", {"type": "comparison_card", "data": {"left": {"title": "Habit A", "bullets": ["Reads daily", "Saves 20%"]},
                                                                                                              "right": {"title": "Habit B", "bullets": ["Scrolls daily", "Spends it all"]}}}))
    W.append(("comparison_myth_truth", "education science", {"type": "comparison_card", "data": {"left": {"title": "Myth", "bullets": ["Sounds true", "Spreads fast"]},
                                                                                                 "right": {"title": "Truth", "bullets": ["Backed by data", "Less viral"]}}}))
    W.append(("funnel_marketing", "marketing business", {"type": "funnel", "data": {"stages": [{"label": "Views", "value": 1000}, {"label": "Clicks", "value": 240},
                                                                                              {"label": "Buyers", "value": 38}]}}))
    W.append(("funnel_hiring", "career business", {"type": "funnel", "data": {"stages": [{"label": "Applied", "value": 500}, {"label": "Interview", "value": 40},
                                                                                         {"label": "Hired", "value": 3}]}}))
    out = _items(W, "widget/v1")
    for it in out:
        it["json"].setdefault("animate", "auto")
    return out


# =========================================================================== overlays
def overlays() -> List[Dict[str, Any]]:
    O: List[Tuple[str, str, Dict[str, Any]]] = []

    def o(oid, tags, kind, **kw):
        O.append((oid, tags, {"kind": kind, "anchor": "character.head", **kw}))

    for oid, tags, prop in (("pop_idea_bulb", "idea thinking creativity", "light_bulb_on"), ("pop_money_bag", "finance money", "money_bag"),
                            ("pop_heart", "love relationships", "heart_red"), ("pop_warning", "safety general", "warning_sign"),
                            ("pop_check", "general success", "check_badge"), ("pop_cross", "general failure", "cross_badge"),
                            ("pop_question", "thinking confused", "question_badge"), ("pop_fire", "trending motivation", "fire_flame"),
                            ("pop_trophy", "winner success", "trophy_gold"), ("pop_rocket", "startup crypto growth", "rocket_moon"),
                            ("pop_crypto_coin", "crypto finance", "crypto_coin"), ("pop_brain", "psychology thinking science", "brain_anatomy"),
                            ("pop_clock", "time productivity", "alarm_clock_ring"), ("pop_phone_notif", "tech social_media addiction", "phone_notification"),
                            ("pop_virus", "health disease", "virus_germ"), ("pop_dna", "science biology health", "dna_helix"),
                            ("pop_pill", "health medicine", "pill_capsule"), ("pop_syringe", "health medical", "syringe"),
                            ("pop_chart_up", "finance growth", "chart_line_up"), ("pop_chart_down", "finance decline", "arrow_trend_down"),
                            ("pop_lock", "security tech", "lock_closed"), ("pop_gift", "holiday celebration", "gift_box"),
                            ("pop_book", "education", "book_open"), ("pop_coffee", "food productivity", "coffee_cup"),
                            ("pop_burger", "food", "burger"), ("pop_dumbbell", "fitness", "dumbbell"), ("pop_sleep_moon", "sleep", "moon_crescent"),
                            ("pop_robot", "ai tech", "robot_head"), ("pop_target", "goal business", "target_bullseye"),
                            ("pop_gem", "finance luxury", "diamond_gem"), ("pop_bomb_warning", "danger comedy", "radioactive_sign")):
        o(oid, tags, "icon_pop", prop_id=prop, size=0.17)
    for sym, tags in (("exclaim", "surprise emphasis"), ("question", "confused"), ("heart", "love"), ("star", "winner"), ("bolt", "energy idea"),
                      ("check", "success"), ("cross", "failure"), ("dollar", "money"), ("idea", "idea"), ("warning", "danger"), ("fire", "trending"),
                      ("anger", "angry"), ("plus_one", "social_media growth"), ("zzz", "sleep")):
        o(f"symbol_{sym}", f"{tags} general", "icon_pop", symbol=sym, size=0.14)
    for oid, tags, kw in (("thought_question", "thinking confused", {"text": "?"}), ("thought_money", "finance money", {"prop_id": "money_bag"}),
                          ("thought_love", "love relationships", {"prop_id": "heart_red"}), ("thought_food", "food", {"prop_id": "pizza_slice"}),
                          ("thought_idea", "idea creativity", {"prop_id": "light_bulb_on"}), ("thought_sleep", "sleep", {"text": "Zzz"}),
                          ("thought_crypto", "crypto finance", {"prop_id": "rocket_moon"}), ("thought_home", "home family", {"prop_id": "house_home"})):
        o(oid, tags, "thought", size=0.22, **kw)
    for oid, tags, kw in (("hearts_rise", "love relationships", {"text": "♥", "color": "#f43f5e"}),
                          ("music_notes_rise", "music", {"text": ["♪", "♫"], "color": "theme.highlight"}),
                          ("zzz_rise", "sleep tired", {"text": "Z", "color": "#a5b4fc", "count": 3, "lifetime_sec": 2.2}),
                          ("stars_rise", "celebration magic", {"text": "★", "color": "theme.highlight"}),
                          ("plus_one_rise", "social_media growth", {"text": "+1", "color": "#22c55e"}),
                          ("question_rise", "confused thinking", {"text": "?", "color": "theme.accent"}),
                          ("exclaim_rise", "surprise", {"text": "!", "color": "#f97316"}),
                          ("dollar_rise", "finance money growth", {"text": "$", "color": "#22c55e"}),
                          ("money_rain", "finance money celebration", {"text": "$", "color": "#22c55e", "direction": "down", "spread": "screen", "count": 14, "size": 0.06}),
                          ("coins_rain", "finance crypto", {"text": "●", "color": "#fbbf24", "direction": "down", "spread": "screen", "count": 16, "size": 0.05}),
                          ("hearts_rain", "love celebration", {"text": "♥", "color": "#f472b6", "direction": "down", "spread": "screen", "count": 14}),
                          ("check_rise", "success productivity", {"text": "✓", "color": "#22c55e"}),
                          ("cross_rise", "failure", {"text": "✗", "color": "theme.danger"}),
                          ("bolt_rise", "energy idea", {"text": "⚡", "color": "#facc15"}),
                          ("sweat_rise", "stress", {"text": "💧", "color": "#7dd3fc"})):
        if oid == "sweat_rise":
            continue
        o(oid, tags, "rise", **kw)
    for oid, tags, kw in (("dizzy_stars_orbit", "comedy confused", {"text": "★", "count": 3, "speed": 5}),
                          ("birds_orbit", "comedy confused", {"text": "✦", "count": 4, "speed": 4, "color": "#f8fafc"}),
                          ("money_orbit", "finance money", {"text": "$", "count": 3, "speed": 3, "color": "#22c55e"}),
                          ("hearts_orbit", "love", {"text": "♥", "count": 4, "speed": 3, "color": "#f43f5e"})):
        o(oid, tags, "orbit", **kw)
    o("burst_emphasis", "emphasis surprise general", "burst", count=16, color="theme.highlight")
    o("burst_anger", "angry", "burst", count=12, color="theme.danger", speed=14)
    o("burst_idea", "idea", "burst", count=10, color="#fde047", speed=6)
    o("sparkle_magic", "magic celebration", "sparkle", count=7, color="theme.highlight")
    o("sparkle_clean", "home health", "sparkle", count=5, color="#e0f2fe", speed=1.2)
    o("confetti_party", "celebration winner holiday", "confetti", count=46)
    o("confetti_gold", "winner celebration", "confetti", count=40, colors=["#fbbf24", "#fde68a", "#f59e0b", "#ffffff"])
    o("rain_weather", "weather sad", "weather", weather="rain", count=70)
    o("snow_weather", "weather holiday", "weather", weather="snow", count=60)
    o("leaves_falling", "nature weather", "weather", weather="leaves", count=26)
    o("vignette_dark", "mystery tension spooky", "vignette", strength=0.7)
    o("vignette_soft", "calm storytelling", "vignette", strength=0.4)
    o("vignette_red_alarm", "danger tension", "vignette", strength=0.55, color="#7f1d1d")
    o("spotlight_focus", "entertainment motivation", "spotlight")
    o("flash_white", "impact surprise", "flash")
    o("flash_red", "danger impact", "flash", color="#ef4444")
    o("focus_lines_manga", "emphasis surprise comedy", "focus_lines", count=44)
    o("motion_lines_left", "movement fitness", "motion_lines", side="left")
    o("motion_lines_right", "movement fitness", "motion_lines", side="right")
    o("glitch_screen", "tech security mystery", "glitch", count=7)
    o("ring_pulse_signal", "tech communication", "ring_pulse")
    o("ring_pulse_alert", "danger health", "ring_pulse", color="theme.danger", speed=1.8)
    o("dust_landing", "impact movement", "dust")
    o("shine_sweep", "luxury success", "shine")
    O.append(("sweat_drops_big", "stress nervous", {"kind": "particles", "anchor": "character.head", "count": 4,
                                                    "particle": {"size": 0.022, "color": "#7dd3fc"}, "motion": {"direction": [0.6, -1.0], "gravity": 1.2, "lifetime_sec": 0.9}}))
    O.append(("tears_stream", "sad", {"kind": "particles", "anchor": "character.head", "count": 6,
                                      "particle": {"size": 0.012, "color": "#38bdf8"}, "motion": {"direction": [0.2, 0.2], "gravity": 2.2, "lifetime_sec": 0.7}}))
    O.append(("exclaim_marks", "surprise", {"kind": "floating_text", "anchor": "character.head", "text": "!", "count": 3, "color": "#f97316", "size": 0.06,
                                            "motion": {"bob": 0.01, "lifetime_sec": 1.0}}))
    O.append(("dollar_signs_float", "finance money", {"kind": "floating_text", "anchor": "character.head", "text": "$", "count": 3, "color": "#22c55e", "size": 0.06,
                                                      "motion": {"bob": 0.012, "lifetime_sec": 1.4}}))
    return _items(O, "overlay/v1")


# =========================================================================== transitions
def transitions() -> List[Dict[str, Any]]:
    T: List[Tuple[str, str, Dict[str, Any]]] = [
        ("fade_quick", "general calm", {"type": "fade", "duration_sec": 0.15, "easing": "ease_in_out"}),
        ("fade_slow", "calm storytelling", {"type": "fade", "duration_sec": 0.6, "easing": "ease_in_out"}),
        ("whip_pan_right", "energy general", {"type": "whip_pan", "direction": "right", "duration_sec": 0.25, "motion_blur": True, "easing": "expo_out"}),
        ("whip_pan_left_clean", "general", {"type": "whip_pan", "direction": "left", "duration_sec": 0.3, "motion_blur": False, "easing": "expo_out"}),
        ("zoom_in_flash", "impact emphasis", {"type": "zoom", "from_scale": 1.0, "to_scale": 1.8, "duration_sec": 0.3, "flash": True, "easing": "expo_out"}),
        ("zoom_out_soft", "calm reveal", {"type": "zoom", "from_scale": 1.0, "to_scale": 0.7, "duration_sec": 0.45, "easing": "ease_out"}),
        ("zoom_crash", "impact comedy", {"type": "zoom", "from_scale": 1.0, "to_scale": 2.6, "duration_sec": 0.22, "flash": False, "easing": "expo_out"}),
        ("wipe_right", "general", {"type": "wipe", "angle_deg": 0, "duration_sec": 0.35, "easing": "ease_in_out"}),
        ("wipe_steep", "energy", {"type": "wipe", "angle_deg": 55, "duration_sec": 0.3, "easing": "expo_out"}),
        ("wipe_reverse_diag", "general", {"type": "wipe", "angle_deg": -35, "duration_sec": 0.35, "easing": "ease_in_out"}),
        ("slide_up", "general", {"type": "slide", "direction": "up", "duration_sec": 0.35, "easing": "expo_out"}),
        ("slide_down", "general", {"type": "slide", "direction": "down", "duration_sec": 0.35, "easing": "expo_out"}),
        ("slide_left", "general", {"type": "slide", "direction": "left", "duration_sec": 0.35, "easing": "expo_out"}),
        ("slide_right", "general", {"type": "slide", "direction": "right", "duration_sec": 0.35, "easing": "expo_out"}),
        ("iris_circle", "storytelling reveal", {"type": "iris", "shape": "circle", "duration_sec": 0.45, "easing": "ease_in_out"}),
        ("iris_circle_character", "storytelling reveal", {"type": "iris", "shape": "circle", "cx": 0.6, "cy": 0.6, "duration_sec": 0.45, "easing": "ease_out"}),
        ("iris_diamond", "game reveal", {"type": "iris", "shape": "diamond", "duration_sec": 0.4, "easing": "ease_out"}),
        ("iris_star", "celebration magic", {"type": "iris", "shape": "star", "duration_sec": 0.5, "easing": "ease_out", "color": "#fde047"}),
        ("iris_heart", "love relationships", {"type": "iris", "shape": "heart", "duration_sec": 0.55, "easing": "ease_out", "color": "#f472b6"}),
        ("iris_square", "tech", {"type": "iris", "shape": "square", "duration_sec": 0.35, "easing": "expo_out"}),
        ("dip_to_black", "storytelling calm sad", {"type": "dip", "color": "#000000", "duration_sec": 0.6, "easing": "ease_in_out"}),
        ("dip_to_white", "dream magic", {"type": "dip", "color": "#ffffff", "duration_sec": 0.5, "easing": "ease_in_out"}),
        ("dip_to_brand", "general", {"type": "dip", "color": "#1e3a8a", "duration_sec": 0.45, "easing": "ease_in_out"}),
        ("spin_in_cw", "comedy energy", {"type": "spin", "degrees": 180, "direction": "cw", "duration_sec": 0.45, "easing": "expo_out"}),
        ("spin_in_ccw", "comedy energy", {"type": "spin", "degrees": 360, "direction": "ccw", "duration_sec": 0.55, "easing": "expo_out"}),
        ("blinds_vertical", "tech general", {"type": "blinds", "count": 7, "orientation": "vertical", "duration_sec": 0.4, "easing": "ease_in_out"}),
        ("blinds_horizontal", "general", {"type": "blinds", "count": 9, "orientation": "horizontal", "duration_sec": 0.4, "easing": "ease_in_out"}),
        ("barn_door_open", "reveal", {"type": "barn_door", "orientation": "horizontal", "duration_sec": 0.4, "easing": "expo_out"}),
        ("barn_door_vertical", "reveal", {"type": "barn_door", "orientation": "vertical", "duration_sec": 0.4, "easing": "expo_out"}),
        ("glitch_cut", "tech security mystery", {"type": "glitch", "duration_sec": 0.3, "easing": "linear"}),
        ("glitch_long", "tech gaming", {"type": "glitch", "duration_sec": 0.5, "easing": "ease_out"}),
        ("flash_cut", "impact emphasis", {"type": "flash", "duration_sec": 0.25, "easing": "ease_out"}),
        ("flash_red_cut", "danger impact", {"type": "flash", "color": "#ef4444", "duration_sec": 0.25, "easing": "ease_out"}),
        ("pop_in", "comedy kids", {"type": "pop", "duration_sec": 0.45, "easing": "linear"}),
        ("slice_split", "energy gaming", {"type": "slice", "duration_sec": 0.35, "easing": "expo_out"}),
        ("hard_cut", "general", {"type": "fade", "duration_sec": 0.02, "easing": "linear"}),
    ]
    return _items(T, "transition/v1")


# =========================================================================== caption styles
def caption_styles() -> List[Dict[str, Any]]:
    base = {"font": "DejaVu Sans Bold", "size_ratio": 0.065, "case": "upper", "max_words_per_line": 3, "position_y": 0.68, "inactive_color": "#ffffff",
            "active_word": {"color": "#facc15", "scale_pop": 1.15, "pop_ms": 90}, "stroke": {"color": "#000000", "width_ratio": 0.012}}

    def c(cid, tags, **kw):
        d = {**base, **{k: v for k, v in kw.items() if k not in ("active_word", "stroke")}}
        d["active_word"] = {**base["active_word"], **kw.get("active_word", {})}
        if "stroke" in kw:
            d["stroke"] = kw["stroke"]
        return (cid, tags, d)

    C = [
        c("pop_green", "general finance", active_word={"color": "#22c55e"}),
        c("pop_cyan", "general tech", active_word={"color": "#22d3ee"}),
        c("pop_pink", "general love", active_word={"color": "#f472b6"}),
        c("pop_orange", "general food", active_word={"color": "#fb923c"}),
        c("pop_red", "general danger", active_word={"color": "#ef4444"}),
        c("karaoke_box_yellow", "general", inactive_color="#ffffff", active_word={"color": "#0f172a", "box": {"color": "#facc15", "radius": 0.2}}),
        c("karaoke_box_purple", "general", active_word={"color": "#ffffff", "box": {"color": "#7c3aed", "radius": 0.25}}),
        c("karaoke_box_green", "finance general", active_word={"color": "#052e16", "box": {"color": "#4ade80", "radius": 0.2}}),
        c("karaoke_box_red", "general", active_word={"color": "#ffffff", "box": {"color": "#dc2626", "radius": 0.1}}),
        c("lowercase_soft", "calm storytelling", case="sentence", size_ratio=0.058, active_word={"color": "#fde68a", "scale_pop": 1.06}, stroke={"color": "#0f172a", "width_ratio": 0.008}),
        c("big_one_word", "energy motivation", max_words_per_line=1, size_ratio=0.11, active_word={"color": "#facc15", "scale_pop": 1.25, "pop_ms": 120}),
        c("two_words_punchy", "energy general", max_words_per_line=2, size_ratio=0.085),
        c("four_words_clean", "education calm", max_words_per_line=4, size_ratio=0.05, case="sentence", active_word={"color": "#38bdf8", "scale_pop": 1.0, "pop_ms": 0}),
        c("shadow_white", "general", stroke=None, shadow={"color": "#000000", "dx": 0.06, "dy": 0.08, "opacity": 0.75}),
        c("shadow_cream", "storytelling history", inactive_color="#fef3c7", stroke=None, shadow={"color": "#451a03", "dx": 0.05, "dy": 0.07, "opacity": 0.8},
          active_word={"color": "#f59e0b"}),
        c("mono_terminal", "tech coding", font="DejaVu Sans Mono Bold", case="lower", inactive_color="#86efac", active_word={"color": "#ffffff", "box": {"color": "#166534", "radius": 0.05}},
          stroke={"color": "#052e16", "width_ratio": 0.01}),
        c("mono_hacker_red", "security tech", font="DejaVu Sans Mono Bold", inactive_color="#fecaca", active_word={"color": "#ef4444"}),
        c("serif_classic", "history storytelling stoicism", font="DejaVu Serif Bold", case="sentence", inactive_color="#f8fafc", active_word={"color": "#fbbf24", "scale_pop": 1.08}),
        c("serif_elegant_box", "luxury storytelling", font="DejaVu Serif Bold", case="sentence", active_word={"color": "#1c1917", "box": {"color": "#fde68a", "radius": 0.15}}),
        c("bar_dark_clean", "general business", stroke=None, background={"color": "#0f172a", "opacity": 0.75}, case="sentence", size_ratio=0.055,
          active_word={"color": "#38bdf8", "scale_pop": 1.0, "pop_ms": 0}),
        c("bar_white_news", "media general", stroke=None, inactive_color="#0f172a", background={"color": "#ffffff", "opacity": 0.92}, active_word={"color": "#dc2626", "scale_pop": 1.0}),
        c("high_position", "general", position_y=0.22),
        c("low_position", "general", position_y=0.86, size_ratio=0.058),
        c("mid_position_big", "energy", position_y=0.5, size_ratio=0.09, max_words_per_line=2),
        c("kids_bubbly", "kids comedy", case="sentence", size_ratio=0.075, inactive_color="#fef08a", active_word={"color": "#f472b6", "scale_pop": 1.3, "pop_ms": 150},
          stroke={"color": "#4c1d95", "width_ratio": 0.016}),
        c("thick_outline_comic", "comedy", size_ratio=0.08, stroke={"color": "#000000", "width_ratio": 0.022}, active_word={"color": "#fde047", "scale_pop": 1.2}),
        c("minimal_gray", "calm education", case="sentence", inactive_color="#cbd5e1", stroke=None, active_word={"color": "#ffffff", "scale_pop": 1.0, "pop_ms": 0}, size_ratio=0.052),
        c("neon_violet", "gaming music", inactive_color="#e9d5ff", active_word={"color": "#22d3ee", "scale_pop": 1.18}, stroke={"color": "#4c1d95", "width_ratio": 0.014}),
        c("health_calm_teal", "health medical", case="sentence", inactive_color="#f0fdfa", active_word={"color": "#2dd4bf", "scale_pop": 1.06}, stroke={"color": "#134e4a", "width_ratio": 0.01}),
        c("money_gold_box", "finance crypto", active_word={"color": "#1c1917", "box": {"color": "#fbbf24", "radius": 0.18}}, inactive_color="#fef3c7"),
    ]
    return _items(C, "caption_style/v1")


# =========================================================================== themes
def themes() -> List[Dict[str, Any]]:
    P = [
        ("midnight_blue", "general", ("#0f172a", "#1e293b", "#e2e8f0", "#f8fafc", "#38bdf8", "#818cf8", "#fde047", "#f87171")),
        ("forest_green", "nature health", ("#052e16", "#14532d", "#dcfce7", "#f0fdf4", "#4ade80", "#a3e635", "#fde047", "#f87171")),
        ("sunset_orange", "storytelling", ("#431407", "#7c2d12", "#ffedd5", "#fff7ed", "#fb923c", "#f472b6", "#fde047", "#ef4444")),
        ("royal_purple", "luxury magic", ("#2e1065", "#4c1d95", "#ede9fe", "#faf5ff", "#c084fc", "#f472b6", "#fde047", "#fb7185")),
        ("ocean_teal", "ocean calm", ("#042f2e", "#115e59", "#ccfbf1", "#f0fdfa", "#2dd4bf", "#38bdf8", "#fde68a", "#fb7185")),
        ("crimson_bold", "danger energy", ("#450a0a", "#7f1d1d", "#fee2e2", "#fff1f2", "#f87171", "#fb923c", "#fde047", "#ffffff")),
        ("money_green", "finance money", ("#022c22", "#064e3b", "#d1fae5", "#ecfdf5", "#34d399", "#fbbf24", "#fde047", "#f87171")),
        ("crypto_neon", "crypto web3 tech", ("#0b0b1a", "#1e1b4b", "#e0e7ff", "#f5f3ff", "#a78bfa", "#22d3ee", "#facc15", "#f43f5e")),
        ("hospital_clean", "health medical", ("#0c4a6e", "#075985", "#e0f2fe", "#f0f9ff", "#2dd4bf", "#38bdf8", "#fde68a", "#f87171")),
        ("chalk_school", "education", ("#14532d", "#166534", "#f0fdf4", "#ffffff", "#fde047", "#93c5fd", "#fca5a5", "#f87171")),
        ("paper_warm", "storytelling history", ("#fef3c7", "#fde68a", "#78350f", "#451a03", "#b45309", "#be185d", "#dc2626", "#991b1b")),
        ("newspaper_bw", "media history", ("#f5f5f4", "#e7e5e4", "#292524", "#0c0a09", "#57534e", "#a8a29e", "#dc2626", "#991b1b")),
        ("cyber_pink", "gaming tech", ("#1a0b2e", "#3b0764", "#fae8ff", "#fdf4ff", "#f472b6", "#22d3ee", "#facc15", "#fb7185")),
        ("stoic_stone", "stoicism self_improvement", ("#1c1917", "#292524", "#e7e5e4", "#fafaf9", "#d6a76c", "#a8a29e", "#fbbf24", "#f87171")),
        ("kids_candy", "kids comedy", ("#fdf2f8", "#fce7f3", "#831843", "#500724", "#ec4899", "#8b5cf6", "#f59e0b", "#ef4444")),
        ("space_deep", "space science", ("#020617", "#0f172a", "#c7d2fe", "#eef2ff", "#818cf8", "#f472b6", "#fde047", "#fb7185")),
        ("desert_sand", "travel history", ("#451a03", "#78350f", "#fef3c7", "#fffbeb", "#f59e0b", "#ea580c", "#fde047", "#ef4444")),
        ("arctic_frost", "nature weather", ("#082f49", "#0c4a6e", "#e0f2fe", "#f0f9ff", "#7dd3fc", "#e0e7ff", "#fde68a", "#f87171")),
        ("coffee_shop", "food relaxation", ("#1c0f0a", "#3f2a1d", "#f5e6d3", "#fffaf0", "#d6a76c", "#f59e0b", "#fde68a", "#ef4444")),
        ("fitness_lime", "fitness sports", ("#0a0a0a", "#171717", "#e5e5e5", "#fafafa", "#a3e635", "#22d3ee", "#facc15", "#ef4444")),
        ("law_navy_gold", "law business", ("#0b1736", "#1e2a4f", "#e2e8f0", "#f8fafc", "#d4af37", "#94a3b8", "#fde68a", "#f87171")),
        ("mint_fresh", "health food", ("#f0fdf4", "#dcfce7", "#14532d", "#052e16", "#10b981", "#0ea5e9", "#f59e0b", "#ef4444")),
        ("light_minimal", "business education", ("#f8fafc", "#e2e8f0", "#334155", "#0f172a", "#2563eb", "#db2777", "#d97706", "#dc2626")),
        ("halloween", "spooky holiday", ("#0c0a09", "#1c1917", "#fed7aa", "#fff7ed", "#f97316", "#a855f7", "#84cc16", "#ef4444")),
        ("festive_red_green", "holiday celebration", ("#14532d", "#7f1d1d", "#fef2f2", "#ffffff", "#ef4444", "#22c55e", "#fde047", "#f87171")),
        ("mono_dark", "general tech", ("#0a0a0a", "#171717", "#d4d4d4", "#fafafa", "#a3a3a3", "#e5e5e5", "#fde047", "#ef4444")),
        ("lavender_calm", "mental_health calm", ("#2e1065", "#3b0764", "#f3e8ff", "#faf5ff", "#c4b5fd", "#f9a8d4", "#fde68a", "#fda4af")),
        ("trader_terminal", "trading finance", ("#030712", "#111827", "#d1d5db", "#f9fafb", "#22c55e", "#ef4444", "#facc15", "#ef4444")),
    ]
    keys = ("bg", "surface", "line", "text", "accent", "accent2", "highlight", "danger")
    return _items([(tid, tags, {"palette": dict(zip(keys, cols))}) for tid, tags, cols in P], "theme/v1")


# =========================================================================== voices (Gemini prebuilt voices)
GEMINI_VOICE_STYLES = {
    "Zephyr": "Bright", "Puck": "Upbeat", "Charon": "Informative", "Kore": "Firm", "Fenrir": "Excitable", "Leda": "Youthful", "Orus": "Firm",
    "Aoede": "Breezy", "Callirrhoe": "Easy-going", "Autonoe": "Bright", "Enceladus": "Breathy", "Iapetus": "Clear", "Umbriel": "Easy-going",
    "Algieba": "Smooth", "Despina": "Smooth", "Erinome": "Clear", "Algenib": "Gravelly", "Rasalgethi": "Informative", "Laomedeia": "Upbeat",
    "Achernar": "Soft", "Alnilam": "Firm", "Schedar": "Even", "Gacrux": "Mature", "Pulcherrima": "Forward", "Achird": "Friendly",
    "Zubenelgenubi": "Casual", "Vindemiatrix": "Gentle", "Sadachbia": "Lively", "Sadaltager": "Knowledgeable", "Sulafat": "Warm",
}

_PERSONAS = [
    ("bright_zephyr", "Zephyr", "Bright, curious and clear; light smile in the voice.", "science education"),
    ("upbeat_puck", "Puck", "Upbeat and playful; quick timing, punchy endings.", "comedy kids gaming"),
    ("informative_charon", "Charon", "Calm documentary narrator; measured and confident.", "history science storytelling"),
    ("firm_kore", "Kore", "Firm, precise and assured; crisp consonants.", "business finance"),
    ("excited_fenrir", "Fenrir", "Excitable and energetic; big emphasis on key words.", "fitness motivation sports"),
    ("youthful_leda", "Leda", "Youthful and earnest; friendly curiosity.", "education career"),
    ("firm_orus", "Orus", "Firm and grounded; steady authority.", "law business"),
    ("breezy_aoede", "Aoede", "Breezy and warm; relaxed storytelling.", "storytelling travel art"),
    ("easy_callirrhoe", "Callirrhoe", "Easy-going and friendly; conversational.", "food home agriculture"),
    ("bright_autonoe", "Autonoe", "Bright and cheerful; light and quick.", "kids celebration"),
    ("breathy_enceladus", "Enceladus", "Breathy and intimate; suspense in the pauses.", "mystery spooky"),
    ("clear_iapetus", "Iapetus", "Clear and neutral; easy to follow.", "health medical tech"),
    ("easy_umbriel", "Umbriel", "Easy-going and casual; relatable.", "productivity comedy"),
    ("smooth_algieba", "Algieba", "Smooth and polished; premium feel.", "luxury finance trading"),
    ("smooth_despina", "Despina", "Smooth and soothing; gentle warmth.", "mental_health relationships"),
    ("clear_erinome", "Erinome", "Clear and articulate; slightly robotic precision.", "ai tech"),
    ("gravel_algenib", "Algenib", "Gravelly and rugged; tough and dramatic.", "construction history adventure"),
    ("informative_rasalgethi", "Rasalgethi", "Informative newsreader; brisk and factual.", "media communication"),
    ("upbeat_laomedeia", "Laomedeia", "Upbeat and musical; rhythmic phrasing.", "music entertainment"),
    ("soft_achernar", "Achernar", "Soft and calm; slow and kind.", "mental_health sleep"),
    ("firm_alnilam", "Alnilam", "Firm coach voice; clear instructions.", "fitness education"),
    ("even_schedar", "Schedar", "Even and steady; corporate clarity.", "business office"),
    ("mature_gacrux", "Gacrux", "Mature and wise; grandparent warmth.", "history stoicism family"),
    ("forward_pulcherrima", "Pulcherrima", "Forward and confident; persuasive.", "marketing sales travel"),
    ("friendly_achird", "Achird", "Friendly and reassuring; bedside manner.", "health medical"),
    ("casual_zubenelgenubi", "Zubenelgenubi", "Casual and cheeky; insider tone.", "crypto web3 comedy"),
    ("gentle_vindemiatrix", "Vindemiatrix", "Gentle and patient; teacherly.", "education stoicism"),
    ("lively_sadachbia", "Sadachbia", "Lively and expressive; big reactions.", "food entertainment"),
    ("knowledge_sadaltager", "Sadaltager", "Knowledgeable explainer; dry wit.", "tech coding science"),
    ("warm_sulafat", "Sulafat", "Warm and caring; trustworthy.", "health family holiday"),
    ("hype_fenrir_shout", "Fenrir", "Hype host energy; shouts the payoff word.", "gaming sports celebration"),
    ("whisper_enceladus", "Enceladus", "Near-whisper secret-telling; tension.", "mystery spooky"),
    ("deadpan_charon", "Charon", "Deadpan, unimpressed delivery for jokes.", "comedy"),
    ("story_aoede_slow", "Aoede", "Slow bedtime-story pacing; soft smiles.", "storytelling kids sleep"),
    ("coach_kore_push", "Kore", "Tough-love coach; short, punchy commands.", "fitness motivation"),
    ("news_rasalgethi_urgent", "Rasalgethi", "Urgent breaking-news cadence.", "media danger"),
    ("trader_algieba_fast", "Algieba", "Fast trader floor patter; numbers crisp.", "trading crypto finance"),
    ("doctor_achird_calm", "Achird", "Calm doctor explaining clearly; reassuring.", "health medical"),
    ("teacher_vindemiatrix_bright", "Vindemiatrix", "Bright classroom teacher; checks understanding.", "education kids"),
    ("villain_algenib_low", "Algenib", "Low villain drawl; slow menace.", "storytelling comedy spooky"),
]


def voices(model: str = "gemini-3.8-flash-tts") -> List[Dict[str, Any]]:
    out = []
    for vid, name, style, tags in _PERSONAS:
        out.append({"id": vid, "tags": tags.split(), "gemini_voice_name": name,
                    "json": {"id": vid, "format": "voice_persona/v1", "type": "prebuilt", "gemini_voice_name": name, "tts_model": model,
                             "default_style": style, "voice_character": GEMINI_VOICE_STYLES.get(name, ""), "pace_multiplier": 1.0}})
    return out
