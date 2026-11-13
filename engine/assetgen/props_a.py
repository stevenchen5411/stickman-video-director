"""Props, part A: symbols & badges, money & finance, crypto, business, tech & devices."""
from __future__ import annotations

import math

from .kit import *  # noqa: F401,F403
from .registry import P

# =========================================================================== symbols & badges (global)
P("check_badge", "general", lambda: [circle(128, 128, 100, GREEN), hl_ellipse(95, 85, 40, 22, rot=-30),
                                     pline([(80, 130), (114, 164), (178, 94)], WHITE, 22)])
P("cross_badge", "general", lambda: [circle(128, 128, 100, RED), hl_ellipse(95, 85, 40, 22, rot=-30),
                                     line(88, 88, 168, 168, WHITE, 22), line(168, 88, 88, 168, WHITE, 22)])
P("question_badge", "general", lambda: [circle(128, 128, 100, BLUE), hl_ellipse(95, 85, 40, 22, rot=-30),
                                        text(128, 168, "?", 130, WHITE)])
P("exclamation_badge", "general", lambda: [circle(128, 128, 100, ORANGE), hl_ellipse(95, 85, 40, 22, rot=-30),
                                           text(128, 170, "!", 140, WHITE)])
P("warning_sign", "general safety", lambda: [poly([(128, 26), (236, 214), (20, 214)], YELLOW, sw=9),
                                             text(128, 196, "!", 130, OUT)])
P("stop_sign", "general transport", lambda: [poly(reg_pts(128, 128, 108, 8, -67.5), RED, sw=9),
                                             poly(reg_pts(128, 128, 90, 8, -67.5), "none", WHITE, 6),
                                             text(128, 148, "STOP", 56, WHITE)])
P("no_symbol", "general", lambda: [circle(128, 128, 98, WHITE, RED, 26), line(60, 196, 196, 60, RED, 26)])
P("plus_sign", "general", lambda: [rect(102, 30, 52, 196, GREEN, 14), rect(30, 102, 196, 52, GREEN, 14),
                                   rect(108, 36, 40, 184, GREEN, 10, None)])
P("minus_sign", "general", lambda: [rect(30, 100, 196, 56, RED, 16)])
P("percent_sign", "general finance", lambda: [line(196, 48, 60, 208, OUT, 34), line(196, 48, 60, 208, PURPLE, 20),
                                              circle(74, 74, 38, PURPLE, sw=9), circle(182, 182, 38, PURPLE, sw=9)])
P("dollar_sign", "finance money", lambda: [text(128, 204, "$", 210, GREEN, stroke=OUT, sw=8)])
P("infinity_sign", "general", lambda: [path("M128,128 C98,76 34,84 34,128 C34,172 98,180 128,128 C158,76 222,84 222,128 "
                                            "C222,172 158,180 128,128 Z", "none", OUT, 34),
                                       path("M128,128 C98,76 34,84 34,128 C34,172 98,180 128,128 C158,76 222,84 222,128 "
                                            "C222,172 158,180 128,128 Z", "none", VIOLET, 20)])
P("arrow_up", "general growth", lambda: [poly(arrow_pts(128, 230, 128, 26, 60, 92), GREEN, sw=9)])
P("arrow_down", "general decline", lambda: [poly(arrow_pts(128, 26, 128, 230, 60, 92), RED, sw=9)])
P("arrow_right", "general", lambda: [poly(arrow_pts(24, 128, 232, 128, 60, 92), BLUE, sw=9)])
P("arrow_left", "general", lambda: [poly(arrow_pts(232, 128, 24, 128, 60, 92), BLUE, sw=9)])
P("arrow_trend_up", "general finance growth", lambda: [pline([(26, 200), (92, 134), (136, 170), (214, 74)], OUT, 34),
                                                       pline([(26, 200), (92, 134), (136, 170), (214, 74)], GREEN, 20),
                                                       poly([(230, 50), (230, 120), (166, 60)], GREEN, sw=8)])
P("arrow_trend_down", "general finance decline", lambda: [pline([(26, 60), (92, 126), (136, 92), (214, 186)], OUT, 34),
                                                          pline([(26, 60), (92, 126), (136, 92), (214, 186)], RED, 20),
                                                          poly([(230, 210), (230, 140), (166, 200)], RED, sw=8)])
def _refresh():
    a1 = math.radians(320)
    ex, ey = 128 + 80 * math.cos(a1), 128 + 80 * math.sin(a1)
    tx, ty = -math.sin(a1), math.cos(a1)  # tangent (direction of travel, clockwise)
    nx, ny = math.cos(a1), math.sin(a1)
    head = [(ex + tx * 34, ey + ty * 34), (ex + nx * 30 - tx * 6, ey + ny * 30 - ty * 6), (ex - nx * 30 - tx * 6, ey - ny * 30 - ty * 6)]
    return [path(arc_d(128, 128, 80, 40, 320), "none", OUT, 38), path(arc_d(128, 128, 80, 40, 320), "none", TEAL, 24), poly(head, TEAL, sw=7)]


P("refresh_cycle", "general", _refresh)
P("star_gold", "general rating", lambda: [poly(star_pts(128, 134, 112, 48), GOLD, sw=9), hl("M96,96 L128,40 L140,80 Z")])
P("five_stars", "general rating review", lambda: [poly(star_pts(32 + i * 48, 128, 26, 11), GOLD if i < 4 else SILVER, sw=5)
                                                  for i in range(5)])
P("heart_red", "general love health", lambda: [path(heart_d(128, 128, 100), RED, sw=9), hl_ellipse(86, 86, 24, 14, rot=-40)])
P("heart_broken", "relationships love", lambda: [path(heart_d(128, 128, 100), RED, sw=9),
                                                 pline([(128, 60), (110, 104), (142, 134), (116, 176), (128, 216)], OUT, 12)])
P("thumbs_up", "general social_media", lambda: [rect(26, 112, 50, 110, BLUE, 10),
                                               path("M84,112 L118,40 C130,24 156,34 150,58 L142,96 L206,96 C226,96 232,118 222,132 "
                                                    "C232,144 226,162 214,164 C222,178 212,196 198,196 C204,210 192,222 178,222 L84,222 Z", AMBER)])
P("thumbs_down", "general social_media", lambda: [g([rect(26, 112, 50, 110, RED, 10),
                                                     path("M84,112 L118,40 C130,24 156,34 150,58 L142,96 L206,96 C226,96 232,118 222,132 "
                                                          "C232,144 226,162 214,164 C222,178 212,196 198,196 C204,210 192,222 178,222 L84,222 Z", AMBER)],
                                                    "rotate(180 128 128)")])
P("fire_flame", "general trending energy", lambda: [path("M128,20 C170,70 214,104 204,160 C196,206 162,236 128,236 C88,236 52,206 52,160 "
                                                        "C52,124 76,104 92,80 C98,110 110,120 120,124 C112,86 116,50 128,20 Z", ORANGE, sw=8),
                                                   path("M128,110 C150,138 170,154 166,184 C162,208 146,222 128,222 C108,222 92,206 92,184 "
                                                        "C92,162 112,150 128,110 Z", YELLOW, None)])
P("sparkles", "general magic new", lambda: [poly(star_pts(110, 130, 86, 22, 4, 0), YELLOW, sw=7),
                                            poly(star_pts(196, 60, 40, 10, 4, 0), YELLOW, sw=6), poly(star_pts(200, 196, 30, 8, 4, 0), YELLOW, sw=5)])
P("lightning_bolt", "general energy", lambda: [poly(bolt_pts(128, 128, 108), YELLOW, sw=9)])
P("target_bullseye", "general business goal", lambda: [circle(128, 128, 104, RED), circle(128, 128, 76, WHITE), circle(128, 128, 48, RED),
                                                      circle(128, 128, 20, WHITE), line(128, 128, 214, 42, OUT, 14),
                                                      poly([(214, 42), (240, 50), (222, 30)], AMBER, sw=6), circle(128, 128, 8, OUT, None)])
P("magnifying_glass", "general search research", lambda: [line(160, 160, 222, 222, OUT, 30), line(160, 160, 222, 222, BROWN_L, 18),
                                                          circle(108, 108, 74, GLASS, sw=14), hl_ellipse(84, 84, 26, 14, 0.6, -40)])
P("hourglass", "general time", lambda: [rect(50, 22, 156, 26, BROWN_L, 8), rect(50, 208, 156, 26, BROWN_L, 8),
                                        path("M70,48 L186,48 C186,104 140,116 140,128 C140,140 186,152 186,208 L70,208 C70,152 116,140 116,128 "
                                             "C116,116 70,104 70,48 Z", GLASS),
                                        path("M92,76 L164,76 C160,100 132,112 128,124 C124,112 96,100 92,76 Z", SAND, None),
                                        path("M128,150 L172,200 L84,200 Z", SAND, None)])
P("hundred_badge", "general social_media", lambda: [text(128, 150, "100", 104, RED, stroke=OUT, sw=6),
                                                     line(40, 178, 216, 178, RED, 12), line(52, 198, 204, 198, RED, 10)])
P("new_badge", "general marketing", lambda: [poly(star_pts(128, 128, 112, 88, 14), RED, sw=7), text(128, 146, "NEW", 52, WHITE)])
P("sale_badge", "shopping marketing", lambda: [poly(star_pts(128, 128, 112, 90, 16), YELLOW, sw=7), text(128, 124, "SALE", 46, RED),
                                               text(128, 168, "-50%", 38, OUT)])
P("number_one", "general winner", lambda: [circle(128, 128, 100, GOLD), circle(128, 128, 78, YELLOW, None),
                                           text(128, 172, "1", 128, WHITE, stroke=OUT, sw=7)])
P("speech_bubble", "general communication", lambda: [path("M40,40 L216,40 C230,40 236,50 236,62 L236,150 C236,164 226,172 214,172 L110,172 "
                                                         "L64,220 L72,172 L42,172 C28,172 20,162 20,150 L20,62 C20,50 28,40 40,40 Z", WHITE),
                                                    circle(84, 106, 13, GRAY_D, None), circle(128, 106, 13, GRAY_D, None), circle(172, 106, 13, GRAY_D, None)])
P("thought_cloud", "general thinking", lambda: [path(cloud_d(132, 104, 92), WHITE), circle(70, 196, 16, WHITE), circle(42, 228, 10, WHITE)])
P("lock_closed", "security tech", lambda: [path("M76,112 L76,80 C76,46 100,26 128,26 C156,26 180,46 180,80 L180,112", "none", OUT, 30),
                                           path("M76,112 L76,80 C76,46 100,26 128,26 C156,26 180,46 180,80 L180,112", "none", SILVER, 16),
                                           rect(44, 108, 168, 128, GOLD, 18), circle(128, 160, 16, OUT, None), rect(121, 166, 14, 34, OUT, 4, None)])
P("lock_open", "security tech", lambda: [path("M76,112 L76,70 C76,36 100,18 128,18 C156,18 180,36 180,70 L180,80", "none", OUT, 30),
                                         path("M76,112 L76,70 C76,36 100,18 128,18 C156,18 180,36 180,70 L180,80", "none", SILVER, 16),
                                         rect(44, 108, 168, 128, GREEN, 18), circle(128, 160, 16, OUT, None), rect(121, 166, 14, 34, OUT, 4, None)])
P("key_gold", "security home general", lambda: [circle(76, 128, 52, GOLD), circle(76, 128, 20, WHITE), rect(120, 116, 116, 26, GOLD, 6),
                                               rect(186, 140, 18, 30, GOLD, 4), rect(214, 140, 18, 40, GOLD, 4)])
P("shield_check", "security tech", lambda: [path("M128,20 L222,52 C222,140 186,204 128,236 C70,204 34,140 34,52 Z", BLUE, sw=9),
                                            pline([(84, 128), (116, 160), (176, 96)], WHITE, 22)])
P("crown_gold", "general leader success", lambda: [poly([(28, 196), (36, 68), (88, 126), (128, 44), (168, 126), (220, 68), (228, 196)], GOLD, sw=9),
                                                   rect(28, 190, 200, 32, AMBER, 6), circle(128, 160, 14, RED), circle(76, 166, 10, BLUE), circle(180, 166, 10, GREEN)])
P("trophy_gold", "general winner sports", lambda: [path("M70,28 L186,28 L180,110 C176,146 152,164 128,164 C104,164 80,146 76,110 Z", GOLD, sw=9),
                                                   path("M72,52 C30,52 32,112 78,112", "none", OUT, 12), path("M184,52 C226,52 224,112 178,112", "none", OUT, 12),
                                                   rect(112, 162, 32, 36, AMBER, 4), rect(72, 196, 112, 34, BROWN, 8),
                                                   hl("M92,40 L104,40 L102,120 C96,112 92,96 92,40 Z")])
P("medal_gold", "general winner sports", lambda: [poly([(80, 20), (120, 20), (140, 110), (100, 110)], BLUE, sw=6),
                                                  poly([(176, 20), (136, 20), (116, 110), (156, 110)], RED, sw=6),
                                                  circle(128, 164, 66, GOLD, sw=9), circle(128, 164, 44, AMBER, None),
                                                  poly(star_pts(128, 166, 32, 14), YELLOW, sw=4)])
P("ribbon_award", "general winner education", lambda: [poly([(92, 130), (60, 236), (96, 214), (110, 244), (128, 140)], RED, sw=7),
                                                       poly([(164, 130), (196, 236), (160, 214), (146, 244), (128, 140)], RED, sw=7),
                                                       poly(star_pts(128, 100, 84, 70, 18), BLUE, sw=7), circle(128, 100, 52, WHITE),
                                                       text(128, 116, "1st", 40, BLUE)])
P("flag_goal", "general goal business", lambda: [rect(56, 24, 14, 216, GRAY_D, 6), path("M70,32 C110,12 150,52 214,32 L214,128 C150,148 110,108 70,128 Z", RED),
                                                 ellipse(63, 236, 40, 10, SLATE, None)])
P("location_pin", "general travel map", lambda: [path("M128,236 C92,176 46,138 46,92 C46,46 84,16 128,16 C172,16 210,46 210,92 C210,138 164,176 128,236 Z", RED, sw=9),
                                                 circle(128, 92, 34, WHITE)])
P("bell_notification", "general social_media tech", lambda: [path("M128,30 C84,30 64,64 64,104 L64,156 L40,190 L216,190 L192,156 L192,104 C192,64 172,30 128,30 Z", GOLD, sw=8),
                                                            circle(128, 204, 22, AMBER), circle(196, 54, 26, RED, sw=6), text(196, 66, "3", 32, WHITE)])
P("clock_wall", "general time", lambda: [circle(128, 128, 104, WHITE, sw=10), *[line(128 + 82 * math.cos(math.radians(a)), 128 + 82 * math.sin(math.radians(a)),
                                                                               128 + 92 * math.cos(math.radians(a)), 128 + 92 * math.sin(math.radians(a)), OUT, 6)
                                                                          for a in range(0, 360, 30)],
                                         line(128, 128, 128, 62, OUT, 10), line(128, 128, 176, 150, RED, 8), circle(128, 128, 9, OUT, None)])
P("stopwatch", "general time sports", lambda: [rect(110, 14, 36, 22, GRAY_D, 6), rect(118, 34, 20, 18, GRAY_D, 2), line(190, 56, 206, 40, OUT, 14),
                                               circle(128, 144, 92, SILVER, sw=9), circle(128, 144, 74, WHITE, None),
                                               path(pie_d(128, 144, 66, -90, 30), RED, None, op=0.85), line(128, 144, 128, 84, OUT, 8),
                                               circle(128, 144, 8, OUT, None)])
P("calendar_page", "general time business", lambda: [rect(30, 44, 196, 186, WHITE, 18), path("M30,62 C30,52 38,44 48,44 L208,44 C218,44 226,52 226,62 L226,96 L30,96 Z", RED),
                                                    rect(70, 22, 18, 44, GRAY_D, 8), rect(168, 22, 18, 44, GRAY_D, 8),
                                                    *[rect(54 + c * 40, 112 + r * 36, 26, 22, SILVER if (r, c) != (1, 2) else RED, 4, None)
                                                      for r in range(3) for c in range(4)]])
P("gear_cog", "general tech industry process", lambda: [poly([(128 + (104 if i % 4 < 2 else 80) * math.cos(math.radians(i * 11.25 - 5.6)),
                                                                 128 + (104 if i % 4 < 2 else 80) * math.sin(math.radians(i * 11.25 - 5.6))) for i in range(32)], GRAY, sw=8),
                                                        circle(128, 128, 36, SLATE)])
P("gears_pair", "general tech industry process", lambda: [poly([(96 + (80 if i % 4 < 2 else 60) * math.cos(math.radians(i * 11.25)),
                                                                   140 + (80 if i % 4 < 2 else 60) * math.sin(math.radians(i * 11.25))) for i in range(32)], AMBER, sw=7),
                                                          circle(96, 140, 24, WHITE),
                                                          poly([(186 + (54 if i % 4 < 2 else 40) * math.cos(math.radians(i * 15 + 7)),
                                                                 70 + (54 if i % 4 < 2 else 40) * math.sin(math.radians(i * 15 + 7))) for i in range(24)], TEAL, sw=6),
                                                          circle(186, 70, 16, WHITE)])
P("puzzle_piece", "general business strategy", lambda: [path("M40,72 L96,72 C90,40 150,40 144,72 L200,72 L200,124 C228,118 228,178 200,172 L200,224 L40,224 L40,172 "
                                                             "C68,178 68,118 40,124 Z", VIOLET, sw=8)])
P("light_bulb_on", "general idea creativity", lambda: [*[line(128 + 96 * math.cos(math.radians(a)), 104 + 96 * math.sin(math.radians(a)),
                                                               128 + 120 * math.cos(math.radians(a)), 104 + 120 * math.sin(math.radians(a)), AMBER, 10)
                                                          for a in range(180, 361, 30)],
                                                       path("M128,30 C170,30 196,62 196,100 C196,132 176,148 166,166 L90,166 C80,148 60,132 60,100 C60,62 86,30 128,30 Z", YELLOW, sw=8),
                                                       rect(90, 166, 76, 22, GRAY, 6), rect(96, 188, 64, 20, GRAY_D, 6), rect(110, 208, 36, 16, SLATE, 6),
                                                       hl("M96,70 C104,52 122,46 134,48 C116,56 104,70 100,92 Z")])
P("light_bulb_off", "general idea", lambda: [path("M128,30 C170,30 196,62 196,100 C196,132 176,148 166,166 L90,166 C80,148 60,132 60,100 C60,62 86,30 128,30 Z", SILVER, sw=8),
                                             path("M108,166 L108,120 L128,100 L148,120 L148,166", "none", GRAY_D, 6),
                                             rect(90, 166, 76, 22, GRAY, 6), rect(96, 188, 64, 20, GRAY_D, 6), rect(110, 208, 36, 16, SLATE, 6)])
P("megaphone", "marketing business communication", lambda: [poly([(40, 100), (176, 36), (176, 212), (40, 156)], RED, sw=9), rect(20, 96, 30, 64, SILVER, 8),
                                                            ellipse(176, 124, 26, 88, AMBER), path("M62,156 L78,210 L108,204 L96,164", WHITE),
                                                            *[line(212, 124 + d, 238, 124 + d * 2.2, OUT, 8) for d in (-30, 0, 30)]])
P("hashtag", "social_media marketing", lambda: [g([rect(84, 24, 26, 208, BLUE, 10), rect(146, 24, 26, 208, BLUE, 10),
                                                    rect(24, 84, 208, 26, BLUE, 10), rect(24, 146, 208, 26, BLUE, 10)], "skewX(-10) translate(22 0)")])
P("at_sign", "tech communication", lambda: [text(128, 184, "@", 200, TEAL, stroke=OUT, sw=6)])
P("chat_bubbles", "social_media communication", lambda: [path("M24,38 L160,38 C172,38 178,46 178,56 L178,116 C178,128 170,134 160,134 L74,134 L40,166 L46,134 "
                                                            "L42,134 C30,134 24,126 24,116 Z", BLUE),
                                                       path("M232,110 L104,110 C92,110 86,118 86,128 L86,182 C86,194 94,200 104,200 L184,200 L214,230 L210,200 "
                                                            "L214,200 C226,200 232,192 232,182 Z", WHITE),
                                                       *[circle(132 + i * 32, 156, 9, GRAY_D, None) for i in range(3)]])

# =========================================================================== money & finance
def coin(cx, cy, r, col, sym, sym_col=None):
    glyph = (btc_glyph(cx, cy, r * 1.0, sym_col or lighten(col, 0.6)) if sym == "BTC"
             else text(cx, cy + r * 0.36, sym, r * 1.0, sym_col or lighten(col, 0.6), stroke=OUT, sw=4))
    return [circle(cx, cy, r, col, sw=8), circle(cx, cy, r * 0.76, darken(col, 0.88), None), glyph]


P("coin_dollar", "finance money", lambda: coin(128, 128, 100, GOLD, "$"))
P("coin_euro", "finance money", lambda: coin(128, 128, 100, GOLD, "€"))
P("coin_yen", "finance money", lambda: coin(128, 128, 100, GOLD, "¥"))
P("coin_rupiah", "finance money", lambda: [circle(128, 128, 100, SILVER, sw=8), circle(128, 128, 76, darken(SILVER, 0.9), None),
                                          text(128, 152, "Rp", 74, WHITE, stroke=OUT, sw=4)])
P("coins_falling", "finance money", lambda: [*coin(84, 168, 58, GOLD, "$"), *coin(176, 92, 46, GOLD, "$"), *coin(196, 196, 34, GOLD, "$")])
P("banknote", "finance money", lambda: [rect(18, 64, 220, 128, GREEN, 12), rect(34, 80, 188, 96, "none", 6, WHITE, 4, op=0.5),
                                        circle(128, 128, 36, lighten(GREEN, 0.5)), text(128, 146, "$", 50, GREEN_D),
                                        text(58, 112, "100", 22, WHITE), text(198, 168, "100", 22, WHITE)])
P("cash_stack", "finance money", lambda: [*[rect(30, 150 - i * 22, 196, 70, GREEN if i % 2 == 0 else EMERALD, 10) for i in range(4)],
                                          rect(108, 84, 40, 70, AMBER, 2), text(128, 128, "$", 34, WHITE)])
P("money_bag", "finance money", lambda: [path("M96,64 C70,96 30,136 34,184 C38,224 82,236 128,236 C174,236 218,224 222,184 C226,136 186,96 160,64 Z", TAN, sw=9),
                                         path("M96,64 L82,26 L174,26 L160,64 Z", TAN, sw=8), rect(88, 56, 80, 18, BROWN, 6),
                                         text(128, 190, "$", 92, GREEN_D)])
P("wallet_brown", "finance money", lambda: [rect(24, 64, 208, 150, BROWN_L, 20), path("M24,96 L232,96", "none", OUT, 6),
                                            rect(150, 116, 92, 56, BROWN, 14), circle(178, 144, 10, GOLD), rect(52, 40, 120, 40, GREEN, 6)])
P("credit_card", "finance money shopping", lambda: [rect(16, 52, 224, 152, BLUE, 18), rect(16, 84, 224, 30, OUT, 0, None),
                                                    rect(36, 132, 46, 34, GOLD, 6), text(212, 188, "1234", 22, WHITE, anchor="end"),
                                                    circle(180, 156, 18, RED, None, op=0.9), circle(204, 156, 18, AMBER, None, op=0.9)])
P("piggy_bank", "finance money savings", lambda: [ellipse(122, 140, 96, 72, PINK, sw=9), circle(206, 132, 30, PINK, sw=8),
                                                  ellipse(214, 132, 12, 9, darken(PINK, 0.8), None), poly([(84, 76), (100, 40), (120, 74)], PINK, sw=7),
                                                  rect(72, 196, 24, 34, PINK, 6), rect(144, 196, 24, 34, PINK, 6), rect(104, 74, 44, 10, OUT, 4, None),
                                                  circle(172, 116, 7, OUT, None), path("M26,132 C10,124 12,104 26,108", "none", OUT, 7), *coin(126, 46, 26, GOLD, "$")])
P("safe_vault", "finance security", lambda: [rect(24, 28, 208, 196, GRAY, 16), rect(44, 48, 168, 156, SILVER, 10), circle(128, 126, 46, GRAY_D, sw=7),
                                             *[line(128, 126, 128 + 40 * math.cos(math.radians(a)), 126 + 40 * math.sin(math.radians(a)), OUT, 7) for a in (0, 90, 180, 270)],
                                             circle(128, 126, 12, GOLD), rect(40, 222, 34, 14, SLATE, 4), rect(182, 222, 34, 14, SLATE, 4)])
P("gold_bars", "finance investing", lambda: [*[poly([(x, y + 44), (x + 18, y), (x + 92, y), (x + 110, y + 44)], GOLD, sw=7)
                                               for x, y in ((20, 176), (126, 176), (72, 128))],
                                             *[hl(f"M{x + 26},{y + 8} L{x + 56},{y + 8} L{x + 50},{y + 22} L{x + 22},{y + 22} Z")
                                               for x, y in ((20, 176), (126, 176), (72, 128))]])
P("diamond_gem", "finance luxury", lambda: [poly([(64, 52), (192, 52), (234, 104), (128, 226), (22, 104)], SKY, sw=8),
                                            pline([(22, 104), (234, 104)], OUT, 5), pline([(64, 52), (96, 104), (128, 226), (160, 104), (192, 52)], OUT, 5),
                                            pline([(96, 104), (128, 52), (160, 104)], OUT, 5), hl("M70,60 L92,60 L80,96 L40,100 Z", 0.5)])
P("calculator", "finance education business", lambda: [rect(48, 18, 160, 220, SLATE, 18), rect(66, 38, 124, 50, "#a7f3d0", 8),
                                                       text(180, 76, "1,024", 30, OUT, anchor="end", family="DejaVu Sans Mono"),
                                                       *[rect(66 + c * 34, 104 + r * 32, 24, 22, (ORANGE if c == 3 else GRAY), 5, None)
                                                         for r in range(4) for c in range(4)]])
P("receipt_bill", "finance shopping", lambda: [path("M50,20 L206,20 L206,232 L188,218 L170,232 L152,218 L134,232 L116,218 L98,232 L80,218 L62,232 L50,222 Z", WHITE, sw=7),
                                               *[line(72, 54 + i * 26, 160 if i % 2 else 184, 54 + i * 26, GRAY, 8) for i in range(5)],
                                               line(72, 190, 184, 190, OUT, 6), text(184, 184, "$42", 26, OUT, anchor="end")])
P("bank_building", "finance business", lambda: [poly([(16, 92), (128, 22), (240, 92)], SILVER, sw=8), rect(26, 90, 204, 22, GRAY, 4),
                                                *[rect(42 + i * 46, 116, 26, 86, WHITE, 4) for i in range(4)], rect(20, 202, 216, 18, GRAY, 4),
                                                rect(10, 220, 236, 18, GRAY_D, 4), circle(128, 64, 16, GOLD)])
P("atm_machine", "finance", lambda: [rect(44, 20, 168, 220, BLUE, 16), rect(64, 40, 128, 74, "#0b1d33", 8), text(128, 86, "ATM", 30, CYAN),
                                     *[rect(70 + c * 30, 126 + r * 22, 22, 14, SILVER, 3, None) for r in range(3) for c in range(4)],
                                     rect(78, 200, 100, 14, OUT, 4, None), rect(96, 206, 64, 30, GREEN, 4)])
P("cash_register", "finance shopping business", lambda: [rect(26, 114, 204, 112, GRAY_D, 14), rect(40, 60, 120, 60, SLATE, 10), rect(52, 72, 96, 34, "#a7f3d0", 6),
                                                        text(140, 98, "$9.99", 22, OUT, anchor="end"),
                                                        *[rect(48 + c * 34, 134 + r * 26, 24, 16, SILVER, 4, None) for r in range(2) for c in range(5)],
                                                        rect(26, 196, 204, 34, SLATE, 8), rect(170, 70, 56, 44, GREEN, 6)])
P("chart_bar_up", "finance business growth", lambda: [line(28, 224, 232, 224, OUT, 9), *[rect(40 + i * 48, 196 - h, 36, h + 28, c, 6)
                                                                                         for i, (h, c) in enumerate(((40, SKY), (80, BLUE), (120, INDIGO), (170, GREEN)))]])
P("chart_bar_down", "finance business decline", lambda: [line(28, 224, 232, 224, OUT, 9), *[rect(40 + i * 48, 196 - h, 36, h + 28, c, 6)
                                                                                             for i, (h, c) in enumerate(((170, AMBER), (120, ORANGE), (80, RED), (40, RED_D)))]])
P("chart_pie", "finance business data", lambda: [path(pie_d(124, 132, 100, -90, 130), BLUE), path(pie_d(124, 132, 100, 130, 230), AMBER),
                                                 path(pie_d(138, 120, 100, 230, 270), RED)])
P("chart_line_up", "finance business growth investing", lambda: [rect(16, 28, 224, 200, WHITE, 16), *[line(36, 70 + i * 40, 220, 70 + i * 40, SILVER, 4) for i in range(4)],
                                                               pline([(40, 186), (82, 150), (120, 164), (160, 104), (212, 60)], GREEN, 14),
                                                               circle(212, 60, 12, GREEN, sw=5)])
P("candlestick_chart", "finance crypto investing trading", lambda: [rect(12, 20, 232, 216, INK, 16),
                                                                   *[g([line(x, y - h * 0.4, x, y + h * 1.3, c, 5), rect(x - 12, y, 24, h, c, 3, c, 2)])
                                                                     for x, y, h, c in ((44, 150, 46, RED), (82, 124, 40, GREEN), (120, 100, 34, GREEN),
                                                                                        (158, 116, 44, RED), (196, 64, 60, GREEN))]])
P("stock_ticker", "finance investing trading", lambda: [rect(10, 70, 236, 116, INK, 14), text(26, 118, "NEAR", 28, WHITE, anchor="start", family="DejaVu Sans Mono"),
                                                        text(26, 160, "+12.4%", 32, "#4ade80", anchor="start", family="DejaVu Sans Mono"),
                                                        poly([(206, 108), (226, 136), (186, 136)], "#4ade80", None)])
P("bull_market", "finance investing trading", lambda: [ellipse(128, 150, 92, 58, BROWN_L, sw=8), circle(200, 120, 38, BROWN_L, sw=8),
                                                       path("M186,90 C176,60 196,44 214,50", "none", OUT, 14), path("M220,92 C234,66 224,46 206,40", "none", OUT, 14),
                                                       path("M186,90 C176,60 196,44 214,50", "none", CREAM, 7), path("M220,92 C234,66 224,46 206,40", "none", CREAM, 7),
                                                       *[rect(x, 192, 18, 44, BROWN_L, 6) for x in (60, 94, 150, 180)], circle(212, 116, 6, OUT, None),
                                                       ellipse(222, 136, 14, 10, darken(BROWN_L, 0.8), None), poly(arrow_pts(30, 90, 120, 40, 18, 34), GREEN, sw=6)])
P("bear_market", "finance investing trading", lambda: [ellipse(122, 156, 94, 58, BROWN, sw=8), circle(204, 126, 40, BROWN, sw=8), circle(186, 88, 14, BROWN, sw=6),
                                                       circle(222, 92, 14, BROWN, sw=6), ellipse(226, 140, 14, 10, TAN, None), circle(214, 120, 6, OUT, None),
                                                       *[rect(x, 196, 20, 40, BROWN, 6) for x in (56, 90, 146, 176)], poly(arrow_pts(30, 40, 120, 92, 18, 34), RED, sw=6)])
P("price_tag", "shopping finance marketing", lambda: [poly([(30, 128), (100, 40), (226, 40), (226, 216), (100, 216)], AMBER, sw=8), circle(84, 128, 14, WHITE),
                                                      text(166, 146, "$19", 52, OUT)])
P("discount_coupon", "shopping marketing", lambda: [path("M20,64 L236,64 L236,104 C218,104 218,152 236,152 L236,192 L20,192 L20,152 C38,152 38,104 20,104 Z", PINK, sw=8),
                                                    line(176, 72, 176, 186, WHITE, 5, stroke_dasharray="10 8"), text(98, 142, "-30%", 38, WHITE), text(206, 140, "★", 34, WHITE)])
P("invoice_document", "finance business", lambda: [rect(44, 18, 168, 220, WHITE, 12), text(128, 56, "INVOICE", 22, BLUE), *[line(64, 84 + i * 26, 192, 84 + i * 26, SILVER, 7) for i in range(4)],
                                                   rect(118, 188, 76, 30, GREEN, 6), text(156, 210, "PAID", 18, WHITE)])
P("tax_form", "finance law", lambda: [rect(44, 18, 168, 220, PAPER, 12), text(128, 56, "TAX", 30, RED), *[rect(64, 76 + i * 34, 20, 20, WHITE, 3, OUT, 4) for i in range(4)],
                                      *[line(96, 86 + i * 34, 192, 86 + i * 34, GRAY, 6) for i in range(4)], pline([(66, 86), (74, 94), (88, 76)], GREEN, 6)])
P("loan_contract", "finance law business", lambda: [rect(40, 18, 176, 220, WHITE, 12), *[line(60, 50 + i * 22, 196, 50 + i * 22, SILVER, 6) for i in range(5)],
                                                    path("M64,196 C84,170 96,214 116,190 C130,174 140,206 160,190", "none", BLUE, 6), circle(180, 196, 22, RED, sw=5)])
P("budget_jars", "finance savings", lambda: [*[g([rect(x, 84, 60, 132, GLASS, 14, op=0.95), rect(x - 4, 68, 68, 20, GRAY_D, 6),
                                                  rect(x + 6, 216 - h, 48, h, c, 8, None), text(x + 30, 140, s, 30, OUT)])
                                               for x, h, c, s in ((16, 90, GREEN, "$"), (98, 60, AMBER, "%"), (180, 110, SKY, "★"))]])
P("interest_rate", "finance banking", lambda: [*coin(90, 150, 70, GOLD, "$"), circle(184, 76, 52, PURPLE, sw=7), text(184, 94, "%", 56, WHITE)])
P("pay_phone", "finance tech shopping", lambda: [rect(66, 14, 124, 228, INK, 22), rect(76, 38, 104, 168, WHITE, 6), circle(128, 104, 34, GREEN),
                                                 pline([(110, 104), (124, 118), (148, 92)], WHITE, 9), text(128, 170, "PAID", 22, GREEN_D)])

# =========================================================================== crypto (generic, no brand logos)
def token(cx, cy, r, col, glyph):
    mark = btc_glyph(cx, cy, r * 0.9, WHITE) if glyph == "BTC" else text(cx, cy + r * 0.32, glyph, r * 0.9, WHITE, stroke=OUT, sw=4)
    return [poly(reg_pts(cx, cy, r, 6, 0), col, sw=8), poly(reg_pts(cx, cy, r * 0.72, 6, 0), darken(col, 0.85), None), mark]


P("crypto_coin", "crypto finance", lambda: coin(128, 128, 100, ORANGE, "BTC"))
P("crypto_token", "crypto finance web3", lambda: token(128, 128, 104, INDIGO, "◆"))
P("stablecoin", "crypto finance", lambda: coin(128, 128, 100, EMERALD, "$"))
P("blockchain_blocks", "crypto tech web3", lambda: [*[g([poly([(x, y), (x + 44, y - 22), (x + 88, y), (x + 44, y + 22)], lighten(c, 0.3), sw=6),
                                                         poly([(x, y), (x + 44, y + 22), (x + 44, y + 70), (x, y + 48)], c, sw=6),
                                                         poly([(x + 88, y), (x + 44, y + 22), (x + 44, y + 70), (x + 88, y + 48)], darken(c), sw=6)])
                                                      for x, y, c in ((10, 120, BLUE), (84, 80, INDIGO), (158, 120, VIOLET))],
                                                    line(98, 136, 120, 120, OUT, 8), line(172, 120, 190, 136, OUT, 8)])
P("crypto_wallet", "crypto finance web3", lambda: [rect(20, 58, 216, 158, INDIGO, 22), rect(136, 102, 104, 70, VIOLET, 16), circle(168, 137, 14, GOLD),
                                                   *token(78, 46, 30, ORANGE, "BTC")])
P("hardware_wallet", "crypto security", lambda: [rect(66, 20, 124, 216, SLATE, 20), rect(82, 40, 92, 60, "#0b1d33", 6), text(128, 78, "0x…", 22, CYAN, family="DejaVu Sans Mono"),
                                                 circle(104, 140, 16, GRAY), circle(152, 140, 16, GRAY), rect(110, 190, 36, 14, GRAY, 4)])
P("mining_rig", "crypto tech energy", lambda: [rect(18, 70, 220, 140, GRAY_D, 12), *[g([rect(34 + i * 68, 92, 52, 96, SLATE, 6), circle(60 + i * 68, 140, 20, GRAY, sw=5)])
                                                                                   for i in range(3)], poly(bolt_pts(212, 46, 30), YELLOW, sw=5)])
P("pickaxe_mining", "crypto industry", lambda: [line(56, 220, 190, 64, BROWN, 24), path("M120,40 C170,30 220,50 240,90 C200,70 160,62 120,66 Z", GRAY, sw=7),
                                                path("M190,64 C200,40 180,18 150,20", "none", OUT, 0), *coin(76, 92, 40, ORANGE, "BTC")])
P("rocket_moon", "crypto finance growth startup", lambda: [circle(196, 58, 40, SILVER), circle(184, 48, 8, GRAY, None), circle(208, 70, 6, GRAY, None),
                                                           g([path("M128,24 C158,48 170,96 162,150 L94,150 C86,96 98,48 128,24 Z", WHITE, sw=8), circle(128, 86, 18, SKY, sw=6),
                                                              poly([(94, 120), (66, 160), (96, 150)], RED, sw=6), poly([(162, 120), (190, 160), (160, 150)], RED, sw=6),
                                                              path("M104,150 L152,150 L140,196 L128,214 L116,196 Z", ORANGE, sw=6)], "rotate(28 128 128) translate(-20 10)")])
P("nft_frame", "crypto art web3", lambda: [rect(22, 22, 212, 212, GOLD, 10), rect(44, 44, 168, 168, "#0b1d33", 4), circle(128, 112, 40, PINK, None),
                                           path("M66,212 C80,160 176,160 190,212 Z", VIOLET, None)])
P("smart_contract", "crypto web3 tech law", lambda: [rect(40, 18, 176, 220, WHITE, 12), text(128, 70, "{ }", 46, INDIGO, family="DejaVu Sans Mono"),
                                                     *[line(62, 100 + i * 24, 194 - i * 18, 100 + i * 24, SILVER, 7) for i in range(4)], *token(176, 196, 34, INDIGO, "◆")])
P("gas_fee", "crypto finance", lambda: [rect(54, 40, 112, 196, RED, 14), rect(74, 64, 72, 50, WHITE, 6), text(110, 100, "$$", 30, RED),
                                        path("M166,90 L200,90 L214,110 L214,200 C214,212 196,214 196,200 L196,130", "none", OUT, 10), rect(40, 228, 140, 12, OUT, 4, None)])
P("whale_investor", "crypto finance investing", lambda: [path("M28,140 C28,96 80,72 140,80 C196,88 222,116 222,150 C222,196 168,216 112,214 C64,212 28,186 28,140 Z", BLUE, sw=8),
                                                         path("M210,130 C232,108 246,96 248,80 C232,92 224,108 214,118", BLUE, sw=6),
                                                         path("M40,168 C80,190 160,196 210,170 L200,190 C150,212 80,206 46,184 Z", WHITE, None, op=0.9),
                                                         circle(84, 128, 9, OUT, None), path("M130,66 C126,40 134,26 146,20 M130,66 C122,46 112,38 100,36", "none", SKY, 8)])
P("diamond_hands", "crypto investing", lambda: [poly([(64, 64), (192, 64), (232, 112), (128, 228), (24, 112)], CYAN, sw=8),
                                                pline([(24, 112), (232, 112)], OUT, 5), pline([(64, 64), (100, 112), (128, 228), (156, 112), (192, 64)], OUT, 5),
                                                pline([(100, 112), (128, 64), (156, 112)], OUT, 5), poly(star_pts(214, 40, 26, 7, 4, 0), WHITE, sw=4),
                                                poly(star_pts(40, 200, 20, 6, 4, 0), WHITE, sw=4)])

# =========================================================================== business & work
P("briefcase", "business career", lambda: [path("M96,64 L96,44 C96,34 104,28 114,28 L142,28 C152,28 160,34 160,44 L160,64", "none", OUT, 12),
                                           rect(20, 62, 216, 160, BROWN_L, 18), line(20, 120, 236, 120, OUT, 6), rect(112, 108, 32, 28, GOLD, 6)])
P("handshake_deal", "business partnership", lambda: [path("M10,110 L70,80 L120,96 L150,84 L210,110 L246,96 L246,160 L200,176 L150,214 L104,206 L60,176 L10,170 Z", AMBER, sw=8),
                                                     path("M70,80 L120,96 L96,130 C88,146 108,152 120,140 L150,116 L200,176", "none", OUT, 7),
                                                     rect(0, 96, 36, 84, BLUE, 6), rect(220, 86, 36, 84, GRAY_D, 6)])
P("presentation_board", "business education", lambda: [rect(24, 28, 208, 140, WHITE, 10), line(128, 168, 128, 230, OUT, 10), line(128, 168, 76, 236, OUT, 8),
                                                       line(128, 168, 180, 236, OUT, 8), rect(44, 108, 30, 44, BLUE, 4), rect(88, 84, 30, 68, GREEN, 4),
                                                       rect(132, 60, 30, 92, ORANGE, 4), pline([(176, 120), (196, 80), (214, 96)], RED, 6)])
P("org_chart", "business management", lambda: [rect(96, 18, 64, 46, INDIGO, 10), *[rect(x, 112, 56, 40, BLUE, 8) for x in (24, 100, 176)],
                                               *[rect(x, 196, 44, 36, SKY, 8) for x in (18, 72, 140, 194)], line(128, 64, 128, 90, OUT, 6), line(52, 90, 204, 90, OUT, 6),
                                               *[line(x, 90, x, 112, OUT, 6) for x in (52, 128, 204)], line(52, 152, 52, 180, OUT, 5), line(40, 180, 94, 180, OUT, 5),
                                               line(204, 152, 204, 180, OUT, 5), line(162, 180, 216, 180, OUT, 5)])
P("office_building", "business city career", lambda: [rect(48, 22, 160, 216, SKY, 8), *[rect(66 + c * 44, 40 + r * 36, 28, 22, GLASS if (r + c) % 3 else YELLOW, 3, OUT, 4)
                                                                                     for r in range(5) for c in range(3)], rect(104, 206, 48, 32, SLATE, 4)])
P("factory_industry", "industry business energy", lambda: [poly([(16, 236), (16, 120), (72, 150), (72, 120), (128, 150), (128, 120), (184, 150), (184, 236)], GRAY, sw=8),
                                                           rect(184, 60, 40, 176, GRAY_D, 4), *[rect(36 + i * 52, 180, 30, 26, YELLOW, 3, OUT, 5) for i in range(3)],
                                                           path(cloud_d(206, 40, 30), SILVER, None, op=0.9)])
P("storefront_shop", "business shopping", lambda: [rect(26, 92, 204, 140, WHITE, 6), path("M16,60 L240,60 L240,100 " + " ".join(f"Q{240 - 14 - i * 28},{120} {240 - 28 - i * 28},{100}" for i in range(8)) + " Z", RED, sw=7),
                                                   rect(44, 128, 74, 104, SKY, 4), rect(144, 128, 68, 60, GLASS, 4), rect(16, 40, 224, 22, OUT, 4, None),
                                                   text(128, 58, "SHOP", 18, WHITE)])
P("shopping_cart", "shopping business", lambda: [pline([(14, 40), (50, 40), (80, 170), (208, 170)], OUT, 12),
                                                 path("M58,72 L232,72 L212,146 L74,146 Z", ORANGE, sw=8), circle(96, 206, 18, GRAY_D), circle(190, 206, 18, GRAY_D)])
P("shopping_bag", "shopping fashion", lambda: [path("M92,84 L92,58 C92,34 110,22 128,22 C146,22 164,34 164,58 L164,84", "none", OUT, 10),
                                               path("M44,78 L212,78 L226,236 L30,236 Z", PINK, sw=8), hl("M60,92 L80,92 L74,220 L50,220 Z", 0.25)])
P("package_box", "shopping business logistics", lambda: [poly([(128, 26), (236, 72), (128, 118), (20, 72)], TAN, sw=8), poly([(20, 72), (128, 118), (128, 236), (20, 190)], BROWN_L, sw=8),
                                                         poly([(236, 72), (128, 118), (128, 236), (236, 190)], darken(TAN, 0.8), sw=8),
                                                         poly([(74, 49), (182, 95), (182, 140), (160, 130), (160, 104), (52, 58)], SAND, OUT, 5)])
P("delivery_truck", "logistics transport shopping", lambda: [rect(10, 70, 150, 120, WHITE, 8), path("M160,104 L212,104 L244,146 L244,190 L160,190 Z", BLUE, sw=8),
                                                            path("M178,116 L208,116 L228,144 L178,144 Z", GLASS, OUT, 5), circle(60, 196, 26, SLATE), circle(204, 196, 26, SLATE),
                                                            circle(60, 196, 10, SILVER, None), circle(204, 196, 10, SILVER, None), text(84, 140, "FAST", 32, BLUE)])
P("gift_box", "holiday shopping celebration", lambda: [rect(30, 104, 196, 128, RED, 8), rect(18, 76, 220, 40, RED_D, 8), rect(112, 76, 32, 156, YELLOW, 2),
                                                       path("M128,76 C92,30 50,48 76,76 Z", YELLOW), path("M128,76 C164,30 206,48 180,76 Z", YELLOW)])
P("pen_signature", "business law education", lambda: [g([rect(100, 10, 40, 170, INDIGO, 10), poly([(100, 180), (140, 180), (120, 230)], CREAM, sw=7),
                                                          poly([(112, 210), (128, 210), (120, 230)], OUT, None), rect(100, 10, 40, 32, GOLD, 8)], "rotate(35 120 128)"),
                                                       path("M20,226 C40,200 56,240 76,214 C88,200 96,232 110,220", "none", BLUE, 6)])
P("rubber_stamp", "business law", lambda: [rect(104, 18, 48, 70, BROWN_L, 20), rect(60, 86, 136, 40, BROWN, 10), rect(48, 126, 160, 34, RED, 6),
                                           rect(40, 196, 176, 40, "none", 8, RED, 7), text(128, 226, "APPROVED", 24, RED)])
P("clipboard_checklist", "business productivity", lambda: [rect(40, 34, 176, 206, BROWN_L, 14), rect(56, 52, 144, 176, WHITE, 6), rect(92, 20, 72, 34, GRAY_D, 8),
                                                           *[g([rect(70, 76 + i * 44, 24, 24, WHITE, 4, OUT, 5), line(106, 88 + i * 44, 186, 88 + i * 44, GRAY, 7),
                                                                pline([(74, 88 + i * 44), (82, 96 + i * 44), (96, 76 + i * 44)], GREEN, 6) if i < 2 else ""]) for i in range(3)]])
P("sticky_notes", "productivity business", lambda: [g([rect(30, 46, 120, 120, YELLOW, 4)], "rotate(-8 90 106)"), g([rect(106, 90, 120, 120, PINK, 4)], "rotate(6 166 150)"),
                                                    *[line(124, 128 + i * 22, 206, 132 + i * 22, darken(PINK, 0.7), 6) for i in range(3)]])
P("ladder_success", "career self_improvement growth", lambda: [line(70, 236, 110, 20, OUT, 14), line(150, 236, 190, 20, OUT, 14), line(70, 236, 110, 20, BROWN_L, 6),
                                                               line(150, 236, 190, 20, BROWN_L, 6), *[line(74 + i * 7.5, 214 - i * 40, 154 + i * 7.5, 214 - i * 40, BROWN, 9) for i in range(5)],
                                                               poly(star_pts(198, 26, 22, 9), GOLD, sw=5)])
P("stairs_growth", "career self_improvement growth", lambda: [path("M16,236 L16,190 L70,190 L70,144 L124,144 L124,98 L178,98 L178,52 L240,52 L240,236 Z", BLUE, sw=8),
                                                             poly(arrow_pts(30, 170, 214, 30, 14, 30), GREEN, sw=5)])
P("mountain_summit_flag", "goal self_improvement adventure", lambda: [poly([(10, 236), (110, 60), (150, 120), (176, 92), (246, 236)], GRAY, sw=8),
                                                                      poly([(110, 60), (134, 100), (118, 92), (100, 106), (88, 98)], WHITE, None),
                                                                      line(110, 60, 110, 18, OUT, 7), poly([(112, 20), (150, 30), (112, 42)], RED, sw=5)])
P("chess_knight", "strategy business game", lambda: [path("M76,206 L76,184 L96,150 C70,140 64,118 82,96 L120,46 L134,24 L146,46 C186,60 204,108 194,150 "
                                                         "L196,184 L196,206 Z", INK, WHITE, 7), circle(130, 76, 8, WHITE, None), rect(56, 202, 160, 30, INK, 8, WHITE, 6)])
P("compass_direction", "travel strategy navigation", lambda: [circle(128, 128, 104, SILVER, sw=9), circle(128, 128, 84, WHITE, None),
                                                              poly([(128, 52), (146, 128), (110, 128)], RED, sw=5), poly([(128, 204), (146, 128), (110, 128)], GRAY_D, sw=5),
                                                              circle(128, 128, 10, GOLD), text(128, 44, "N", 22, OUT)])
P("rocket_startup", "startup business tech", lambda: [g([path("M128,16 C166,46 178,104 168,170 L88,170 C78,104 90,46 128,16 Z", WHITE, sw=8),
                                                         circle(128, 92, 22, SKY, sw=6), poly([(88, 128), (52, 182), (90, 172)], RED, sw=6),
                                                         poly([(168, 128), (204, 182), (166, 172)], RED, sw=6), path("M100,170 L156,170 L144,214 L128,240 L112,214 Z", ORANGE, sw=6),
                                                         path("M114,170 L142,170 L134,200 L128,214 L122,200 Z", YELLOW, None)], "rotate(30 128 128)")])
P("idea_to_money", "business startup finance", lambda: [path("M74,28 C102,28 120,48 120,72 C120,94 106,104 100,118 L48,118 C42,104 28,94 28,72 C28,48 46,28 74,28 Z", YELLOW, sw=7),
                                                        rect(50, 118, 48, 18, GRAY, 5), poly(arrow_pts(110, 150, 170, 150, 18, 30), OUT, sw=0), *coin(196, 170, 50, GOLD, "$")])
P("time_is_money", "business productivity finance", lambda: [circle(104, 116, 86, WHITE, sw=9), line(104, 116, 104, 60, OUT, 9), line(104, 116, 146, 136, OUT, 8),
                                                             *coin(190, 186, 52, GOLD, "$")])
P("contract_handshake", "business law partnership", lambda: [rect(26, 18, 150, 196, WHITE, 10), *[line(46, 50 + i * 24, 156, 50 + i * 24, SILVER, 6) for i in range(5)],
                                                            path("M46,184 C62,164 74,200 92,178", "none", BLUE, 5), *[circle(186, 186, 54, GREEN, sw=7)],
                                                            pline([(160, 186), (180, 206), (214, 166)], WHITE, 12)])
P("money_growth_plant", "finance investing savings growth", lambda: [path("M60,176 L196,176 L182,236 L74,236 Z", BROWN_L, sw=8), line(128, 176, 128, 92, GREEN_D, 10),
                                                                     path("M128,120 C90,120 70,96 74,70 C104,70 126,92 128,120 Z", GREEN, sw=6),
                                                                     path("M128,104 C160,104 182,82 180,56 C150,56 130,78 128,104 Z", GREEN, sw=6), *coin(128, 52, 30, GOLD, "$")])
P("burnout_battery", "career mental_health productivity", lambda: [rect(22, 70, 196, 116, WHITE, 16, sw=9), rect(218, 106, 20, 44, OUT, 6, None),
                                                                   rect(38, 86, 34, 84, RED, 6, None), text(150, 150, "!", 70, RED)])
P("full_battery", "productivity energy", lambda: [rect(22, 70, 196, 116, WHITE, 16, sw=9), rect(218, 106, 20, 44, OUT, 6, None),
                                                  *[rect(38 + i * 44, 86, 34, 84, GREEN, 6, None) for i in range(4)]])
P("inbox_tray", "business productivity tech", lambda: [path("M26,120 L60,40 L196,40 L230,120 L230,220 L26,220 Z", WHITE, sw=8), path("M26,120 L86,120 L100,150 L156,150 L170,120 L230,120",
                                                                                                                                   "none", OUT, 7),
                                                       rect(84, 70, 88, 52, SKY, 6), circle(206, 50, 26, RED, sw=6), text(206, 62, "9", 30, WHITE)])

# =========================================================================== tech & devices
def phone(content, body=INK):
    return [rect(64, 10, 128, 236, body, 24), rect(74, 32, 108, 192, WHITE, 8, None), rect(108, 18, 40, 8, GRAY_D, 4, None), *content]


def laptop(content, screen="#0b1d33"):
    return [rect(36, 40, 184, 128, SLATE, 12), rect(48, 52, 160, 104, screen, 4, None), *content,
            path("M14,176 L242,176 L230,206 L26,206 Z", SILVER, sw=7), rect(104, 180, 48, 8, GRAY, 3, None)]


P("smartphone", "tech social_media general", lambda: phone([rect(86, 46, 84, 40, SKY, 8, None), rect(86, 96, 38, 38, PINK, 8, None), rect(132, 96, 38, 38, AMBER, 8, None),
                                                            rect(86, 142, 38, 38, GREEN, 8, None), rect(132, 142, 38, 38, VIOLET, 8, None), circle(128, 206, 10, SILVER, None)]))
P("phone_chat", "tech social_media communication", lambda: phone([rect(82, 52, 70, 26, SILVER, 10, None), rect(104, 88, 70, 26, GREEN, 10, None),
                                                                   rect(82, 124, 60, 26, SILVER, 10, None), rect(112, 160, 62, 26, GREEN, 10, None)]))
P("phone_chart_up", "tech finance trading", lambda: phone([pline([(84, 180), (104, 150), (122, 162), (146, 108), (170, 70)], GREEN, 8),
                                                           text(128, 206, "+24%", 22, GREEN_D)]))
P("phone_lock", "tech security", lambda: phone([rect(98, 118, 60, 52, GOLD, 8, OUT, 5), path("M108,118 L108,102 C108,88 118,80 128,80 C138,80 148,88 148,102 L148,118", "none", OUT, 7)]))
P("phone_video_call", "tech communication remote_work", lambda: phone([rect(74, 32, 108, 192, SKY, 8, None), circle(128, 104, 26, WHITE, OUT, 5),
                                                                       path("M90,180 C96,140 160,140 166,180 Z", WHITE, OUT, 5), circle(110, 206, 11, RED, None),
                                                                       circle(146, 206, 11, GREEN, None)]))
P("phone_notification", "tech social_media addiction", lambda: phone([*[g([rect(80, 46 + i * 40, 96, 32, PAPER, 8, OUT, 3), circle(96, 62 + i * 40, 8, [RED, BLUE, GREEN, PINK][i], None),
                                                                           line(110, 58 + i * 40, 164, 58 + i * 40, GRAY, 4), line(110, 68 + i * 40, 150, 68 + i * 40, SILVER, 4)])
                                                                        for i in range(4)]]))
P("phone_map_route", "tech travel navigation", lambda: phone([rect(74, 32, 108, 192, "#dcfce7", 8, None), path("M84,200 C100,150 150,170 160,120 C168,84 120,80 130,56", "none", BLUE, 7),
                                                              path(f"M130,74 C122,62 114,56 114,48 C114,40 122,34 130,34 C138,34 146,40 146,48 C146,56 138,62 130,74 Z", RED, OUT, 3)]))
P("phone_shopping", "tech shopping ecommerce", lambda: phone([rect(86, 50, 84, 70, SILVER, 8, None), path("M106,72 L150,72 L144,100 L112,100 Z", PINK, OUT, 3),
                                                              text(128, 146, "$29", 26, OUT), rect(90, 164, 76, 30, ORANGE, 8, None), text(128, 186, "BUY", 18, WHITE)]))
P("laptop_code", "tech coding", lambda: laptop([text(60, 82, "def", 16, PINK, anchor="start", family="DejaVu Sans Mono"),
                                                *[line(62 + (i % 3) * 10, 96 + i * 12, 130 + (i * 23) % 60, 96 + i * 12, [CYAN, GREEN, AMBER, VIOLET][i % 4], 5) for i in range(5)]]))
P("laptop_chart", "tech business finance data", lambda: laptop([*[rect(66 + i * 26, 140 - h, 18, h, c, 3, None) for i, (h, c) in enumerate(((20, SKY), (36, BLUE), (52, CYAN), (70, GREEN), (60, EMERALD)))],
                                                                pline([(64, 120), (110, 100), (150, 84), (194, 64)], AMBER, 4)]))
P("laptop_email", "tech business communication", lambda: laptop([rect(80, 70, 96, 64, WHITE, 6, None), pline([(80, 70), (128, 106), (176, 70)], GRAY_D, 5)]))
P("laptop_warning", "tech security", lambda: laptop([poly([(128, 62), (168, 140), (88, 140)], YELLOW, OUT, 4), text(128, 134, "!", 44, OUT)], "#3f1d1d"))
P("laptop_video", "tech entertainment education", lambda: laptop([poly([(116, 80), (148, 104), (116, 128)], WHITE, None), rect(58, 146, 140, 4, GRAY, 2, None), rect(58, 146, 60, 4, RED, 2, None)]))
P("desktop_monitor", "tech office", lambda: [rect(18, 24, 220, 150, SLATE, 14), rect(32, 38, 192, 122, SKY, 4, None), rect(110, 174, 36, 34, GRAY, 2), rect(70, 206, 116, 18, GRAY_D, 6),
                                             rect(46, 56, 80, 50, WHITE, 6, None), rect(136, 56, 74, 90, WHITE, 6, None), rect(46, 116, 80, 30, WHITE, 6, None)])
P("tablet_device", "tech education", lambda: [rect(28, 30, 200, 200, INK, 20), rect(42, 44, 172, 172, WHITE, 6, None), circle(96, 110, 30, AMBER, None),
                                              rect(140, 84, 60, 10, SILVER, 4, None), rect(140, 104, 46, 10, SILVER, 4, None), rect(56, 160, 144, 40, SKY, 6, None)])
P("smartwatch", "tech health fitness", lambda: [rect(92, 6, 72, 60, SLATE, 10), rect(92, 190, 72, 60, SLATE, 10), rect(62, 58, 132, 140, INK, 32),
                                                rect(76, 72, 104, 112, "#0b1d33", 22, None), path(heart_d(128, 112, 22), RED, None),
                                                pline([(86, 156), (106, 156), (116, 138), (128, 172), (140, 150), (170, 150)], GREEN, 5)])
P("tv_screen", "tech entertainment media", lambda: [rect(14, 40, 228, 152, INK, 14), rect(28, 54, 200, 124, SKY, 4, None), path(cloud_d(160, 100, 26), WHITE, None),
                                                    poly([(28, 178), (90, 120), (140, 178)], GREEN, None), line(128, 192, 128, 220, OUT, 10), rect(78, 216, 100, 16, GRAY_D, 6)])
P("robot_head", "ai tech", lambda: [line(128, 40, 128, 16, OUT, 8), circle(128, 14, 10, RED), rect(36, 40, 184, 160, SILVER, 30), rect(56, 70, 144, 70, "#0b1d33", 18),
                                    circle(98, 104, 16, CYAN, None), circle(158, 104, 16, CYAN, None), rect(86, 160, 84, 18, GRAY, 6),
                                    *[line(102 + i * 18, 160, 102 + i * 18, 178, OUT, 4) for i in range(4)], rect(14, 92, 24, 56, GRAY, 8), rect(218, 92, 24, 56, GRAY, 8)])
P("ai_chip", "ai tech", lambda: [*[line(70 + i * 29, 20, 70 + i * 29, 236, OUT, 8) for i in range(5)], *[line(20, 70 + i * 29, 236, 70 + i * 29, OUT, 8) for i in range(5)],
                                 rect(48, 48, 160, 160, INK, 18), rect(66, 66, 124, 124, VIOLET, 10), text(128, 146, "AI", 54, WHITE)])
P("cpu_processor", "tech computing", lambda: [*[line(70 + i * 29, 20, 70 + i * 29, 236, GOLD, 8) for i in range(5)], *[line(20, 70 + i * 29, 236, 70 + i * 29, GOLD, 8) for i in range(5)],
                                              rect(48, 48, 160, 160, GREEN_D, 18), rect(80, 80, 96, 96, SILVER, 10), text(128, 138, "CPU", 26, OUT)])
P("neural_network", "ai tech data", lambda: [*[line(x0, y0, x1, y1, GRAY, 4) for x0, ys0, x1, ys1 in ((50, (60, 128, 196), 128, (40, 100, 156, 216)), (128, (40, 100, 156, 216), 206, (90, 166)))
                                               for y0 in ys0 for y1 in ys1],
                                             *[circle(50, y, 18, CYAN) for y in (60, 128, 196)], *[circle(128, y, 18, VIOLET) for y in (40, 100, 156, 216)],
                                             *[circle(206, y, 18, PINK) for y in (90, 166)]])
P("cloud_upload", "tech data storage", lambda: [path(cloud_d(128, 120, 96), SKY, sw=9), poly(arrow_pts(128, 196, 128, 92, 26, 50), WHITE, OUT, 6)])
P("cloud_computing", "tech data storage", lambda: [path(cloud_d(128, 96, 92), WHITE, sw=9), *[line(x, 140, x, 196, OUT, 6) for x in (80, 128, 176)],
                                                   *[circle(x, 208, 16, CYAN) for x in (80, 128, 176)]])
P("server_rack", "tech data infrastructure", lambda: [rect(56, 14, 144, 228, INK, 12), *[g([rect(70, 30 + i * 52, 116, 40, SLATE, 6), circle(86, 50 + i * 52, 6, GREEN if i != 2 else RED, None),
                                                                                       line(104, 50 + i * 52, 170, 50 + i * 52, GRAY, 4)]) for i in range(4)]])
P("database_cylinder", "tech data", lambda: [path("M40,60 L40,196 C40,226 216,226 216,196 L216,60", BLUE, sw=8), ellipse(128, 60, 88, 30, SKY),
                                             path("M40,106 C40,136 216,136 216,106", "none", OUT, 6), path("M40,152 C40,182 216,182 216,152", "none", OUT, 6)])
P("wifi_signal", "tech internet", lambda: [path(arc_d(128, 200, r, 225, 315), "none", OUT, 30) for r in (150, 104, 58)] + [circle(128, 200, 22, OUT, None)] +
          [path(arc_d(128, 200, r, 225, 315), "none", c, 18) for r, c in ((150, GREEN), (104, GREEN), (58, GREEN))])
P("code_brackets", "tech coding", lambda: [pline([(84, 48), (24, 128), (84, 208)], OUT, 30), pline([(172, 48), (232, 128), (172, 208)], OUT, 30),
                                           pline([(84, 48), (24, 128), (84, 208)], CYAN, 18), pline([(172, 48), (232, 128), (172, 208)], CYAN, 18),
                                           line(146, 40, 110, 216, OUT, 22), line(146, 40, 110, 216, PINK, 10)])
P("software_bug", "tech coding", lambda: [line(70, 60, 98, 90, OUT, 8), line(186, 60, 158, 90, OUT, 8), *[line(x0, y, x1, y + d, OUT, 8) for x0, x1, y, d in
                                                                                                       ((60, 26, 130, -10), (60, 22, 168, 10), (196, 230, 130, -10), (196, 234, 168, 10))],
                                          ellipse(128, 150, 66, 82, RED), circle(128, 86, 34, INK), line(128, 100, 128, 230, OUT, 6),
                                          *[circle(x, y, 10, OUT, None) for x, y in ((100, 140), (156, 140), (104, 190), (152, 190))]])
P("usb_drive", "tech data storage", lambda: [rect(96, 14, 64, 60, SILVER, 6), rect(110, 30, 12, 14, OUT, 2, None), rect(134, 30, 12, 14, OUT, 2, None),
                                             rect(80, 70, 96, 170, BLUE, 18), circle(128, 200, 14, CYAN, None)])
P("game_controller", "gaming entertainment tech", lambda: [path("M60,72 L196,72 C232,72 250,140 240,190 C232,226 196,222 182,196 L168,170 L88,170 L74,196 "
                                                              "C60,222 24,226 16,190 C6,140 24,72 60,72 Z", INDIGO, sw=8), rect(54, 108, 52, 18, WHITE, 4, None),
                                                           rect(71, 91, 18, 52, WHITE, 4, None), *[circle(x, y, 12, c, None) for x, y, c in ((182, 100, GREEN), (206, 122, RED), (158, 122, AMBER), (182, 144, SKY))]])
P("vr_headset", "tech gaming entertainment", lambda: [path("M22,88 C22,70 34,60 52,60 L204,60 C222,60 234,70 234,88 L234,160 C234,178 222,188 204,188 L160,188 L140,160 L116,160 L96,188 "
                                                         "L52,188 C34,188 22,178 22,160 Z", SLATE, sw=8), rect(40, 80, 176, 64, INK, 16, None), hl("M52,92 L120,92 L110,116 L52,116 Z", 0.25)])
P("drone_quad", "tech photography", lambda: [*[g([line(128, 128, x, y, OUT, 10), ellipse(x, y - 8, 40, 8, GRAY, OUT, 5), circle(x, y, 10, OUT, None)])
                                               for x, y in ((50, 60), (206, 60), (50, 196), (206, 196))],
                                             rect(90, 100, 76, 56, SILVER, 16), circle(128, 166, 14, INK)])
P("satellite", "space tech", lambda: [g([rect(10, 106, 80, 44, BLUE, 4), rect(166, 106, 80, 44, BLUE, 4), *[line(x, 106, x, 150, SKY, 3) for x in (30, 50, 70, 186, 206, 226)],
                                         line(90, 128, 166, 128, OUT, 8), rect(100, 92, 56, 72, SILVER, 10), path(arc_d(128, 86, 26, 200, 340), "none", OUT, 7),
                                         line(128, 72, 128, 52, OUT, 6), circle(128, 48, 7, RED, None)], "rotate(-25 128 128)")])
P("satellite_dish", "tech communication space", lambda: [path("M40,60 C60,150 140,190 210,170 Z", SILVER, sw=8), line(116, 132, 160, 70, OUT, 7), circle(162, 66, 10, RED),
                                                         line(120, 150, 110, 230, OUT, 12), rect(70, 222, 90, 16, GRAY_D, 6)])
P("printer_office", "tech office", lambda: [rect(66, 18, 124, 70, WHITE, 6), rect(20, 82, 216, 100, GRAY, 16), rect(60, 160, 136, 76, WHITE, 6),
                                            *[line(80, 186 + i * 16, 176, 186 + i * 16, SILVER, 5) for i in range(3)], circle(206, 110, 9, GREEN, None)])
P("keyboard_mouse", "tech office coding", lambda: [rect(10, 110, 180, 90, SLATE, 12), *[rect(22 + c * 28, 122 + r * 24, 20, 16, GRAY, 4, None) for r in range(3) for c in range(6)],
                                                   rect(204, 120, 46, 76, SILVER, 22), line(227, 120, 227, 146, OUT, 4), path("M227,120 C227,80 200,70 180,60", "none", OUT, 5)])
P("camera_photo", "tech photography travel media", lambda: [rect(20, 70, 216, 150, INK, 18), rect(64, 44, 70, 34, INK, 8), circle(128, 146, 54, SLATE, GRAY, 9),
                                                            circle(128, 146, 30, SKY, None), hl_ellipse(116, 132, 12, 7, 0.6), rect(184, 88, 32, 16, RED, 4, None)])
P("video_camera", "media entertainment", lambda: [rect(16, 82, 168, 112, SLATE, 16), poly([(184, 120), (240, 86), (240, 190), (184, 156)], GRAY_D, sw=8),
                                                  circle(64, 58, 30, GRAY_D), circle(134, 58, 30, GRAY_D), circle(42, 104, 9, RED, None)])
P("microphone_studio", "media music podcast", lambda: [rect(90, 18, 76, 124, GRAY_D, 38), *[line(96, 46 + i * 18, 160, 46 + i * 18, GRAY, 4) for i in range(4)],
                                                       path("M64,112 C64,166 192,166 192,112", "none", OUT, 10), line(128, 160, 128, 214, OUT, 10), rect(82, 210, 92, 18, OUT, 6, None)])
P("headphones_music", "music media gaming", lambda: [path("M40,150 L40,120 C40,66 80,30 128,30 C176,30 216,66 216,120 L216,150", "none", OUT, 22),
                                                     path("M40,150 L40,120 C40,66 80,30 128,30 C176,30 216,66 216,120 L216,150", "none", GRAY_D, 10),
                                                     rect(22, 130, 52, 92, VIOLET, 18), rect(182, 130, 52, 92, VIOLET, 18)])
P("speaker_loud", "music media", lambda: [rect(58, 16, 140, 224, INK, 16), circle(128, 76, 32, SLATE, GRAY, 6), circle(128, 170, 50, SLATE, GRAY, 7), circle(128, 170, 16, GRAY_D, None),
                                          *[path(arc_d(128, 170, r, -40, 40), "none", CYAN, 6) for r in (80, 100)]])
P("qr_code", "tech shopping", lambda: [rect(20, 20, 216, 216, WHITE, 10), *[rect(x, y, 56, 56, "none", 4, OUT, 12) for x, y in ((40, 40), (160, 40), (40, 160))],
                                       *[rect(x + 18, y + 18, 20, 20, OUT, 0, None) for x, y in ((40, 40), (160, 40), (40, 160))],
                                       *[rect(110 + (i * 37) % 110, 110 + (i * 53) % 110, 18, 18, OUT, 0, None) for i in range(11)]])
P("fingerprint", "security tech", lambda: [*[path(arc_d(128, 140, r, 200, 340 + (i % 2) * 20), "none", c, 10) for i, (r, c) in enumerate(((96, BLUE), (76, BLUE), (56, INDIGO), (36, INDIGO), (16, VIOLET)))],
                                           *[path(f"M{128 - r},{140} C{128 - r},{180} {128 - r * 0.6},{210} {128 - r * 0.2},{226}", "none", c, 10)
                                             for r, c in ((76, BLUE), (36, INDIGO))]])
P("password_field", "security tech", lambda: [rect(14, 80, 228, 96, WHITE, 16), *[circle(48 + i * 32, 128, 10, OUT, None) for i in range(5)], rect(196, 98, 30, 60, BLUE, 8)])
P("hacker_skull_laptop", "security tech", lambda: laptop([circle(128, 96, 26, WHITE, None), rect(112, 112, 32, 16, WHITE, 3, None), circle(118, 94, 7, OUT, None),
                                                          circle(138, 94, 7, OUT, None), *[text(70 + i * 30, 150, "01"[i % 2], 14, GREEN, family="DejaVu Sans Mono") for i in range(5)]], "#052e16"))
P("cctv_camera", "security", lambda: [rect(110, 20, 20, 60, GRAY_D, 4), g([rect(40, 70, 150, 64, SILVER, 14), rect(180, 84, 40, 36, INK, 8), circle(200, 102, 10, RED, None)], "rotate(14 128 100)")])
P("plug_socket", "tech energy home", lambda: [rect(40, 40, 176, 176, WHITE, 28), circle(128, 128, 60, SILVER), rect(98, 104, 14, 44, OUT, 4, None), rect(144, 104, 14, 44, OUT, 4, None)])
P("battery_charging", "tech energy", lambda: [rect(70, 34, 116, 200, WHITE, 18, sw=9), rect(106, 18, 44, 20, OUT, 4, None), rect(86, 140, 84, 78, GREEN, 8, None),
                                              poly(bolt_pts(128, 120, 54), YELLOW, OUT, 6)])
P("folder_files", "tech office business", lambda: [path("M20,58 C20,48 28,40 38,40 L98,40 L118,62 L218,62 C228,62 236,70 236,80 L236,206 C236,216 228,224 218,224 L38,224 "
                                                       "C28,224 20,216 20,206 Z", AMBER, sw=8), rect(40, 84, 176, 120, YELLOW, 8, OUT, 6)])
P("trash_bin", "general tech environment", lambda: [rect(60, 70, 136, 166, GRAY, 12), rect(40, 46, 176, 28, GRAY_D, 8), rect(104, 24, 48, 26, GRAY_D, 6),
                                                    *[line(x, 98, x, 208, OUT, 8) for x in (96, 128, 160)]])
P("download_arrow", "tech internet", lambda: [poly(arrow_pts(128, 20, 128, 176, 44, 84), BLUE, sw=8), rect(30, 196, 196, 34, BLUE, 10)])
P("email_envelope", "tech communication business", lambda: [rect(18, 52, 220, 152, WHITE, 14), pline([(22, 60), (128, 140), (234, 60)], OUT, 8),
                                                            pline([(22, 196), (100, 120)], OUT, 6), pline([(234, 196), (156, 120)], OUT, 6), circle(214, 58, 22, RED, sw=5)])
P("cursor_click", "tech internet", lambda: [poly([(100, 46), (100, 226), (144, 184), (176, 246), (202, 234), (170, 172), (230, 172)], WHITE, sw=9),
                                            *[line(76 + 26 * math.cos(math.radians(a)), 50 + 26 * math.sin(math.radians(a)), 76 + 46 * math.cos(math.radians(a)),
                                                   50 + 46 * math.sin(math.radians(a)), AMBER, 8) for a in (160, 215, 270)]])
P("browser_window", "tech internet marketing", lambda: [rect(14, 30, 228, 196, WHITE, 14), path("M14,44 C14,36 20,30 28,30 L228,30 C236,30 242,36 242,44 L242,66 L14,66 Z", SLATE),
                                                        *[circle(36 + i * 22, 48, 7, c, None) for i, c in enumerate((RED, AMBER, GREEN))], rect(34, 84, 120, 70, SKY, 6, None),
                                                        *[line(166, 92 + i * 20, 222, 92 + i * 20, SILVER, 7) for i in range(3)], rect(34, 168, 188, 40, SILVER, 6, None)])
P("social_profile", "social_media marketing", lambda: [rect(30, 20, 196, 216, WHITE, 18), circle(128, 82, 36, SKY), path("M86,148 C92,112 164,112 170,148 Z", SKY, None),
                                                       rect(66, 166, 124, 14, SILVER, 6, None), rect(86, 192, 84, 24, PINK, 10, None), text(128, 210, "Follow", 16, WHITE)])
P("video_play_button", "media social_media entertainment", lambda: [rect(20, 46, 216, 164, RED, 40), poly([(108, 90), (176, 128), (108, 166)], WHITE, None)])
P("live_badge", "media social_media", lambda: [rect(20, 84, 216, 88, RED, 22), circle(64, 128, 16, WHITE, None), text(148, 148, "LIVE", 52, WHITE)])
P("viral_graph", "social_media marketing growth", lambda: [rect(16, 28, 224, 200, INK, 18), path("M36,200 C110,196 150,170 170,120 C184,84 196,60 222,40", "none", PINK, 10),
                                                           path(heart_d(196, 84, 20), RED, OUT, 4), text(70, 76, "1M", 36, WHITE)])
