"""Props, part C: education, home & everyday, tools & construction, transport & travel, sports & fitness,
music & entertainment, holidays, energy, law, history, mind & self-improvement, agriculture, real estate."""
from __future__ import annotations

import math

from .kit import *  # noqa: F401,F403
from .registry import P

# =========================================================================== education
P("book_closed", "education general", lambda: [rect(50, 20, 156, 216, BLUE, 12), rect(50, 20, 26, 216, BLUE_D, 8), rect(96, 60, 90, 40, WHITE, 6), line(106, 76, 176, 76, GRAY, 5), line(106, 88, 160, 88, GRAY, 5)])
P("book_open", "education general history", lambda: [path("M128,60 C100,40 50,36 18,46 L18,206 C50,196 100,200 128,220 Z", WHITE, sw=8),
                                                     path("M128,60 C156,40 206,36 238,46 L238,206 C206,196 156,200 128,220 Z", WHITE, sw=8),
                                                     *[line(38, 76 + i * 26, 108, 82 + i * 26, GRAY, 5) for i in range(5)], *[line(148, 82 + i * 26, 218, 76 + i * 26, GRAY, 5) for i in range(5)]])
P("books_stack", "education general", lambda: [rect(30, 180, 196, 46, RED, 8), rect(44, 136, 172, 46, GREEN, 8), rect(24, 92, 184, 46, BLUE, 8), rect(54, 52, 150, 42, AMBER, 8),
                                               *[line(x, y, x, y + 30, WHITE, 5) for x, y in ((200, 188), (196, 144), (190, 100), (190, 58))]])
P("graduation_cap", "education career", lambda: [path("M60,120 L60,170 C60,196 196,196 196,170 L196,120", INK, OUT, 8), poly([(128, 40), (246, 92), (128, 144), (10, 92)], INK, WHITE, 6),
                                                 line(128, 92, 210, 112, AMBER, 6), line(210, 112, 210, 176, AMBER, 6), circle(210, 184, 12, AMBER)])
P("pencil", "education art", lambda: [g([rect(98, 20, 60, 170, YELLOW, 4), rect(98, 20, 60, 30, PINK, 8), rect(98, 44, 60, 14, SILVER, 0), poly([(98, 190), (158, 190), (128, 244)], CREAM, sw=7),
                                         poly([(116, 224), (140, 224), (128, 244)], OUT, None), line(118, 58, 118, 188, AMBER, 4), line(138, 58, 138, 188, AMBER, 4)], "rotate(40 128 128)")])
P("ruler", "education construction", lambda: [g([rect(10, 98, 236, 60, YELLOW, 6), *[line(26 + i * 18, 98, 26 + i * 18, 98 + (30 if i % 2 == 0 else 18), OUT, 4) for i in range(12)]],
                                                 "rotate(-30 128 128)")])
P("school_backpack", "education kids", lambda: [rect(46, 50, 164, 186, RED, 36), rect(70, 140, 116, 70, RED_D, 18), path("M92,50 C92,20 164,20 164,50", "none", OUT, 12), rect(112, 152, 32, 10, YELLOW, 4)])
P("chalkboard", "education", lambda: [rect(14, 30, 228, 160, GREEN_D, 8), rect(14, 30, 228, 160, "none", 8, BROWN_L, 12), text(128, 104, "A+B", 44, WHITE, family="DejaVu Sans Mono"),
                                      path("M40,140 C70,120 100,160 130,140 C150,128 170,150 200,136", "none", WHITE, 4), rect(80, 190, 96, 12, BROWN_L, 4), line(70, 202, 50, 240, OUT, 8),
                                      line(186, 202, 206, 240, OUT, 8)])
P("globe_desk", "education travel history", lambda: [circle(128, 104, 82, SKY), path("M80,60 C100,56 116,80 104,96 C92,110 106,132 84,140 C66,124 62,84 80,60 Z", GREEN, OUT, 4),
                                                     path("M150,40 C180,56 196,94 186,120 C170,110 166,94 150,90 C138,78 140,54 150,40 Z", GREEN, OUT, 4),
                                                     path(arc_d(128, 104, 100, 120, 300), "none", OUT, 8), line(128, 190, 128, 216, OUT, 10), rect(78, 212, 100, 20, BROWN, 6)])
P("abacus", "education history math", lambda: [rect(20, 30, 216, 196, BROWN_L, 10), rect(36, 46, 184, 164, CREAM, 4, None), *[line(36, 72 + r * 32, 220, 72 + r * 32, OUT, 4) for r in range(5)],
                                               *[circle(52 + c * 22 + (30 if c > r % 3 + 2 else 0), 72 + r * 32, 11, [RED, BLUE, GREEN, AMBER, VIOLET][r], OUT, 4)
                                                 for r in range(5) for c in range(5)]])
P("notebook_spiral", "education productivity", lambda: [rect(56, 20, 160, 216, WHITE, 10), *[circle(56, 44 + i * 26, 9, "none", OUT, 6) for i in range(8)],
                                                        *[line(80, 60 + i * 24, 196, 60 + i * 24, SKY, 4) for i in range(7)], line(96, 20, 96, 236, RED, 3)])
P("scissors", "education art tools", lambda: [line(70, 40, 170, 180, SILVER, 18), line(186, 40, 86, 180, SILVER, 18), circle(66, 196, 30, RED, sw=8), circle(190, 196, 30, RED, sw=8),
                                              circle(128, 110, 8, OUT, None)])
P("paint_palette", "art creativity", lambda: [path("M128,26 C200,26 240,76 236,130 C232,170 196,166 180,180 C164,196 186,230 150,232 C80,236 20,190 22,124 C24,64 70,26 128,26 Z", TAN, sw=8),
                                              *[circle(x, y, 16, c) for x, y, c in ((80, 90, RED), (126, 66, YELLOW), (176, 80, BLUE), (198, 126, GREEN), (66, 150, VIOLET))]])
P("paint_brush", "art creativity", lambda: [g([rect(112, 20, 32, 130, BROWN_L, 10), rect(108, 140, 40, 30, SILVER, 4), path("M108,170 L148,170 C150,200 140,230 128,244 C116,230 106,200 108,170 Z", RED)],
                                               "rotate(35 128 128)")])
P("crayons", "art kids education", lambda: [*[g([rect(x, 60, 36, 170, c, 6), poly([(x, 60), (x + 18, 20), (x + 36, 60)], c, sw=6), rect(x, 120, 36, 40, darken(c), 0, None)])
                                              for x, c in ((40, RED), (110, BLUE), (180, GREEN))]])
P("diploma_scroll", "education career", lambda: [rect(30, 70, 196, 116, CREAM, 6), circle(30, 128, 26, TAN), circle(226, 128, 26, TAN), line(70, 104, 186, 104, GRAY, 6), line(70, 128, 160, 128, GRAY, 6),
                                                 poly([(150, 160), (170, 220), (180, 200), (196, 220), (190, 160)], RED, sw=5), circle(172, 158, 20, RED)])
P("exam_paper", "education", lambda: [rect(44, 18, 168, 220, WHITE, 10), text(70, 64, "A+", 40, RED, anchor="start"), *[g([text(66, 104 + i * 36, f"{i + 1}.", 18, OUT, anchor="start"),
                                                                                                                       line(94, 98 + i * 36, 186, 98 + i * 36, GRAY, 5)]) for i in range(4)],
                                      circle(176, 56, 26, "none", RED, 6)])
P("brain_lightbulb", "education thinking idea psychology", lambda: [path("M128,26 C176,26 204,62 204,104 C204,138 182,154 172,174 L84,174 C74,154 52,138 52,104 C52,62 80,26 128,26 Z", YELLOW, sw=8),
                                                                   path("M88,104 C88,70 120,60 128,72 C136,60 168,70 168,104 C168,130 140,136 128,124 C116,136 88,130 88,104 Z", PINK, OUT, 5),
                                                                   rect(84, 174, 88, 24, GRAY, 6), rect(94, 198, 68, 20, GRAY_D, 6)])

# =========================================================================== home & everyday
P("house_home", "home real_estate family", lambda: [poly([(16, 124), (128, 26), (240, 124)], RED, sw=8), rect(40, 118, 176, 118, CREAM, 4), rect(104, 160, 48, 76, BROWN_L, 4),
                                                    rect(56, 142, 36, 34, SKY, 3, OUT, 5), rect(166, 142, 36, 34, SKY, 3, OUT, 5), rect(170, 46, 28, 50, GRAY_D, 2)])
P("house_for_sale", "real_estate home finance", lambda: [poly([(16, 124), (128, 26), (240, 124)], BLUE, sw=8), rect(40, 118, 176, 118, WHITE, 4), rect(104, 160, 48, 76, BROWN_L, 4),
                                                         line(60, 236, 60, 160, OUT, 8), rect(20, 150, 92, 44, RED, 6), text(66, 180, "SALE", 22, WHITE)])
P("door_open", "home self_improvement opportunity", lambda: [rect(50, 20, 156, 220, BROWN, 6), rect(64, 34, 128, 206, YELLOW, 0, None, op=0.9),
                                                             poly([(64, 34), (140, 60), (140, 222), (64, 240)], BROWN_L, sw=7), circle(126, 140, 8, GOLD)])
P("bed_sleep", "home sleep health", lambda: [rect(20, 120, 216, 70, BLUE, 12), rect(20, 70, 30, 150, BROWN, 8), rect(206, 110, 30, 110, BROWN, 8), rect(56, 96, 60, 34, WHITE, 14),
                                             path("M110,120 L236,120 L236,150 L110,150 Z", SKY, sw=7), text(170, 70, "Zz", 40, INDIGO)])
P("sofa_couch", "home", lambda: [rect(20, 100, 216, 80, TEAL, 20), rect(36, 140, 184, 50, darken(TEAL, 0.85), 10), rect(10, 120, 40, 90, TEAL, 14), rect(206, 120, 40, 90, TEAL, 14),
                                 rect(30, 206, 16, 24, BROWN, 3), rect(210, 206, 16, 24, BROWN, 3)])
P("desk_lamp", "home office productivity", lambda: [ellipse(110, 228, 70, 14, GRAY_D), line(110, 220, 80, 130, OUT, 12), line(80, 130, 150, 70, OUT, 12),
                                                    path("M140,40 L210,60 L196,120 L120,90 Z", AMBER, sw=7), poly([(200, 110), (250, 200), (150, 190)], YELLOW, None, op=0.35)])
P("office_chair", "home office", lambda: [rect(70, 20, 116, 120, SLATE, 24), rect(56, 130, 144, 34, SLATE, 14), line(128, 164, 128, 206, OUT, 12),
                                          *[line(128, 206, x, 230, OUT, 9) for x in (60, 100, 156, 196)], *[circle(x, 234, 9, GRAY_D) for x in (60, 100, 156, 196)]])
P("potted_plant", "home nature garden", lambda: [path("M70,150 L186,150 L170,236 L86,236 Z", ORANGE, sw=8), *[path(d, GREEN, sw=6) for d in
                                                                                                            ("M128,150 C100,110 70,100 50,110 C70,130 100,146 128,150 Z", "M128,150 C110,90 120,50 140,30 C150,70 144,120 128,150 Z",
                                                                                                             "M128,150 C160,110 196,100 214,110 C190,134 160,148 128,150 Z")]])
P("alarm_clock_ring", "time sleep productivity", lambda: [circle(128, 136, 84, RED, sw=9), circle(128, 136, 64, WHITE, None), line(128, 136, 128, 92, OUT, 8), line(128, 136, 160, 150, OUT, 7),
                                                          circle(62, 56, 26, AMBER), circle(194, 56, 26, AMBER), line(76, 214, 60, 238, OUT, 10), line(180, 214, 196, 238, OUT, 10),
                                                          *[line(x0, y0, x1, y1, OUT, 6) for x0, y0, x1, y1 in ((20, 110, 6, 100), (236, 110, 250, 100), (24, 150, 8, 156), (232, 150, 248, 156))]])
P("umbrella", "weather home", lambda: [path("M20,128 C20,60 70,24 128,24 C186,24 236,60 236,128 C220,112 196,112 182,128 C168,112 144,112 128,128 C112,112 88,112 74,128 C60,112 36,112 20,128 Z", VIOLET, sw=8),
                                       line(128, 128, 128, 212, OUT, 10), path("M128,212 C128,236 96,236 96,214", "none", OUT, 10)])
P("eyeglasses", "general health education", lambda: [circle(70, 140, 50, GLASS, sw=10), circle(186, 140, 50, GLASS, sw=10), path("M120,134 C126,120 130,120 136,134", "none", OUT, 9),
                                                     line(20, 128, 6, 90, OUT, 9), line(236, 128, 250, 90, OUT, 9)])
P("tshirt", "fashion shopping", lambda: [path("M80,30 C96,50 160,50 176,30 L236,64 L212,116 L186,104 L186,236 L70,236 L70,104 L44,116 L20,64 Z", SKY, sw=8)])
P("sneaker_shoe", "fashion fitness sports", lambda: [path("M20,150 C20,110 40,80 60,74 L90,74 C100,100 140,110 170,120 L220,134 C240,140 246,160 236,180 L20,180 Z", RED, sw=8),
                                                     rect(14, 176, 230, 26, WHITE, 10), *[line(76 + i * 18, 92 + i * 6, 96 + i * 18, 82 + i * 6, WHITE, 5) for i in range(3)]])
P("toothbrush", "health dental home", lambda: [g([rect(30, 118, 200, 26, SKY, 12), rect(176, 90, 50, 30, WHITE, 4), *[line(182 + i * 9, 92, 182 + i * 9, 116, SKY, 3) for i in range(5)]],
                                                  "rotate(-25 128 128)"), path(cloud_d(204, 60, 22), WHITE, OUT, 4)])
P("soap_bar", "health home hygiene", lambda: [rect(40, 110, 176, 100, PINK, 30), *[circle(x, y, r, WHITE, OUT, 4, op=0.9) for x, y, r in ((80, 80, 20), (130, 60, 14), (176, 86, 24), (110, 100, 10))]])
P("broom_clean", "home cleaning", lambda: [line(70, 20, 140, 150, BROWN_L, 12), poly([(110, 130), (170, 110), (230, 220), (120, 236)], AMBER, sw=7),
                                           *[line(140 + i * 18, 140 - i * 6, 160 + i * 20, 226 - i * 4, darken(AMBER), 4) for i in range(4)]])
P("trash_bag", "home environment", lambda: [path("M60,90 C40,140 40,236 128,236 C216,236 216,140 196,90 Z", SLATE, sw=8), poly([(96, 92), (128, 60), (160, 92)], SLATE, sw=6),
                                            path("M110,60 C100,30 156,30 146,60", "none", AMBER, 8)])
P("candle_light", "home holiday relaxation", lambda: [rect(90, 110, 76, 126, CREAM, 10), line(128, 110, 128, 90, OUT, 5), path(drop_d(128, 70, 26), ORANGE, None), path(drop_d(128, 76, 13), YELLOW, None),
                                                      circle(128, 70, 70, YELLOW, None, op=0.15)])
P("flashlight", "tools adventure", lambda: [g([rect(30, 104, 130, 48, GRAY_D, 10), poly([(160, 96), (200, 76), (200, 180), (160, 160)], SILVER, sw=7), rect(80, 116, 26, 24, RED, 4),
                                               poly([(200, 80), (256, 40), (256, 216), (200, 176)], YELLOW, None, op=0.4)], "rotate(-10 128 128)")])
P("mirror_reflection", "self_improvement psychology home", lambda: [ellipse(128, 112, 80, 100, GLASS, BROWN_L, 14), hl("M90,60 L120,50 L80,150 L66,130 Z", 0.5), rect(110, 210, 36, 30, BROWN_L, 6)])

# =========================================================================== tools & construction
P("hammer", "construction tools", lambda: [g([rect(116, 70, 26, 170, BROWN_L, 8), path("M50,40 L190,40 L206,64 L190,90 L50,90 C40,90 40,40 50,40 Z", GRAY_D)], "rotate(-30 128 128)")])
P("wrench", "construction tools industry", lambda: [g([rect(112, 70, 32, 170, SILVER, 14), path("M88,20 C70,40 74,80 104,90 L152,90 C182,80 186,40 168,20 L156,52 L100,52 Z", SILVER)],
                                                      "rotate(40 128 128)")])
P("screwdriver", "construction tools", lambda: [g([rect(112, 20, 32, 100, RED, 12), rect(122, 118, 12, 110, SILVER, 3), rect(118, 226, 20, 14, SILVER, 2)], "rotate(-40 128 128)")])
P("toolbox", "construction tools", lambda: [rect(20, 90, 216, 136, RED, 14), rect(20, 90, 216, 40, RED_D, 8), path("M90,90 L90,60 C90,46 166,46 166,60 L166,90", "none", OUT, 12),
                                            rect(110, 120, 36, 22, SILVER, 4)])
P("hard_hat_prop", "construction safety industry", lambda: [path("M30,170 C30,90 76,50 128,50 C180,50 226,90 226,170 Z", YELLOW, sw=8), rect(10, 160, 236, 30, YELLOW, 12),
                                                            rect(110, 46, 36, 124, AMBER, 6)])
P("traffic_cone", "construction safety transport", lambda: [poly([(100, 30), (156, 30), (200, 210), (56, 210)], ORANGE, sw=8), poly([(86, 90), (170, 90), (180, 130), (76, 130)], WHITE, None),
                                                            rect(30, 206, 196, 30, ORANGE, 6)])
P("brick_wall", "construction home", lambda: [*[rect(10 + c * 80 - (40 if r % 2 else 0), 30 + r * 40, 76, 36, BROWN_L if (r + c) % 2 else RED_D, 4, OUT, 5) for r in range(5) for c in range(4)]])
P("crane_construction", "construction industry", lambda: [line(70, 236, 70, 40, OUT, 14), line(70, 236, 70, 40, YELLOW, 6), line(30, 50, 236, 50, OUT, 12), line(30, 50, 236, 50, YELLOW, 5),
                                                          line(200, 50, 200, 140, OUT, 4), rect(186, 140, 28, 30, GRAY_D, 4), rect(26, 52, 40, 30, GRAY_D, 4), rect(40, 220, 60, 20, GRAY_D, 4)])
P("blueprint_plan", "construction engineering real_estate", lambda: [rect(14, 30, 228, 196, BLUE_D, 8), *[line(14, y, 242, y, SKY, 1, op=0.4) for y in range(50, 226, 20)],
                                                                     rect(46, 66, 90, 90, "none", 0, WHITE, 5), rect(136, 66, 76, 130, "none", 0, WHITE, 5), line(46, 120, 90, 120, WHITE, 5),
                                                                     path(arc_d(90, 156, 30, 270, 360), "none", WHITE, 3)])
P("paint_roller", "construction home art", lambda: [rect(40, 30, 160, 60, BLUE, 20), path("M200,60 L226,60 L226,120 L128,130 L128,160", "none", OUT, 10), rect(114, 156, 28, 84, BROWN_L, 8),
                                                    rect(30, 26, 20, 68, GRAY, 4)])
P("drill_power", "construction tools", lambda: [path("M40,70 L190,70 C204,70 210,80 210,90 L210,120 C210,130 204,136 190,136 L140,136 L120,226 L70,226 L90,136 L40,136 Z", AMBER, sw=8),
                                                rect(210, 92, 40, 20, SILVER, 4), rect(70, 200, 50, 30, GRAY_D, 6)])
P("gear_wrench", "industry engineering tools", lambda: [poly([(128 + (96 if i % 4 < 2 else 74) * math.cos(math.radians(i * 11.25)), 128 + (96 if i % 4 < 2 else 74) * math.sin(math.radians(i * 11.25)))
                                                              for i in range(32)], GRAY, sw=7), circle(128, 128, 40, WHITE),
                                                        g([rect(116, 60, 24, 140, BLUE, 10)], "rotate(45 128 128)")])

# =========================================================================== transport & travel
P("car_red", "transport travel", lambda: [path("M20,150 L36,104 C42,90 54,84 68,84 L176,84 C190,84 200,90 208,104 L232,140 C244,144 246,156 246,170 L246,190 L20,190 Z", RED, sw=8),
                                          path("M66,98 L120,98 L120,132 L50,132 Z", GLASS, OUT, 5), path("M136,98 L184,98 L208,132 L136,132 Z", GLASS, OUT, 5),
                                          circle(74, 192, 26, SLATE), circle(194, 192, 26, SLATE), circle(74, 192, 10, SILVER, None), circle(194, 192, 10, SILVER, None)])
P("taxi_cab", "transport city travel", lambda: [path("M20,150 L36,104 C42,90 54,84 68,84 L176,84 C190,84 200,90 208,104 L232,140 C244,144 246,156 246,170 L246,190 L20,190 Z", YELLOW, sw=8),
                                                rect(100, 56, 60, 28, YELLOW, 6), text(130, 78, "TAXI", 18, OUT), path("M66,98 L120,98 L120,132 L50,132 Z", GLASS, OUT, 5),
                                                path("M136,98 L184,98 L208,132 L136,132 Z", GLASS, OUT, 5), circle(74, 192, 26, SLATE), circle(194, 192, 26, SLATE)])
P("bus_city", "transport city", lambda: [rect(20, 50, 216, 160, BLUE, 18), *[rect(36 + i * 48, 70, 38, 50, GLASS, 4, OUT, 5) for i in range(4)], rect(36, 140, 184, 10, WHITE, 2, None),
                                         circle(70, 214, 22, SLATE), circle(186, 214, 22, SLATE)])
P("train_rail", "transport travel", lambda: [rect(50, 20, 156, 186, RED, 30), rect(70, 46, 116, 70, GLASS, 8), circle(86, 160, 14, YELLOW), circle(170, 160, 14, YELLOW),
                                             line(70, 206, 40, 240, OUT, 8), line(186, 206, 216, 240, OUT, 8), line(30, 236, 226, 236, OUT, 6)])
P("airplane", "transport travel", lambda: [g([path("M128,10 C140,10 146,30 146,50 L146,110 L240,160 L240,182 L146,154 L146,206 L178,230 L178,246 L128,234 L78,246 L78,230 L110,206 "
                                                   "L110,154 L16,182 L16,160 L110,110 L110,50 C110,30 116,10 128,10 Z", WHITE, sw=8)], "rotate(45 128 128)")])
P("helicopter", "transport", lambda: [line(30, 40, 226, 40, OUT, 8), line(128, 40, 128, 70, OUT, 8), ellipse(110, 120, 80, 54, RED), path("M180,110 L240,96 L240,124 L184,130 Z", RED, sw=7),
                                      path("M60,110 C60,84 90,74 110,74 L110,120 L60,120 Z", GLASS, OUT, 5), line(60, 190, 170, 190, OUT, 7), line(80, 170, 80, 190, OUT, 6), line(150, 170, 150, 190, OUT, 6)])
P("sailboat", "transport ocean travel", lambda: [poly([(128, 20), (128, 170), (44, 170)], WHITE, sw=7), poly([(140, 40), (140, 170), (210, 170)], SAND, sw=7),
                                                 path("M30,176 L226,176 L196,220 L60,220 Z", BROWN_L, sw=8), path("M10,226 C60,212 100,240 150,226 C190,214 220,236 250,226", "none", BLUE, 7)])
P("cargo_ship", "transport logistics ocean", lambda: [path("M14,150 L242,150 L214,212 L42,212 Z", RED, sw=8), *[rect(40 + i * 46, 104, 42, 46, c, 3) for i, c in enumerate((BLUE, GREEN, AMBER, TEAL))],
                                                      rect(190, 70, 36, 80, WHITE, 4), path("M10,226 C60,212 100,240 150,226 C190,214 220,236 250,226", "none", BLUE, 7)])
P("bicycle", "transport fitness sports", lambda: [circle(62, 170, 46, "none", OUT, 10), circle(194, 170, 46, "none", OUT, 10), pline([(62, 170), (110, 100), (180, 100), (194, 170)], TEAL, 10),
                                                  pline([(110, 100), (128, 170), (180, 100)], TEAL, 10), line(100, 80, 130, 80, OUT, 10), line(176, 100, 170, 72, OUT, 8), line(158, 70, 186, 70, OUT, 8)])
P("motorbike", "transport", lambda: [circle(56, 180, 40, SLATE), circle(200, 180, 40, SLATE), path("M56,180 L100,120 L170,120 L200,180", "none", OUT, 10),
                                     path("M90,130 L120,100 L180,104 L190,140 L110,146 Z", ORANGE, sw=7), line(170, 100, 190, 70, OUT, 8), circle(56, 180, 14, SILVER, None), circle(200, 180, 14, SILVER, None)])
P("electric_scooter", "transport city", lambda: [line(180, 50, 196, 190, OUT, 18), line(180, 50, 196, 190, TEAL, 8), line(160, 50, 200, 46, OUT, 12),
                                                 rect(50, 180, 160, 18, TEAL, 8), circle(60, 206, 24, SLATE), circle(200, 206, 24, SLATE), circle(60, 206, 9, SILVER, None),
                                                 circle(200, 206, 9, SILVER, None), poly(bolt_pts(120, 150, 28), YELLOW, OUT, 4)])
P("suitcase_travel", "travel", lambda: [rect(40, 60, 176, 160, ORANGE, 20), path("M96,60 L96,36 C96,26 160,26 160,36 L160,60", "none", OUT, 10), *[line(x, 60, x, 220, OUT, 6) for x in (88, 168)],
                                        circle(70, 230, 10, OUT, None), circle(186, 230, 10, OUT, None), rect(100, 120, 56, 30, WHITE, 6)])
P("passport_ticket", "travel", lambda: [rect(40, 26, 140, 200, BLUE_D, 12), circle(110, 106, 34, "none", 0, GOLD, 5), text(110, 186, "PASS", 22, GOLD),
                                        g([rect(130, 120, 110, 60, WHITE, 8), line(204, 120, 204, 180, GRAY, 3, stroke_dasharray="6 5"), text(166, 158, "✈", 30, BLUE)], "rotate(-12 185 150)")])
P("map_folded", "travel navigation adventure", lambda: [poly([(20, 50), (90, 30), (166, 50), (236, 30), (236, 206), (166, 226), (90, 206), (20, 226)], SAND, sw=8),
                                                        line(90, 30, 90, 206, OUT, 5), line(166, 50, 166, 226, OUT, 5), path("M40,190 C80,150 110,190 140,140 C160,110 190,120 210,80", "none", RED, 5,
                                                                                                                             stroke_dasharray="10 8"),
                                                        line(196, 70, 220, 94, RED, 7), line(220, 70, 196, 94, RED, 7)])
P("tent_camping", "travel adventure nature", lambda: [poly([(128, 30), (240, 220), (16, 220)], GREEN, sw=8), poly([(128, 90), (170, 220), (86, 220)], GREEN_D, sw=6), line(128, 30, 128, 10, OUT, 6),
                                                      line(6, 224, 250, 224, OUT, 8)])
P("binoculars", "travel adventure mystery", lambda: [circle(76, 160, 52, SLATE), circle(180, 160, 52, SLATE), circle(76, 160, 30, GLASS, None), circle(180, 160, 30, GLASS, None),
                                                     rect(52, 70, 48, 70, INK, 8), rect(156, 70, 48, 70, INK, 8), rect(100, 90, 56, 30, GRAY_D, 6)])
P("traffic_light", "transport city safety", lambda: [rect(80, 14, 96, 200, INK, 18), circle(128, 56, 24, RED), circle(128, 112, 24, "#713f12"), circle(128, 168, 24, "#14532d"),
                                                     rect(116, 214, 24, 30, GRAY_D, 2)])
P("fuel_pump", "transport energy", lambda: [rect(50, 40, 112, 196, GREEN, 14), rect(70, 64, 72, 56, WHITE, 6), path("M162,90 L196,90 L210,110 L210,200 C210,214 192,216 192,200 L192,130", "none", OUT, 10),
                                            rect(36, 228, 140, 12, OUT, 4, None)])
P("ev_charger", "transport energy tech environment", lambda: [rect(50, 30, 112, 206, TEAL, 16), rect(70, 54, 72, 60, WHITE, 6), poly(bolt_pts(106, 84, 26), YELLOW, OUT, 4),
                                                             path("M162,150 C220,150 230,210 200,230", "none", OUT, 10), rect(186, 216, 34, 26, GRAY_D, 6)])
P("road_sign_turn", "transport navigation", lambda: [line(128, 128, 128, 246, GRAY_D, 12), poly([(128, 10), (246, 128), (128, 246), (10, 128)], YELLOW, sw=9),
                                                     path("M110,180 L110,120 C110,100 120,92 140,92 L160,92", "none", OUT, 18), poly([(150, 66), (190, 92), (150, 118)], OUT, None)])
P("anchor_ship", "ocean travel history", lambda: [circle(128, 44, 22, "none", OUT, 22), line(128, 66, 128, 220, OUT, 28), line(84, 96, 172, 96, OUT, 24),
                                                  path("M40,150 C40,210 216,210 216,150", "none", OUT, 28), circle(128, 44, 22, "none", SILVER, 10), line(128, 66, 128, 220, SILVER, 14),
                                                  line(84, 96, 172, 96, SILVER, 12), path("M40,150 C40,210 216,210 216,150", "none", SILVER, 14),
                                                  poly([(22, 164), (52, 136), (58, 172)], SILVER, sw=5), poly([(234, 164), (204, 136), (198, 172)], SILVER, sw=5)])
P("hot_air_balloon", "travel adventure", lambda: [path("M128,20 C190,20 220,70 210,120 C200,160 160,180 150,196 L106,196 C96,180 56,160 46,120 C36,70 66,20 128,20 Z", RED, sw=8),
                                                  path("M128,20 C150,40 156,120 140,196 L116,196 C100,120 106,40 128,20 Z", YELLOW, OUT, 5), line(108, 196, 100, 214, OUT, 5), line(148, 196, 156, 214, OUT, 5),
                                                  rect(96, 212, 64, 32, BROWN_L, 6)])

# =========================================================================== sports & fitness
P("dumbbell", "fitness sports health", lambda: [rect(60, 110, 136, 36, GRAY, 6), rect(30, 70, 40, 116, SLATE, 10), rect(186, 70, 40, 116, SLATE, 10), rect(12, 90, 24, 76, SLATE, 8), rect(220, 90, 24, 76, SLATE, 8)])
P("kettlebell", "fitness sports", lambda: [path("M90,96 L90,70 C90,30 166,30 166,70 L166,96", "none", OUT, 22), path("M90,96 L90,70 C90,30 166,30 166,70 L166,96", "none", SLATE, 10),
                                           circle(128, 160, 76, SLATE), hl_ellipse(100, 132, 18, 12, 0.3, -30)])
P("barbell", "fitness sports", lambda: [rect(10, 118, 236, 20, SILVER, 6), *[rect(x, 64, 22, 128, RED if x in (36, 198) else SLATE, 6) for x in (36, 62, 172, 198)]])
P("soccer_ball", "sports", lambda: [circle(128, 128, 104, WHITE, sw=9), poly(reg_pts(128, 128, 34, 5), OUT, None), *[poly(reg_pts(128 + 80 * math.cos(math.radians(a)), 128 + 80 * math.sin(math.radians(a)), 26, 5, a + 90),
                                                                                                                     OUT, None) for a in (-90, -18, 54, 126, 198)],
                                    *[line(128 + 34 * math.cos(math.radians(a)), 128 + 34 * math.sin(math.radians(a)), 128 + 60 * math.cos(math.radians(a)), 128 + 60 * math.sin(math.radians(a)), OUT, 6)
                                      for a in (-90, -18, 54, 126, 198)]])
P("basketball", "sports", lambda: [circle(128, 128, 104, ORANGE, sw=9), line(24, 128, 232, 128, OUT, 6), line(128, 24, 128, 232, OUT, 6), path("M60,48 C100,90 100,166 60,208", "none", OUT, 6),
                                   path("M196,48 C156,90 156,166 196,208", "none", OUT, 6)])
P("american_football", "sports", lambda: [ellipse(128, 128, 110, 66, BROWN_L, transform="rotate(-30 128 128)"), g([line(90, 128, 166, 128, WHITE, 6), *[line(x, 116, x, 140, WHITE, 5) for x in (104, 118, 132, 146)]],
                                                                                                                   "rotate(-30 128 128)")])
P("tennis_racket", "sports", lambda: [g([ellipse(128, 90, 70, 84, "none", OUT, 14), ellipse(128, 90, 70, 84, "none", RED, 7), *[line(128 + d, 14, 128 + d, 166, GRAY, 2) for d in range(-50, 60, 14)],
                                         *[line(62, 90 + d, 194, 90 + d, GRAY, 2) for d in range(-60, 70, 14)], rect(116, 172, 24, 76, OUT, 8)], "rotate(30 128 128)"),
                                      circle(208, 208, 26, LIME)])
P("baseball_bat", "sports", lambda: [g([path("M116,236 L112,120 C108,60 116,20 128,20 C140,20 148,60 144,120 L140,236 Z", TAN, sw=7), rect(110, 220, 36, 24, OUT, 6)], "rotate(40 128 128)"),
                                     circle(196, 70, 28, WHITE), path("M180,52 C192,66 192,76 180,90 M212,52 C200,66 200,76 212,90", "none", RED, 4)])
P("boxing_glove", "sports fitness", lambda: [path("M60,110 C50,50 110,20 160,30 C210,40 230,90 220,140 C212,180 180,196 150,196 L80,196 C70,170 62,140 60,110 Z", RED, sw=8),
                                             path("M60,110 C80,96 110,100 120,120", "none", OUT, 6), rect(72, 192, 100, 46, WHITE, 8)])
P("running_shoe", "fitness sports", lambda: [path("M14,160 C14,120 30,96 52,90 L82,90 C92,112 132,120 162,128 L214,140 C236,146 246,166 236,184 L14,184 Z", BLUE, sw=8),
                                             rect(8, 180, 240, 24, WHITE, 10), path("M60,100 L120,160 M90,100 L150,150", "none", WHITE, 5)])
P("yoga_mat", "fitness health mental_health", lambda: [rect(20, 160, 216, 30, VIOLET, 10), ellipse(220, 175, 26, 36, PURPLE), circle(120, 70, 24, WHITE, OUT, 6),
                                                       path("M120,96 L120,140 M80,110 L160,110 M120,140 L84,160 M120,140 L156,160", "none", OUT, 9)])
P("jump_rope", "fitness sports kids", lambda: [path("M40,40 C20,200 236,200 216,40", "none", OUT, 12), path("M40,40 C20,200 236,200 216,40", "none", AMBER, 6), rect(28, 20, 24, 50, RED, 8), rect(204, 20, 24, 50, RED, 8)])
P("whistle_coach", "sports education", lambda: [circle(110, 150, 66, SILVER, sw=8), rect(110, 84, 120, 50, SILVER, 12), circle(110, 150, 24, GRAY_D, None), path("M60,100 C40,60 70,30 100,40",
                                                                                                                                                          "none", RED, 8)])
P("weight_scale", "health fitness", lambda: [rect(26, 70, 204, 160, WHITE, 26), rect(70, 92, 116, 50, INK, 10), text(128, 128, "72.5", 28, "#4ade80", family="DejaVu Sans Mono"),
                                             *[circle(x, 196, 12, SILVER, None) for x in (80, 176)]])
P("heart_rate_watch", "fitness health tech", lambda: [rect(92, 6, 72, 60, TEAL, 10), rect(92, 190, 72, 60, TEAL, 10), circle(128, 128, 76, INK, sw=8), circle(128, 128, 60, "#0b1d33", None),
                                                      text(128, 128, "128", 34, WHITE), text(128, 158, "BPM", 16, RED)])
P("finish_line_flag", "sports winner goal", lambda: [line(50, 20, 50, 240, OUT, 10), *[rect(56 + c * 30, 26 + r * 30, 30, 30, OUT if (r + c) % 2 else WHITE, 0, None) for r in range(4) for c in range(6)],
                                                     rect(56, 26, 180, 120, "none", 0, OUT, 6)])
P("podium_winners", "sports winner competition", lambda: [rect(90, 90, 76, 146, GOLD, 4), rect(14, 140, 76, 96, SILVER, 4), rect(166, 170, 76, 66, AMBER, 4),
                                                          text(128, 160, "1", 50, WHITE), text(52, 200, "2", 40, WHITE), text(204, 216, "3", 36, WHITE), poly(star_pts(128, 50, 32, 13), GOLD, sw=6)])
P("golf_flag", "sports", lambda: [ellipse(128, 220, 100, 22, GREEN), line(128, 220, 128, 40, OUT, 7), poly([(130, 40), (200, 64), (130, 88)], RED, sw=6), circle(170, 210, 12, WHITE)])
P("skateboard", "sports kids", lambda: [rect(10, 110, 236, 34, PINK, 17), *[circle(x, 166, 18, AMBER) for x in (60, 196)], rect(50, 140, 20, 10, GRAY, 2), rect(186, 140, 20, 10, GRAY, 2)])
P("swimming_goggles", "sports fitness", lambda: [ellipse(76, 130, 50, 36, SKY, sw=9), ellipse(180, 130, 50, 36, SKY, sw=9), line(126, 130, 130, 130, OUT, 10),
                                                 path("M26,130 C10,170 246,170 230,130", "none", BLUE, 8)])

# =========================================================================== music & entertainment
P("music_note", "music entertainment", lambda: [path("M96,190 L96,50 L210,30 L210,170", "none", OUT, 16), ellipse(72, 194, 34, 26, VIOLET, transform="rotate(-20 72 194)"),
                                                ellipse(186, 174, 34, 26, VIOLET, transform="rotate(-20 186 174)"), poly([(96, 50), (210, 30), (210, 66), (96, 86)], OUT, None)])
P("guitar", "music entertainment", lambda: [g([path("M96,140 C50,140 30,180 50,216 C70,250 130,246 140,210 C170,206 186,180 176,156 C166,132 130,140 118,130 Z", AMBER, sw=8),
                                               circle(110, 186, 18, OUT, None), rect(140, 20, 22, 130, BROWN, 4, transform="rotate(35 151 85)"), rect(176, 4, 40, 34, BROWN, 6, transform="rotate(35 196 21)")])])
P("piano_keys", "music", lambda: [rect(10, 60, 236, 140, WHITE, 8), *[line(10 + i * 33.7, 60, 10 + i * 33.7, 200, OUT, 5) for i in range(1, 7)],
                                  *[rect(10 + i * 33.7 - 11, 60, 22, 80, OUT, 3, None) for i in (1, 2, 4, 5, 6)]])
P("drum_kit", "music entertainment", lambda: [ellipse(128, 100, 90, 26, WHITE), path("M38,100 L38,190 C38,220 218,220 218,190 L218,100", RED, sw=8), ellipse(128, 100, 90, 26, WHITE),
                                              line(80, 20, 120, 90, BROWN_L, 8), line(180, 20, 140, 90, BROWN_L, 8), *[line(x, 110, x + 30, 200, GOLD, 4) for x in (60, 120, 180)]])
P("vinyl_record", "music entertainment", lambda: [circle(128, 128, 108, INK, sw=8), *[circle(128, 128, r, "none", SLATE, 2) for r in (90, 76, 62)], circle(128, 128, 40, RED, None), circle(128, 128, 8, WHITE, None)])
P("film_reel", "entertainment media", lambda: [circle(128, 128, 104, GRAY_D, sw=8), *[circle(128 + 56 * math.cos(math.radians(a)), 128 + 56 * math.sin(math.radians(a)), 22, INK, None) for a in range(0, 360, 72)],
                                               circle(128, 128, 14, SILVER, None)])
P("clapperboard", "entertainment media", lambda: [rect(20, 96, 216, 140, INK, 10), g([rect(20, 60, 216, 40, WHITE, 4), *[poly([(30 + i * 44, 60), (54 + i * 44, 60), (40 + i * 44, 100), (16 + i * 44, 100)], OUT, None)
                                                                                                                for i in range(5)]], "rotate(-12 20 100)"),
                                                  line(40, 150, 216, 150, WHITE, 4), text(40, 196, "TAKE 1", 28, WHITE, anchor="start")])
P("theater_masks", "art entertainment", lambda: [g([path("M30,40 L130,40 L130,120 C130,170 80,200 70,200 C60,200 30,170 30,120 Z", YELLOW, sw=7), circle(60, 90, 9, OUT, None), circle(100, 90, 9, OUT, None),
                                                    path("M56,140 C70,160 90,160 104,140", "none", OUT, 7)], "rotate(-10 80 120)"),
                                                 g([path("M126,70 L226,70 L226,150 C226,200 176,230 166,230 C156,230 126,200 126,150 Z", SKY, sw=7), circle(156, 120, 9, OUT, None), circle(196, 120, 9, OUT, None),
                                                    path("M152,190 C166,170 186,170 200,190", "none", OUT, 7)], "rotate(10 176 150)")])
P("ticket_admit", "entertainment travel", lambda: [path("M20,70 L236,70 L236,110 C220,110 220,146 236,146 L236,186 L20,186 L20,146 C36,146 36,110 20,110 Z", GOLD, sw=8),
                                                   line(176, 76, 176, 180, OUT, 4, stroke_dasharray="8 7"), text(98, 140, "ADMIT", 32, OUT)])
P("dice_pair", "game entertainment mystery", lambda: [g([rect(26, 70, 110, 110, WHITE, 18), *[circle(x, y, 10, OUT, None) for x, y in ((56, 100), (106, 150), (81, 125))]], "rotate(-15 81 125)"),
                                                      g([rect(126, 90, 110, 110, RED, 18), *[circle(x, y, 10, WHITE, None) for x, y in ((156, 120), (206, 120), (156, 170), (206, 170))]], "rotate(12 181 145)")])
P("playing_cards", "game entertainment", lambda: [g([rect(40, 40, 120, 170, WHITE, 12), text(70, 76, "A", 26, RED), path(heart_d(100, 130, 30), RED, None)], "rotate(-12 100 125)"),
                                                  g([rect(100, 50, 120, 170, WHITE, 12), text(130, 86, "K", 26, OUT), poly(star_pts(160, 140, 30, 12), OUT, None)], "rotate(10 160 135)")])
P("chess_board", "game strategy", lambda: [*[rect(28 + c * 25, 28 + r * 25, 25, 25, BROWN if (r + c) % 2 else CREAM, 0, None) for r in range(8) for c in range(8)], rect(28, 28, 200, 200, "none", 0, OUT, 8)])
P("joystick_arcade", "gaming", lambda: [rect(30, 150, 196, 80, RED, 14), line(128, 150, 128, 70, OUT, 12), circle(128, 60, 30, RED), circle(186, 186, 14, YELLOW), circle(70, 186, 14, SKY)])
P("trophy_esports", "gaming winner", lambda: [path("M70,40 L186,40 L180,110 C176,146 152,164 128,164 C104,164 80,146 76,110 Z", SILVER, sw=9), rect(112, 162, 32, 36, GRAY, 4), rect(72, 196, 112, 34, INK, 8),
                                              rect(98, 70, 60, 34, INK, 10), circle(114, 87, 6, CYAN, None), circle(142, 87, 6, PINK, None)])
P("magic_wand", "magic entertainment kids", lambda: [line(40, 216, 170, 86, OUT, 16), line(40, 216, 170, 86, INK, 8), line(150, 106, 170, 86, WHITE, 8), poly(star_pts(188, 66, 40, 16), YELLOW, sw=6),
                                                     poly(star_pts(80, 70, 16, 6, 4, 0), YELLOW, sw=3), poly(star_pts(220, 150, 14, 5, 4, 0), YELLOW, sw=3)])
P("magic_hat_rabbit", "magic entertainment", lambda: [ellipse(96, 50, 16, 40, WHITE), ellipse(144, 50, 16, 40, WHITE), rect(54, 90, 148, 130, INK, 10), rect(54, 160, 148, 26, RED, 0, None),
                                                      rect(20, 210, 216, 26, INK, 12)])

# =========================================================================== holiday & celebration
P("balloons", "celebration holiday kids", lambda: [*[g([line(x, y + 50, 128, 240, OUT, 3), ellipse(x, y, 40, 50, c), poly([(x - 6, y + 50), (x + 6, y + 50), (x, y + 60)], c, sw=4)])
                                                     for x, y, c in ((76, 80, RED), (180, 70, BLUE), (128, 110, YELLOW))]])
P("party_popper", "celebration holiday", lambda: [poly([(40, 236), (90, 110), (160, 180)], GOLD, sw=8), *[rect(x, y, 14, 6, c, 2, None, transform=f"rotate({a} {x} {y})")
                                                                                                      for x, y, c, a in ((150, 60, RED, 30), (190, 100, BLUE, -20), (120, 40, GREEN, 60),
                                                                                                                         (210, 60, PINK, 10), (180, 140, YELLOW, 45), (100, 80, VIOLET, -30))],
                                                  *[circle(x, y, 7, c, None) for x, y, c in ((160, 30, YELLOW), (220, 130, RED), (130, 100, SKY))]])
P("fireworks", "celebration holiday", lambda: [*[line(128, 110, 128 + 90 * math.cos(math.radians(a)), 110 + 90 * math.sin(math.radians(a)), [RED, YELLOW, SKY, PINK][i % 4], 7)
                                                 for i, a in enumerate(range(0, 360, 24))], circle(128, 110, 14, WHITE, None), line(128, 240, 128, 200, GRAY, 4, stroke_dasharray="6 6")])
P("christmas_tree", "holiday celebration", lambda: [rect(112, 200, 32, 40, BROWN, 4), poly([(128, 30), (200, 120), (170, 120), (220, 200), (36, 200), (86, 120), (56, 120)], GREEN_D, sw=8),
                                                    poly(star_pts(128, 30, 26, 11), YELLOW, sw=5), *[circle(x, y, 9, c) for x, y, c in ((100, 110, RED), (150, 140, SKY), (110, 170, YELLOW), (170, 180, RED))]])
P("pumpkin_lantern", "holiday spooky", lambda: [ellipse(128, 146, 104, 84, ORANGE), *[ellipse(128, 146, r, 84, "none", OUT, 5) for r in (40, 74)], rect(116, 46, 24, 30, GREEN_D, 4),
                                                poly([(84, 120), (108, 120), (96, 100)], OUT, None), poly([(148, 120), (172, 120), (160, 100)], OUT, None),
                                                path("M80,170 L96,180 L112,168 L128,182 L144,168 L160,180 L176,170 L160,196 L96,196 Z", OUT, None)])
P("ghost_cute", "holiday spooky kids", lambda: [path("M48,236 L48,110 C48,56 84,22 128,22 C172,22 208,56 208,110 L208,236 L182,214 L156,236 L128,214 L100,236 L74,214 Z", WHITE, sw=8),
                                                ellipse(100, 106, 12, 18, OUT, None), ellipse(156, 106, 12, 18, OUT, None), ellipse(128, 150, 14, 18, OUT, None)])
P("snowman", "holiday weather kids", lambda: [circle(128, 176, 62, WHITE), circle(128, 86, 44, WHITE), poly([(128, 88), (170, 96), (128, 100)], ORANGE, None), circle(112, 76, 6, OUT, None),
                                              circle(144, 76, 6, OUT, None), rect(92, 28, 72, 22, INK, 4), rect(104, 0, 48, 34, INK, 4), rect(84, 124, 88, 14, RED, 6)])
P("wedding_rings", "love relationships celebration", lambda: [circle(96, 150, 62, "none", GOLD, 16), circle(160, 150, 62, "none", AMBER, 16), poly([(160, 72), (186, 96), (160, 120), (134, 96)], SKY, sw=5)])
P("lantern_festival", "holiday celebration culture", lambda: [line(128, 10, 128, 40, OUT, 6), path("M70,60 L186,60 L210,120 L186,200 L70,200 L46,120 Z", RED, sw=8), rect(84, 40, 88, 24, GOLD, 4),
                                                              rect(84, 196, 88, 22, GOLD, 4), *[line(x, 60, x, 200, darken(RED), 4) for x in (100, 128, 156)], circle(128, 130, 30, YELLOW, None, op=0.5),
                                                              line(128, 218, 128, 246, GOLD, 5)])
P("crescent_star", "holiday night culture", lambda: [path("M150,30 C90,30 40,76 40,136 C40,196 90,236 150,236 C110,210 90,176 90,134 C90,90 112,54 150,30 Z", GOLD, sw=8),
                                                     poly(star_pts(176, 104, 36, 15), GOLD, sw=6)])
P("confetti_burst", "celebration", lambda: [*[rect(30 + (i * 53) % 200, 20 + (i * 37) % 210, 18, 8, [RED, YELLOW, SKY, PINK, GREEN, VIOLET][i % 6], 2, None,
                                                   transform=f"rotate({(i * 47) % 180} {39 + (i * 53) % 200} {24 + (i * 37) % 210})") for i in range(28)]])
P("love_letter", "love relationships", lambda: [rect(20, 60, 216, 150, PINK, 12), pline([(24, 66), (128, 150), (232, 66)], OUT, 7), path(heart_d(128, 140, 30), RED, OUT, 5)])

# =========================================================================== energy & industry & environment
P("solar_panel", "energy environment tech", lambda: [g([rect(20, 50, 216, 130, BLUE_D, 6), *[line(20 + i * 43.2, 50, 20 + i * 43.2, 180, SKY, 3) for i in range(1, 5)],
                                                        *[line(20, 50 + i * 43.3, 236, 50 + i * 43.3, SKY, 3) for i in range(1, 3)]], "skewX(-12) translate(26 0)"),
                                                     line(128, 180, 128, 236, OUT, 10), circle(220, 30, 22, YELLOW)])
P("wind_turbine", "energy environment", lambda: [poly([(120, 100), (136, 100), (146, 240), (110, 240)], WHITE, sw=6), circle(128, 96, 12, SILVER),
                                                 *[g([path("M128,96 C120,60 122,30 128,12 C134,30 136,60 128,96 Z", WHITE, sw=5)], f"rotate({a} 128 96)") for a in (0, 120, 240)]])
P("power_plant", "energy industry", lambda: [path("M30,236 C46,180 46,120 34,70 L110,70 C98,120 98,180 114,236 Z", SILVER, sw=7), path("M130,236 C146,180 146,140 136,100 L200,100 C190,140 190,180 206,236 Z",
                                                                                                                                      SILVER, sw=7),
                                             path(cloud_d(76, 48, 30), WHITE, None, op=0.9), path(cloud_d(170, 80, 24), WHITE, None, op=0.9)])
P("oil_barrel", "energy industry finance", lambda: [rect(56, 30, 144, 200, INK, 14), *[line(56, y, 200, y, SLATE, 8) for y in (80, 180)], ellipse(128, 32, 72, 14, SLATE),
                                                    path(drop_d(128, 136, 30), AMBER, None)])
P("water_tap", "environment home", lambda: [rect(20, 60, 60, 40, GRAY, 8), path("M80,70 L170,70 C196,70 206,90 206,110 L206,130 L170,130 L170,110 L80,110 Z", SILVER, sw=7),
                                            rect(110, 40, 40, 20, BLUE, 4), path(drop_d(188, 176, 22), SKY, OUT, 5), path(drop_d(188, 226, 14), SKY, OUT, 4)])
P("factory_pollution", "environment industry", lambda: [poly([(16, 236), (16, 140), (72, 170), (72, 140), (128, 170), (128, 140), (184, 170), (184, 236)], GRAY_D, sw=8),
                                                        rect(184, 80, 36, 156, SLATE, 4), path(cloud_d(190, 50, 36), GRAY, None, op=0.9), path(cloud_d(130, 34, 26), GRAY, None, op=0.7)])
P("power_plug", "energy tech", lambda: [rect(80, 80, 96, 100, SLATE, 16), rect(98, 30, 18, 56, SILVER, 4), rect(140, 30, 18, 56, SILVER, 4), path("M128,180 C128,230 60,220 40,250", "none", OUT, 12)])
P("lightning_cloud_energy", "energy weather", lambda: [path(cloud_d(128, 86, 86), GRAY_D, sw=8), poly(bolt_pts(128, 176, 70), YELLOW, sw=7)])

# =========================================================================== law, justice, history
P("scales_justice", "law", lambda: [line(128, 30, 128, 220, OUT, 12), rect(80, 214, 96, 22, GOLD, 6), line(40, 70, 216, 70, OUT, 10), circle(128, 40, 12, GOLD),
                                    *[g([line(x, 70, x - 34, 150, OUT, 4), line(x, 70, x + 34, 150, OUT, 4), path(f"M{x - 44},150 C{x - 44},190 {x + 44},190 {x + 44},150 Z", GOLD, sw=7)])
                                      for x in (56, 200)]])
P("gavel_judge", "law", lambda: [g([rect(110, 90, 26, 150, BROWN_L, 8), rect(60, 40, 126, 60, BROWN, 14), rect(50, 50, 20, 40, GOLD, 4), rect(176, 50, 20, 40, GOLD, 4)], "rotate(-35 128 128)"),
                                 rect(120, 206, 120, 30, BROWN, 8)])
P("courthouse", "law history", lambda: [poly([(10, 86), (128, 20), (246, 86)], CREAM, sw=8), *[rect(30 + i * 42, 90, 24, 120, WHITE, 3) for i in range(5)], rect(16, 206, 224, 30, CREAM, 6)])
P("handcuffs", "law crime", lambda: [circle(80, 150, 50, "none", SILVER, 16), circle(176, 150, 50, "none", SILVER, 16), path("M110,110 C120,90 136,90 146,110", "none", GRAY_D, 10)])
P("police_siren", "law safety emergency", lambda: [path("M60,150 C60,80 196,80 196,150 Z", RED, sw=8), rect(40, 150, 176, 40, GRAY_D, 8), *[line(x0, y0, x1, y1, RED, 8) for x0, y0, x1, y1 in
                                                                                                                                         ((30, 90, 10, 70), (226, 90, 246, 70), (128, 60, 128, 30))]])
P("detective_magnifier", "mystery law", lambda: [line(150, 150, 222, 222, OUT, 30), line(150, 150, 222, 222, BROWN, 18), circle(104, 104, 74, GLASS, sw=14),
                                                 path(drop_d(104, 104, 26), OUT, None, op=0.0), ellipse(104, 110, 26, 30, "none", BROWN, 6), *[path(arc_d(104, 110, r, 210, 330), "none", BROWN, 5) for r in (14, 22)]])
P("pyramid_egypt", "history travel archaeology", lambda: [poly([(128, 30), (240, 220), (16, 220)], SAND, sw=8), poly([(128, 30), (240, 220), (150, 220)], TAN, None),
                                                          *[line(40 + i * 12, 220 - i * 30, 216 - i * 12, 220 - i * 30, darken(SAND), 3) for i in range(1, 6)], circle(210, 50, 22, YELLOW)])
P("greek_column", "history", lambda: [rect(50, 20, 156, 30, CREAM, 4), rect(70, 50, 116, 160, WHITE, 2), *[line(x, 56, x, 204, GRAY, 4) for x in (94, 118, 142, 166)],
                                      rect(50, 210, 156, 30, CREAM, 4)])
P("castle_tower", "history storytelling", lambda: [rect(40, 90, 176, 146, GRAY, 4), *[rect(40 + i * 44, 64, 28, 30, GRAY, 2) for i in range(5)], path("M100,236 L100,180 C100,150 156,150 156,180 L156,236 Z", BROWN, sw=7),
                                                   rect(116, 20, 6, 50, OUT, 0, None), poly([(122, 20), (160, 32), (122, 44)], RED, sw=5)])
P("sword_knight", "history storytelling game", lambda: [g([rect(118, 10, 20, 170, SILVER, 4), poly([(118, 10), (128, 0), (138, 10)], SILVER, sw=5), rect(80, 176, 96, 18, GOLD, 6), rect(118, 192, 20, 40, BROWN, 4),
                                                           circle(128, 238, 12, GOLD)], "rotate(30 128 128)")])
P("shield_knight", "history storytelling game", lambda: [path("M128,16 L222,46 C222,140 186,206 128,240 C70,206 34,140 34,46 Z", BLUE, sw=9), path("M128,16 L128,240", "none", GOLD, 10),
                                                         line(44, 110, 212, 110, GOLD, 10)])
P("treasure_chest", "adventure history mystery", lambda: [rect(26, 110, 204, 120, BROWN_L, 10), path("M26,110 C26,50 230,50 230,110 Z", BROWN, sw=8), rect(112, 100, 32, 40, GOLD, 6),
                                                          *[rect(x, 60, 16, 170, GOLD, 2) for x in (54, 186)], circle(128, 70, 30, YELLOW, None, op=0.4)])
P("scroll_ancient", "history education mystery", lambda: [rect(56, 40, 144, 176, CREAM, 2), *[rect(40, y, 176, 30, TAN, 15) for y in (24, 202)], *[line(76, 80 + i * 24, 180, 80 + i * 24, BROWN_L, 5) for i in range(5)]])
P("hourglass_ancient", "history time mystery", lambda: [rect(50, 14, 156, 22, BROWN, 8), rect(50, 220, 156, 22, BROWN, 8), line(60, 36, 60, 220, BROWN, 8), line(196, 36, 196, 220, BROWN, 8),
                                                        path("M80,40 L176,40 C176,100 136,116 136,128 C136,140 176,156 176,216 L80,216 C80,156 120,140 120,128 C120,116 80,100 80,40 Z", GLASS),
                                                        path("M128,150 L166,210 L90,210 Z", SAND, None)])
P("viking_helmet", "history", lambda: [path("M50,150 C50,80 206,80 206,150 Z", SILVER, sw=8), rect(40, 140, 176, 26, GOLD, 8), path("M60,110 C30,100 20,60 30,40 C40,70 56,86 76,96 Z", CREAM, sw=6),
                                       path("M196,110 C226,100 236,60 226,40 C216,70 200,86 180,96 Z", CREAM, sw=6)])

# =========================================================================== mind, emotions & self-improvement
P("meditation_lotus", "mental_health self_improvement psychology", lambda: [*[path(f"M128,200 C{128 + dx},{150} {128 + dx * 0.6},{90} 128,{60 + abs(dx) * 0.3} C{128 - dx * 0.2},{110} 128,{160} 128,200 Z",
                                                                                   PINK, sw=6, transform=f"rotate({a} 128 200)") for dx, a in ((60, -50), (60, -25), (60, 0), (60, 25), (60, 50))],
                                                                         ellipse(128, 206, 80, 14, GREEN, sw=6)])
P("broken_chain", "self_improvement addiction motivation", lambda: [*[rect(x, 104, 70, 48, "none", 24, OUT, 16) for x in (10, 176)], *[rect(x, 104, 70, 48, "none", 24, SILVER, 8) for x in (10, 176)],
                                                                    path("M96,112 C110,100 120,110 116,124 M160,144 C146,156 136,146 140,132", "none", SILVER, 12),
                                                                    *[line(128 + 30 * math.cos(math.radians(a)), 128 + 30 * math.sin(math.radians(a)), 128 + 50 * math.cos(math.radians(a)),
                                                                           128 + 50 * math.sin(math.radians(a)), YELLOW, 6) for a in (-90, -30, 90, 150)]])
P("maze_puzzle", "psychology strategy thinking", lambda: [rect(20, 20, 216, 216, WHITE, 10), pline([(48, 48), (208, 48), (208, 112), (80, 112), (80, 176), (208, 176)], OUT, 12),
                                                          pline([(48, 80), (48, 208), (176, 208)], OUT, 12), pline([(112, 144), (176, 144)], OUT, 12), circle(64, 96, 10, GREEN, None),
                                                          poly(star_pts(196, 208, 14, 6), RED, None)])
P("journal_diary", "self_improvement mental_health productivity", lambda: [rect(50, 20, 160, 216, VIOLET, 14), rect(50, 20, 24, 216, PURPLE, 8), rect(96, 60, 92, 50, WHITE, 6),
                                                                           path(heart_d(142, 84, 14), PINK, None), rect(180, 130, 30, 70, YELLOW, 2)])
P("happy_face_emoji", "mental_health psychology", lambda: [circle(128, 128, 104, YELLOW, sw=9), circle(92, 104, 13, OUT, None), circle(164, 104, 13, OUT, None),
                                                           path("M72,146 C90,196 166,196 184,146 Z", OUT, None)])
P("sad_face_emoji", "mental_health psychology", lambda: [circle(128, 128, 104, YELLOW, sw=9), circle(92, 104, 13, OUT, None), circle(164, 104, 13, OUT, None),
                                                         path("M84,186 C100,150 156,150 172,186", "none", OUT, 10), path(drop_d(172, 136, 14), SKY, None)])
P("angry_face_emoji", "mental_health psychology", lambda: [circle(128, 128, 104, ORANGE, sw=9), line(70, 82, 110, 100, OUT, 10), line(186, 82, 146, 100, OUT, 10),
                                                           circle(94, 116, 12, OUT, None), circle(162, 116, 12, OUT, None), path("M84,184 C100,160 156,160 172,184", "none", OUT, 10)])
P("shocked_face_emoji", "mental_health psychology comedy", lambda: [circle(128, 128, 104, YELLOW, sw=9), circle(92, 100, 20, WHITE, OUT, 6), circle(164, 100, 20, WHITE, OUT, 6),
                                                                    circle(92, 100, 8, OUT, None), circle(164, 100, 8, OUT, None), ellipse(128, 176, 22, 30, OUT, None)])
P("thinking_face_emoji", "thinking psychology", lambda: [circle(128, 128, 104, YELLOW, sw=9), circle(96, 104, 12, OUT, None), circle(164, 96, 12, OUT, None), line(140, 70, 186, 64, OUT, 8),
                                                         line(96, 170, 156, 160, OUT, 9), path("M150,200 C170,180 200,190 190,214 C176,236 140,230 150,200 Z", AMBER, sw=6)])
P("sleepy_face_emoji", "sleep mental_health", lambda: [circle(128, 128, 104, YELLOW, sw=9), path("M76,108 C88,120 104,120 116,108 M140,108 C152,120 168,120 180,108", "none", OUT, 8),
                                                       ellipse(128, 172, 16, 12, OUT, None), text(206, 60, "Z", 40, INDIGO), text(232, 30, "z", 28, INDIGO)])
P("brain_gears", "psychology thinking process", lambda: [path("M60,150 C30,140 26,96 56,84 C54,52 90,34 118,48 C130,30 172,32 180,58 C214,58 232,94 214,118 C232,146 210,180 182,174 "
                                                              "C170,200 130,206 116,184 C92,196 62,180 60,150 Z", PINK, sw=8),
                                                         poly([(110 + (36 if i % 4 < 2 else 26) * math.cos(math.radians(i * 15)), 116 + (36 if i % 4 < 2 else 26) * math.sin(math.radians(i * 15))) for i in range(24)], AMBER, sw=5),
                                                         circle(110, 116, 10, WHITE, None), poly([(166 + (24 if i % 4 < 2 else 17) * math.cos(math.radians(i * 22.5)), 132 + (24 if i % 4 < 2 else 17) * math.sin(math.radians(i * 22.5)))
                                                                                                   for i in range(16)], TEAL, sw=4)])
P("phone_addiction", "addiction mental_health tech", lambda: [rect(70, 10, 116, 200, INK, 22), rect(80, 30, 96, 160, SKY, 6, None), path(heart_d(128, 92, 22), RED, None),
                                                              text(128, 160, "99+", 26, WHITE), path("M40,230 C70,200 90,240 128,214 C166,240 186,200 216,230", "none", OUT, 10)])
P("battery_low", "mental_health productivity", lambda: [rect(22, 70, 196, 116, WHITE, 16, sw=9), rect(218, 106, 20, 44, OUT, 6, None), rect(38, 86, 30, 84, RED, 6, None)])
P("goal_checklist_star", "goal productivity motivation", lambda: [rect(30, 30, 160, 196, WHITE, 12), *[g([rect(48, 58 + i * 50, 26, 26, WHITE, 4, OUT, 5), line(86, 72 + i * 50, 170, 72 + i * 50, GRAY, 7),
                                                                                                         pline([(52, 70 + i * 50), (60, 78 + i * 50), (74, 60 + i * 50)], GREEN, 6)]) for i in range(3)],
                                                                  poly(star_pts(196, 196, 46, 20), GOLD, sw=7)])
P("habit_calendar", "productivity self_improvement", lambda: [rect(20, 34, 216, 196, WHITE, 16), rect(20, 34, 216, 40, GREEN, 16), *[g([rect(34 + c * 40, 88 + r * 34, 30, 26, PAPER, 4, OUT, 3),
                                                                                                                                       pline([(40 + c * 40, 100 + r * 34), (48 + c * 40, 108 + r * 34), (60 + c * 40, 92 + r * 34)], GREEN, 5)
                                                                                                                                       if (r * 5 + c) < 12 else ""]) for r in range(4) for c in range(5)]])
P("comfort_zone", "self_improvement motivation psychology", lambda: [circle(110, 140, 70, SKY, sw=7), text(110, 148, "COMFORT", 20, OUT), poly(arrow_pts(150, 110, 236, 40, 16, 32), ORANGE, sw=5),
                                                                     poly(star_pts(226, 34, 22, 9), GOLD, sw=5)])
P("two_paths", "self_improvement decision strategy", lambda: [path("M128,240 L128,150 L40,40", "none", OUT, 26), path("M128,150 L216,40", "none", OUT, 26),
                                                              path("M128,240 L128,150 L40,40", "none", TAN, 14), path("M128,150 L216,40", "none", TAN, 14), poly(star_pts(216, 34, 22, 9), GOLD, sw=5),
                                                              text(40, 30, "?", 30, RED)])
P("growth_mindset", "self_improvement psychology growth", lambda: [path("M60,150 C30,140 26,96 56,84 C54,52 90,34 118,48 C130,30 172,32 180,58 C214,58 232,94 214,118 C232,146 210,180 182,174 "
                                                                       "C170,200 130,206 116,184 C92,196 62,180 60,150 Z", PINK, sw=8), line(128, 160, 128, 90, GREEN_D, 8),
                                                                   path("M128,110 C100,110 86,90 88,70 C112,70 128,88 128,110 Z", GREEN, sw=5), path("M128,98 C152,98 168,78 166,58 C142,58 128,76 128,98 Z", GREEN, sw=5)])

# =========================================================================== agriculture & real estate
P("tractor_farm", "agriculture industry", lambda: [rect(70, 80, 80, 80, GREEN, 8), rect(80, 94, 56, 40, GLASS, 4, OUT, 5), rect(140, 120, 90, 50, GREEN, 8), rect(196, 90, 14, 32, GRAY_D, 2),
                                                   circle(90, 180, 46, INK), circle(90, 180, 18, AMBER, None), circle(206, 196, 30, INK), circle(206, 196, 12, AMBER, None)])
P("wheat_crop", "agriculture food", lambda: [*[g([line(x, 236, x + 10, 90, BROWN_L, 6), *[ellipse(x + 10 + (k % 2) * 14 - 7, 100 + k * 16, 9, 16, GOLD, OUT, 4, transform=f"rotate({20 if k % 2 else -20} {x + 10 + (k % 2) * 14 - 7} {100 + k * 16})")
                                                                                        for k in range(6)]]) for x in (60, 118, 176)]])
P("barn_farm", "agriculture", lambda: [poly([(20, 110), (128, 30), (236, 110)], RED_D, sw=8), rect(36, 104, 184, 132, RED, 4), rect(96, 150, 64, 86, WHITE, 4),
                                       line(96, 150, 160, 236, OUT, 5), line(160, 150, 96, 236, OUT, 5), rect(110, 70, 36, 30, WHITE, 3)])
P("watering_can", "garden agriculture", lambda: [rect(40, 100, 130, 110, TEAL, 16), path("M170,130 L230,80 L240,92 L176,150 Z", TEAL, sw=7), path("M60,100 C60,50 150,50 150,100", "none", OUT, 12),
                                                 *[line(236 + d, 98, 244 + d * 2, 130, SKY, 4) for d in (-4, 4)]])
P("key_house", "real_estate home finance", lambda: [poly([(30, 110), (110, 40), (190, 110)], BLUE, sw=7), rect(46, 104, 128, 100, WHITE, 4), rect(96, 150, 30, 54, BROWN_L, 3),
                                                    g([circle(200, 160, 28, GOLD), rect(212, 154, 44, 14, GOLD, 4)], "rotate(30 200 160)")])
P("apartment_building", "real_estate city home", lambda: [rect(56, 20, 144, 220, CREAM, 6), *[rect(72 + c * 40, 36 + r * 38, 26, 26, SKY, 3, OUT, 4) for r in range(5) for c in range(3)],
                                                          rect(108, 206, 40, 34, BROWN_L, 3)])
P("for_rent_sign", "real_estate", lambda: [line(70, 236, 70, 40, BROWN, 10), line(70, 60, 220, 60, BROWN, 8), rect(100, 66, 120, 80, WHITE, 6), text(160, 100, "FOR", 22, RED), text(160, 130, "RENT", 26, RED)])
