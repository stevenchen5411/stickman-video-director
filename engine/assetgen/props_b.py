"""Props, part B: health & medical, science & space, nature & weather, animals, food & drink."""
from __future__ import annotations

import math

from .kit import *  # noqa: F401,F403
from .registry import P

# =========================================================================== health & medical
P("syringe", "health medical medicine", lambda: [g([rect(98, 40, 60, 140, GLASS, 8), rect(98, 104, 60, 76, RED, 0, None, op=0.8), rect(84, 30, 88, 16, GRAY, 6),
                                                    rect(118, 4, 20, 30, GRAY_D, 4), rect(96, 0, 64, 12, GRAY_D, 6), rect(120, 180, 16, 16, GRAY, 3),
                                                    line(128, 196, 128, 252, OUT, 6), *[line(98, 60 + i * 24, 116, 60 + i * 24, OUT, 4) for i in range(5)]],
                                                   "rotate(40 128 128) translate(0 0) scale(0.92) translate(10 10)")])
P("pill_capsule", "health medicine pharmacy", lambda: [g([path("M70,128 L70,92 C70,58 96,38 128,38 C160,38 186,58 186,92 L186,128 Z", RED),
                                                         path("M70,128 L186,128 L186,164 C186,198 160,218 128,218 C96,218 70,198 70,164 Z", WHITE),
                                                         hl("M90,96 C90,72 104,60 120,58 L120,120 L90,120 Z")], "rotate(40 128 128)")])
P("pills_tablets", "health medicine pharmacy", lambda: [circle(86, 150, 58, WHITE), line(54, 150, 118, 150, GRAY, 7), circle(178, 96, 46, SKY), line(152, 96, 204, 96, BLUE, 6),
                                                        ellipse(176, 196, 44, 26, AMBER)])
P("medicine_bottle", "health medicine pharmacy", lambda: [rect(66, 22, 124, 40, WHITE, 8), rect(56, 58, 144, 178, ORANGE, 18), rect(74, 100, 108, 90, WHITE, 6),
                                                          rect(118, 116, 20, 58, RED, 2, None), rect(99, 135, 58, 20, RED, 2, None)])
P("first_aid_kit", "health medical safety", lambda: [path("M96,60 L96,40 C96,32 102,26 110,26 L146,26 C154,26 160,32 160,40 L160,60", "none", OUT, 12),
                                                     rect(18, 58, 220, 170, RED, 18), rect(108, 94, 40, 100, WHITE, 4, None), rect(78, 124, 100, 40, WHITE, 4, None)])
P("stethoscope_prop", "health medical", lambda: [path("M70,30 L70,100 C70,150 160,150 160,100 L160,30", "none", OUT, 18), path("M70,30 L70,100 C70,150 160,150 160,100 L160,30", "none", GRAY_D, 8),
                                                 path("M115,140 L115,170 C115,210 200,214 200,170 L200,150", "none", OUT, 14), circle(200, 140, 28, SILVER, sw=8), circle(200, 140, 12, GRAY_D, None),
                                                 circle(70, 26, 10, GRAY_D), circle(160, 26, 10, GRAY_D)])
P("thermometer", "health medical weather", lambda: [rect(104, 18, 48, 170, WHITE, 24), circle(128, 200, 40, RED), rect(116, 80, 24, 120, RED, 10, None),
                                                    *[line(152, 50 + i * 24, 170, 50 + i * 24, OUT, 5) for i in range(5)]])
P("heart_anatomical", "health medical anatomy", lambda: [path("M128,226 C70,190 30,150 36,100 C42,60 84,46 110,70 L128,86 L146,70 C172,46 214,60 220,100 C226,150 186,190 128,226 Z", RED_D, sw=8),
                                                         path("M100,64 L100,30 L120,30 L120,72", BLUE, sw=6), path("M136,72 L136,22 L160,22 L160,62", RED, sw=6),
                                                         path("M90,120 C100,150 130,170 150,190", "none", "#7f1d1d", 6), hl_ellipse(80, 110, 18, 30, 0.25, -20)])
P("ecg_heartbeat", "health medical fitness", lambda: [rect(10, 46, 236, 164, INK, 18), *[line(10, y, 246, y, "#14532d", 2) for y in (90, 128, 166)],
                                                      pline([(20, 130), (70, 130), (88, 98), (104, 172), (126, 70), (146, 160), (160, 130), (236, 130)], "#4ade80", 8)])
P("brain_anatomy", "health psychology anatomy science", lambda: [path("M60,150 C30,140 26,96 56,84 C54,52 90,34 118,48 C130,30 172,32 180,58 C214,58 232,94 214,118 "
                                                                    "C232,146 210,180 182,174 C170,200 130,206 116,184 C92,196 62,180 60,150 Z", PINK, sw=8),
                                                                 path("M128,52 C116,90 140,120 120,180", "none", darken(PINK, 0.7), 6), path("M66,110 C90,100 100,130 120,120", "none", darken(PINK, 0.7), 5),
                                                                 path("M150,80 C170,90 160,120 190,126", "none", darken(PINK, 0.7), 5), path("M146,150 C160,140 176,156 186,150", "none", darken(PINK, 0.7), 5),
                                                                 rect(112, 176, 30, 50, PINK, 10)])
P("lungs", "health anatomy medical", lambda: [path("M118,70 C80,40 30,90 30,160 C30,210 60,220 100,206 C118,200 118,180 118,160 Z", PINK, sw=8),
                                              path("M138,70 C176,40 226,90 226,160 C226,210 196,220 156,206 C138,200 138,180 138,160 Z", PINK, sw=8),
                                              path("M128,20 L128,110 M128,100 L98,130 M128,100 L158,130", "none", OUT, 12), path("M128,20 L128,110 M128,100 L98,130 M128,100 L158,130", "none", SILVER, 5)])
P("stomach_organ", "health anatomy medical food", lambda: [path("M98,24 L98,70 C60,80 40,130 60,176 C80,220 170,236 206,190 C230,160 214,118 180,120 C150,124 150,160 128,150 "
                                                              "C110,140 128,90 126,24 Z", PINK, sw=8)])
P("kidney_organ", "health anatomy medical", lambda: [path("M110,30 C40,30 30,120 50,170 C70,220 140,236 150,190 C156,160 120,150 126,120 C132,90 170,90 160,60 C152,40 132,30 110,30 Z",
                                                          RED_D, sw=8), path("M150,150 L210,170 L230,230", "none", OUT, 8)])
P("tooth", "health dental", lambda: [path("M60,40 C90,26 110,48 128,48 C146,48 166,26 196,40 C226,56 214,110 200,140 C188,166 186,226 168,228 C150,230 150,170 128,170 "
                                          "C106,170 106,230 88,228 C70,226 68,166 56,140 C42,110 30,56 60,40 Z", WHITE, sw=8), hl("M76,60 C90,52 100,60 98,74 C90,70 82,72 76,60 Z", 0.6)])
P("bone", "health anatomy pets", lambda: [g([circle(46, 104, 30, CREAM), circle(46, 152, 30, CREAM), circle(210, 104, 30, CREAM), circle(210, 152, 30, CREAM),
                                             rect(46, 104, 164, 48, CREAM, 0, None), line(60, 104, 196, 104, OUT, 7), line(60, 152, 196, 152, OUT, 7)], "rotate(-30 128 128)")])
P("skeleton_skull", "health anatomy spooky history", lambda: [path("M128,26 C70,26 38,66 40,112 C42,146 62,160 66,176 L66,206 L190,206 L190,176 C194,160 214,146 216,112 "
                                                                 "C218,66 186,26 128,26 Z", WHITE, sw=8), ellipse(94, 120, 26, 30, OUT, None), ellipse(162, 120, 26, 30, OUT, None),
                                                              poly([(128, 148), (116, 172), (140, 172)], OUT, None), *[line(x, 190, x, 222, OUT, 6) for x in (96, 128, 160)]])
P("dna_helix", "science biology health", lambda: [*[line(70 + 50 * math.sin(i * 0.6), 20 + i * 22, 186 - 50 * math.sin(i * 0.6), 20 + i * 22, GRAY, 6) for i in range(10)],
                                                  pline([(128 - 58 * math.sin(i * 0.15) + 0, 14 + i * 5.5) for i in range(42)], OUT, 16),
                                                  pline([(128 - 58 * math.sin(i * 0.15), 14 + i * 5.5) for i in range(42)], BLUE, 8),
                                                  pline([(128 + 58 * math.sin(i * 0.15), 14 + i * 5.5) for i in range(42)], OUT, 16),
                                                  pline([(128 + 58 * math.sin(i * 0.15), 14 + i * 5.5) for i in range(42)], PINK, 8)])
P("virus_germ", "health disease medical science", lambda: [*[g([line(128, 128, 128 + 104 * math.cos(math.radians(a)), 128 + 104 * math.sin(math.radians(a)), OUT, 8),
                                                              circle(128 + 104 * math.cos(math.radians(a)), 128 + 104 * math.sin(math.radians(a)), 13, RED)])
                                                           for a in range(0, 360, 36)], circle(128, 128, 76, LIME), *[circle(128 + d * math.cos(a), 128 + d * math.sin(a), 11, GREEN, None)
                                                                                                                    for d, a in ((30, 0.5), (40, 2.4), (24, 4.0), (46, 5.2))]])
P("bacteria_cell", "health disease science biology", lambda: [g([rect(36, 92, 184, 76, TEAL, 38), *[circle(x, y, 10, darken(TEAL, 0.7), None) for x, y in ((80, 116), (130, 140), (176, 118))],
                                                                *[path(f"M{x},{y} C{x - 6},{y + 20} {x + 10},{y + 30} {x},{y + 48}", "none", OUT, 5) for x, y in ((70, 166), (110, 168), (150, 168), (190, 166))]],
                                                               "rotate(-20 128 128)")])
P("human_cell", "biology science health", lambda: [path("M128,22 C200,20 238,80 230,140 C222,200 170,236 112,230 C50,224 18,170 26,116 C34,62 72,24 128,22 Z", "#a5f3fc", sw=8),
                                                   circle(124, 124, 42, VIOLET), circle(132, 116, 14, PURPLE, None), ellipse(186, 80, 22, 12, ORANGE, OUT, 5),
                                                   ellipse(70, 178, 24, 12, GREEN, OUT, 5), ellipse(180, 178, 16, 10, PINK, OUT, 5)])
P("blood_drop", "health medical", lambda: [path(drop_d(128, 140, 108), RED, sw=9), hl_ellipse(100, 150, 16, 28, 0.35, 20)])
P("bandage", "health medical", lambda: [g([rect(18, 92, 220, 72, TAN, 30), rect(92, 92, 72, 72, CREAM, 6, OUT, 5), *[circle(110 + c * 18, 110 + r * 18, 4, darken(TAN, 0.8), None)
                                                                                                                  for r in range(3) for c in range(3)]], "rotate(-35 128 128)")])
P("face_mask", "health medical", lambda: [path("M50,90 C90,70 166,70 206,90 L206,160 C166,196 90,196 50,160 Z", SKY, sw=8), *[line(64, 110 + i * 22, 192, 110 + i * 22, BLUE, 4) for i in range(3)],
                                          path("M50,96 C20,100 18,150 50,154", "none", OUT, 6), path("M206,96 C236,100 238,150 206,154", "none", OUT, 6)])
P("microscope", "science biology health research", lambda: [rect(40, 214, 176, 24, GRAY_D, 8), path("M150,214 C210,200 200,120 150,110", "none", OUT, 14),
                                                            g([rect(96, 30, 44, 120, SILVER, 10), rect(104, 14, 28, 24, GRAY_D, 4), rect(104, 150, 28, 30, GRAY_D, 4)], "rotate(-25 118 100)"),
                                                            rect(66, 176, 110, 16, GRAY, 4), rect(150, 98, 40, 40, GRAY_D, 10)])
P("test_tube", "science chemistry medical", lambda: [g([rect(98, 14, 60, 200, GLASS, 30), path("M98,120 L158,120 L158,184 C158,200 146,214 128,214 C110,214 98,200 98,184 Z", GREEN, None),
                                                         rect(90, 10, 76, 22, SILVER, 6), *[circle(120 + i * 8, 150 + (i % 2) * 20, 5, WHITE, None, op=0.7) for i in range(3)]], "rotate(20 128 128)")])
P("test_tubes_rack", "science chemistry", lambda: [*[g([rect(x, 30, 40, 160, GLASS, 20), path(f"M{x},{110} L{x + 40},{110} L{x + 40},{170} C{x + 40},{184} {x + 30},{190} {x + 20},{190} "
                                                                                                  f"C{x + 10},{190} {x},{184} {x},{170} Z", c, None)])
                                                     for x, c in ((40, RED), (108, BLUE), (176, YELLOW))], rect(20, 150, 216, 26, BROWN_L, 6), rect(30, 176, 16, 50, BROWN, 4),
                                                   rect(210, 176, 16, 50, BROWN, 4)])
P("flask_erlenmeyer", "science chemistry", lambda: [path("M100,20 L156,20 L156,90 L222,212 C230,228 220,238 204,238 L52,238 C36,238 26,228 34,212 L100,90 Z", GLASS, sw=8),
                                                    path("M72,160 L184,160 L222,212 C230,228 220,238 204,238 L52,238 C36,238 26,228 34,212 Z", VIOLET, None),
                                                    *[circle(x, y, r, WHITE, None, op=0.7) for x, y, r in ((110, 196, 9), (140, 176, 7), (160, 210, 6), (128, 130, 6))]])
P("beaker", "science chemistry", lambda: [path("M40,30 L216,30 L200,48 L200,226 L56,226 L56,48 Z", GLASS, sw=8), rect(56, 120, 144, 106, ORANGE, 0, None),
                                          *[line(56, y, 86, y, OUT, 5) for y in (70, 110, 150, 190)], path("M56,120 L200,120", "none", OUT, 5)])
P("atom_symbol", "science physics", lambda: [*[ellipse(128, 128, 108, 40, "none", OUT, 14, transform=f"rotate({a} 128 128)") for a in (0, 60, 120)],
                                             *[ellipse(128, 128, 108, 40, "none", CYAN, 6, transform=f"rotate({a} 128 128)") for a in (0, 60, 120)],
                                             circle(128, 128, 22, RED)])
P("magnet_u", "science physics", lambda: [path("M40,40 L96,40 L96,140 C96,160 112,172 128,172 C144,172 160,160 160,140 L160,40 L216,40 L216,140 C216,196 176,232 128,232 "
                                               "C80,232 40,196 40,140 Z", RED, sw=8), rect(40, 40, 56, 40, SILVER, 0), rect(160, 40, 56, 40, SILVER, 0),
                                          *[path(arc_d(128, 40, r, 200, 340), "none", SKY, 5, op=0.8) for r in (100, 120)]])
P("telescope", "space astronomy science", lambda: [g([rect(40, 90, 160, 50, BLUE, 12), rect(196, 82, 34, 66, BLUE_D, 8), rect(20, 98, 26, 34, GRAY_D, 6)], "rotate(-28 128 115)"),
                                                   line(128, 140, 80, 236, OUT, 10), line(128, 140, 176, 236, OUT, 10), line(128, 140, 128, 236, OUT, 10)])
P("planet_saturn", "space astronomy science", lambda: [circle(128, 128, 70, AMBER), path("M58,128 C58,100 198,100 198,128", "none", darken(AMBER), 6),
                                                       ellipse(128, 132, 120, 30, "none", OUT, 20, transform="rotate(-18 128 132)"),
                                                       ellipse(128, 132, 120, 30, "none", SAND, 10, transform="rotate(-18 128 132)"),
                                                       path("M58,128 A70,70 0 0 0 198,128", AMBER, None, op=0)])
P("planet_earth", "space environment travel", lambda: [circle(128, 128, 104, BLUE), path("M70,60 C100,50 120,80 100,100 C80,120 100,150 70,160 C50,140 44,90 70,60 Z", GREEN, OUT, 5),
                                                       path("M150,40 C190,60 210,110 196,150 C176,140 170,110 150,110 C130,96 140,60 150,40 Z", GREEN, OUT, 5),
                                                       path("M130,170 C150,180 170,200 150,222 C130,210 120,190 130,170 Z", GREEN, OUT, 5), hl_ellipse(90, 70, 30, 16, 0.3, -30)])
P("moon_crescent", "space night sleep", lambda: [path("M170,30 C110,30 60,76 60,136 C60,196 110,236 170,236 C130,210 110,176 110,134 C110,90 132,54 170,30 Z", SAND, sw=8),
                                                 circle(100, 120, 10, AMBER, None), circle(116, 180, 7, AMBER, None)])
P("full_moon", "space night", lambda: [circle(128, 128, 104, SILVER), *[circle(x, y, r, GRAY, None, op=0.7) for x, y, r in ((90, 96, 22), (160, 80, 14), (150, 160, 28), (86, 170, 12))]])
P("sun_shining", "weather nature space", lambda: [*[line(128 + 78 * math.cos(math.radians(a)), 128 + 78 * math.sin(math.radians(a)), 128 + 116 * math.cos(math.radians(a)),
                                                         128 + 116 * math.sin(math.radians(a)), ORANGE, 14) for a in range(0, 360, 30)],
                                                  circle(128, 128, 64, YELLOW, sw=8), hl_ellipse(106, 104, 20, 12, 0.5, -30)])
P("comet", "space astronomy", lambda: [path("M200,56 C150,100 80,160 20,236 C70,170 120,110 176,40 Z", SKY, None, op=0.6),
                                       path("M206,70 C160,120 110,170 60,230 C110,180 150,130 190,52 Z", WHITE, None, op=0.5), circle(196, 60, 34, CYAN)])
P("astronaut_helmet", "space adventure", lambda: [circle(128, 120, 100, WHITE, sw=9), rect(56, 76, 144, 96, "#0b1d33", 40), hl("M70,90 C80,82 110,80 120,84 L110,100 C96,96 80,98 72,104 Z", 0.6),
                                                  rect(78, 206, 100, 30, SILVER, 8), circle(206, 104, 16, RED)])
P("ufo_saucer", "space mystery comedy", lambda: [path("M80,110 C80,60 176,60 176,110 Z", GLASS, sw=8), ellipse(128, 124, 112, 34, SILVER), ellipse(128, 118, 70, 14, GRAY, None),
                                                 *[circle(x, 132, 8, YELLOW, None) for x in (52, 90, 128, 166, 204)], poly([(96, 152), (160, 152), (200, 240), (56, 240)], YELLOW, None, op=0.35)])
P("black_hole", "space astronomy physics", lambda: [ellipse(128, 128, 120, 46, ORANGE, None, op=0.85), ellipse(128, 128, 92, 30, YELLOW, None, op=0.85), circle(128, 128, 52, "#000000", ORANGE, 6),
                                                    path("M76,128 C76,92 180,92 180,128", "none", AMBER, 8, op=0.8)])
P("space_station", "space tech", lambda: [rect(20, 110, 70, 36, BLUE, 4), rect(166, 110, 70, 36, BLUE, 4), rect(88, 98, 80, 60, SILVER, 14), rect(116, 40, 24, 176, GRAY, 6),
                                          rect(100, 30, 56, 20, GRAY_D, 6), rect(100, 206, 56, 20, GRAY_D, 6), circle(128, 128, 14, SKY)])
P("rocket_launch", "space adventure tech", lambda: [path("M128,14 C160,40 172,96 166,150 L90,150 C84,96 96,40 128,14 Z", WHITE, sw=8), circle(128, 84, 18, SKY, sw=6),
                                                    poly([(90, 112), (60, 166), (92, 156)], RED, sw=6), poly([(166, 112), (196, 166), (164, 156)], RED, sw=6),
                                                    path("M100,150 L156,150 L146,186 L128,214 L110,186 Z", ORANGE, sw=6), path(cloud_d(80, 222, 34), SILVER, None), path(cloud_d(176, 226, 30), SILVER, None)])
P("crystal_geode", "science geology nature", lambda: [poly([(60, 230), (40, 120), (80, 60), (110, 230)], VIOLET, sw=7), poly([(100, 230), (110, 80), (140, 24), (170, 230)], PURPLE, sw=7),
                                                      poly([(160, 230), (180, 110), (214, 140), (220, 230)], INDIGO, sw=7), hl("M118,90 L136,44 L132,150 Z", 0.4)])
P("volcano_erupt", "nature geology science", lambda: [poly([(10, 240), (96, 90), (160, 90), (246, 240)], BROWN, sw=8), path("M96,90 C110,110 146,110 160,90 L150,130 L106,130 Z", ORANGE, None),
                                                      path("M110,92 C90,40 120,20 128,40 C136,10 170,30 150,92 Z", RED, OUT, 6), *[circle(x, y, r, ORANGE, None) for x, y, r in ((80, 40, 9), (186, 50, 7), (60, 80, 6))]])
P("fossil_ammonite", "science history archaeology", lambda: [circle(128, 128, 100, TAN), pline([(128 + (8 + i * 1.9) * math.cos(i * 0.32), 128 + (8 + i * 1.9) * math.sin(i * 0.32)) for i in range(48)], BROWN, 8)])
P("dinosaur_trex", "history science kids", lambda: [path("M40,120 C40,80 80,58 120,64 L170,54 C200,50 232,60 232,86 C232,104 210,108 196,106 L180,108 C176,130 170,150 160,164 L172,236 "
                                                        "L146,236 L140,184 L110,184 L106,236 L80,236 L84,170 C60,160 40,146 20,180 C14,150 30,132 40,120 Z", GREEN, sw=8),
                                                     circle(200, 76, 8, OUT, None), path("M150,130 L168,150", "none", OUT, 7), pline([(196, 98), (222, 96)], OUT, 4)])
P("solar_system", "space astronomy science education", lambda: [circle(128, 128, 30, YELLOW), *[circle(128, 128, r, "none", GRAY, 3) for r in (56, 84, 112)],
                                                                circle(184, 128, 12, SKY), circle(80, 66, 16, RED), circle(46, 192, 18, AMBER)])
P("periodic_element", "science chemistry education", lambda: [rect(28, 28, 200, 200, TEAL, 14), text(52, 66, "6", 30, WHITE, anchor="start"), text(128, 164, "C", 110, WHITE),
                                                              text(128, 210, "Carbon", 26, WHITE)])
P("formula_board", "science physics education", lambda: [rect(14, 40, 228, 160, GREEN_D, 10), rect(14, 40, 228, 160, "none", 10, BROWN_L, 12), text(128, 120, "E=mc²", 52, WHITE, family="DejaVu Serif"),
                                                         line(40, 160, 120, 160, WHITE, 3, op=0.6), line(140, 168, 214, 168, WHITE, 3, op=0.6)])
P("lab_goggles", "science chemistry safety", lambda: [path("M20,100 C20,80 40,70 60,70 L196,70 C216,70 236,80 236,100 L236,150 C236,170 216,180 196,180 L150,180 L136,160 L120,160 "
                                                         "L106,180 L60,180 C40,180 20,170 20,150 Z", GLASS, sw=8), line(20, 120, 2, 112, OUT, 8), line(236, 120, 254, 112, OUT, 8),
                                                      hl("M40,90 L100,90 L90,110 L40,110 Z", 0.5)])
P("battery_aa", "science energy tech", lambda: [rect(56, 46, 144, 180, GREEN, 18), rect(56, 46, 144, 60, OUT, 18, None), rect(104, 26, 48, 24, SILVER, 6),
                                                text(128, 166, "+", 70, WHITE)])
P("radioactive_sign", "science energy safety", lambda: [circle(128, 128, 108, YELLOW, sw=9), *[path(pie_d(128, 128, 88, a - 30, a + 30), OUT, None) for a in (-90, 30, 150)],
                                                        circle(128, 128, 26, YELLOW, None), circle(128, 128, 16, OUT, None)])
P("pendulum_physics", "science physics", lambda: [rect(30, 20, 196, 18, BROWN, 6), line(128, 38, 180, 196, OUT, 6), circle(184, 204, 30, RED), path(arc_d(128, 38, 150, 60, 120), "none", GRAY, 4, stroke_dasharray="8 8")])

# =========================================================================== nature & weather
P("tree_oak", "nature environment", lambda: [rect(110, 140, 36, 96, BROWN, 6), path(cloud_d(128, 96, 90), GREEN, sw=8), circle(96, 90, 8, RED, None), circle(160, 110, 8, RED, None)])
P("tree_pine", "nature environment holiday", lambda: [rect(114, 196, 28, 44, BROWN, 4), poly([(128, 14), (196, 110), (164, 110), (220, 200), (36, 200), (92, 110), (60, 110)], GREEN_D, sw=8)])
P("palm_tree", "nature travel ocean", lambda: [path("M120,240 C126,180 120,120 136,76 L150,80 C140,120 146,180 142,240 Z", BROWN_L, sw=7),
                                               *[path(d, GREEN, sw=6) for d in ("M142,76 C110,40 60,46 30,80 C70,64 110,70 142,76 Z", "M142,76 C170,30 220,40 240,70 C200,60 170,64 142,76 Z",
                                                                                 "M142,76 C100,90 70,130 66,170 C90,130 116,100 142,76 Z", "M142,76 C184,90 214,130 214,170 C196,130 170,100 142,76 Z")],
                                               circle(134, 90, 12, BROWN), circle(152, 92, 12, BROWN)])
P("cactus_plant", "nature desert garden", lambda: [path("M108,236 L108,50 C108,30 148,30 148,50 L148,236 Z", GREEN, sw=8), path("M108,150 L76,150 C66,150 60,142 60,132 L60,90 C60,76 84,76 84,90 L84,126 L108,126",
                                                                                                                              GREEN, sw=7),
                                                   path("M148,120 L180,120 C190,120 196,112 196,102 L196,70 C196,56 172,56 172,70 L172,96 L148,96", GREEN, sw=7), rect(80, 214, 96, 30, ORANGE, 6)])
P("flower_bloom", "nature garden love", lambda: [line(128, 128, 128, 240, GREEN_D, 10), path("M128,196 C100,170 80,180 80,196 C100,206 116,204 128,196 Z", GREEN, sw=5),
                                                 *[circle(128 + 44 * math.cos(math.radians(a)), 100 + 44 * math.sin(math.radians(a)), 32, PINK) for a in range(0, 360, 72)],
                                                 circle(128, 100, 26, YELLOW)])
P("sunflower", "nature garden agriculture", lambda: [line(128, 140, 128, 240, GREEN_D, 10), *[ellipse(128 + 58 * math.cos(math.radians(a)), 100 + 58 * math.sin(math.radians(a)), 26, 12, YELLOW, OUT, 5,
                                                                                                    transform=f"rotate({a} {128 + 58 * math.cos(math.radians(a))} {100 + 58 * math.sin(math.radians(a))})")
                                                                                            for a in range(0, 360, 30)], circle(128, 100, 40, BROWN)])
P("leaf_green", "nature environment", lambda: [path("M40,216 C30,120 90,40 216,36 C220,150 150,220 40,216 Z", GREEN, sw=8), path("M40,216 C90,160 140,110 200,54", "none", GREEN_D, 7)])
P("seedling_sprout", "nature growth agriculture self_improvement", lambda: [ellipse(128, 216, 80, 22, BROWN, sw=7), line(128, 210, 128, 120, GREEN_D, 10),
                                                                            path("M128,140 C90,140 64,110 66,76 C104,76 128,104 128,140 Z", LIME, sw=7),
                                                                            path("M128,124 C164,124 194,96 192,56 C150,56 128,90 128,124 Z", GREEN, sw=7)])
P("mushroom", "nature food", lambda: [rect(104, 128, 48, 100, CREAM, 18), path("M24,136 C24,60 70,24 128,24 C186,24 232,60 232,136 Z", RED, sw=8),
                                      *[circle(x, y, r, WHITE, None) for x, y, r in ((80, 76, 16), (140, 52, 13), (180, 100, 15), (110, 110, 10))]])
P("water_drop", "nature environment health", lambda: [path(drop_d(128, 140, 108), SKY, sw=9), hl_ellipse(100, 150, 16, 28, 0.5, 20)])
P("flame_campfire", "nature adventure", lambda: [g([rect(40, 196, 176, 26, BROWN, 12)], "rotate(10 128 209)"), g([rect(40, 196, 176, 26, BROWN_L, 12)], "rotate(-10 128 209)"),
                                                 path("M128,40 C160,80 196,110 186,160 C178,196 150,204 128,204 C100,204 74,190 70,160 C66,124 90,110 104,84 C108,110 118,118 124,120 "
                                                      "C118,90 120,64 128,40 Z", ORANGE, sw=7), path("M128,110 C148,136 160,150 156,174 C152,192 140,198 128,198 C114,198 100,188 100,172 "
                                                                                                   "C100,152 118,140 128,110 Z", YELLOW, None)])
P("snowflake", "weather holiday nature", lambda: [*[g([line(128, 128, 128, 24, OUT, 16), line(128, 60, 104, 40, OUT, 12), line(128, 60, 152, 40, OUT, 12),
                                                       line(128, 128, 128, 24, SKY, 8), line(128, 60, 104, 40, SKY, 6), line(128, 60, 152, 40, SKY, 6)], f"rotate({a} 128 128)")
                                                    for a in range(0, 360, 60)]])
P("rain_cloud", "weather nature", lambda: [path(cloud_d(128, 96, 92), SILVER, sw=8), *[line(x, 168, x - 14, 214, BLUE, 9) for x in (78, 128, 178)],
                                           *[line(x, 196, x - 10, 230, SKY, 7) for x in (104, 154)]])
P("storm_cloud", "weather nature", lambda: [path(cloud_d(128, 92, 92), GRAY_D, sw=8), poly(bolt_pts(128, 180, 60), YELLOW, sw=6)])
P("rainbow", "weather nature celebration", lambda: [*[path(arc_d(128, 200, r, 180, 360), "none", c, 18) for r, c in ((112, RED), (94, ORANGE), (76, YELLOW), (58, GREEN), (40, BLUE))],
                                                    path(cloud_d(36, 200, 26), WHITE, None), path(cloud_d(222, 200, 26), WHITE, None)])
P("tornado", "weather nature disaster", lambda: [path("M24,40 C80,20 180,20 232,40 C200,70 170,78 150,96 C176,110 160,130 140,140 C150,160 136,180 120,190 C130,206 118,222 110,236 "
                                                      "C100,220 104,200 96,188 C80,170 96,156 100,140 C70,126 70,110 96,96 C60,80 40,64 24,40 Z", GRAY, sw=8),
                                                 *[path(f"M{60 + i * 14},{50 + i * 34} C{110},{40 + i * 34} {150},{44 + i * 34} {200 - i * 26},{50 + i * 34}", "none", GRAY_D, 5) for i in range(4)]])
P("wave_ocean", "nature ocean travel", lambda: [path("M16,180 C40,100 100,60 160,70 C210,78 236,120 220,150 C200,120 160,120 150,150 C140,180 180,190 200,180 C170,220 60,230 16,180 Z", BLUE, sw=8),
                                                path("M40,176 C60,130 100,104 150,104", "none", WHITE, 7, op=0.8), path("M16,214 C80,200 160,236 240,212 L240,240 L16,240 Z", SKY, sw=6)])
P("mountain_peaks", "nature travel adventure", lambda: [poly([(10, 230), (90, 70), (150, 170), (180, 120), (246, 230)], GRAY, sw=8), poly([(90, 70), (116, 120), (96, 110), (78, 124), (68, 114)], WHITE, None),
                                                        poly([(180, 120), (196, 150), (178, 146), (166, 150)], WHITE, None)])
def _recycle():
    out = []
    for k in range(3):
        a0, a1 = k * 120 - 80, k * 120 + 10
        ex, ey = 128 + 82 * math.cos(math.radians(a1)), 136 + 82 * math.sin(math.radians(a1))
        tx, ty = -math.sin(math.radians(a1)), math.cos(math.radians(a1))
        nx, ny = math.cos(math.radians(a1)), math.sin(math.radians(a1))
        out += [path(arc_d(128, 136, 82, a0, a1), "none", OUT, 36), path(arc_d(128, 136, 82, a0, a1), "none", GREEN, 22),
                poly([(ex + tx * 34, ey + ty * 34), (ex + nx * 30, ey + ny * 30), (ex - nx * 30, ey - ny * 30)], GREEN, sw=7)]
    return out


P("recycle_symbol", "environment nature", _recycle)
P("earth_leaf", "environment nature energy", lambda: [circle(116, 140, 92, BLUE), path("M60,110 C80,96 100,120 90,140 C80,160 60,150 60,110 Z", GREEN, OUT, 5),
                                                      path("M130,70 C170,80 180,120 160,140 C140,120 120,110 130,70 Z", GREEN, OUT, 5), path("M150,96 C160,30 220,20 244,30 C240,80 200,110 150,96 Z", LIME, sw=7)])
P("paw_print", "animals pets", lambda: [ellipse(128, 168, 56, 48, BROWN_L), *[ellipse(x, y, 22, 28, BROWN_L, transform=f"rotate({r} {x} {y})") for x, y, r in ((62, 96, -20), (104, 62, -6), (152, 62, 6), (194, 96, 20))]])
P("feather_quill", "history education writing", lambda: [path("M200,20 C120,40 70,110 56,200 L70,206 C110,120 160,70 200,20 Z", WHITE, sw=7), line(56, 200, 36, 240, OUT, 7),
                                                         *[line(150 - i * 18, 50 + i * 26, 110 - i * 14, 62 + i * 26, GRAY, 4) for i in range(4)]])

# =========================================================================== animals
P("cat_face", "animals pets", lambda: [poly([(40, 40), (90, 76), (52, 120)], AMBER, sw=7), poly([(216, 40), (166, 76), (204, 120)], AMBER, sw=7), ellipse(128, 140, 100, 86, AMBER, sw=8),
                                       ellipse(92, 128, 13, 18, OUT, None), ellipse(164, 128, 13, 18, OUT, None), poly([(118, 158), (138, 158), (128, 170)], PINK, sw=4),
                                       *[line(x0, 168 + d, x1, 160 + d * 2, OUT, 4) for x0, x1, d in ((96, 40, 0), (96, 40, 14), (160, 216, 0), (160, 216, 14))]])
P("dog_face", "animals pets", lambda: [ellipse(128, 136, 92, 84, TAN, sw=8), path("M50,80 C20,90 20,170 46,176 C70,170 70,110 60,90 Z", BROWN_L, sw=7),
                                       path("M206,80 C236,90 236,170 210,176 C186,170 186,110 196,90 Z", BROWN_L, sw=7), circle(98, 120, 11, OUT, None), circle(158, 120, 11, OUT, None),
                                       ellipse(128, 164, 22, 16, OUT, None), path("M128,180 C120,196 108,196 104,188 M128,180 C136,196 148,196 152,188", "none", OUT, 5)])
P("bird_flying", "animals nature", lambda: [path("M30,140 C70,80 110,90 128,130 C146,90 186,80 226,140 C190,116 150,120 128,150 C106,120 66,116 30,140 Z", SKY, sw=7), circle(128, 140, 16, BLUE),
                                            poly([(128, 160), (120, 176), (136, 176)], AMBER, None)])
P("fish_swim", "animals ocean food", lambda: [path("M40,128 C80,60 170,60 200,128 C170,196 80,196 40,128 Z", ORANGE, sw=8), poly([(196, 128), (240, 84), (240, 172)], ORANGE, sw=7),
                                              circle(80, 116, 10, OUT, None), path("M120,90 C134,110 134,146 120,166", "none", darken(ORANGE), 5)])
P("butterfly", "animals nature", lambda: [path("M128,120 C90,40 20,40 30,100 C36,140 80,150 128,130 Z", VIOLET, sw=7), path("M128,120 C166,40 236,40 226,100 C220,140 176,150 128,130 Z", VIOLET, sw=7),
                                          path("M128,136 C90,150 50,180 70,214 C90,230 120,190 128,150 Z", PINK, sw=7), path("M128,136 C166,150 206,180 186,214 C166,230 136,190 128,150 Z", PINK, sw=7),
                                          rect(120, 90, 16, 110, OUT, 8, None), path("M124,92 C116,64 104,56 96,52 M132,92 C140,64 152,56 160,52", "none", OUT, 4)])
P("honey_bee", "animals nature agriculture", lambda: [ellipse(90, 82, 40, 26, WHITE, op=0.9, transform="rotate(-30 90 82)"), ellipse(160, 76, 40, 26, WHITE, op=0.9, transform="rotate(30 160 76)"),
                                                      ellipse(128, 146, 76, 56, YELLOW, sw=8), *[rect(x, 96, 20, 100, OUT, 4, None) for x in (100, 140)],
                                                      circle(60, 140, 30, OUT, None), circle(52, 132, 6, WHITE, None), poly([(204, 146), (232, 140), (204, 158)], OUT, None)])
P("owl_wise", "animals education", lambda: [ellipse(128, 140, 90, 100, BROWN_L, sw=8), poly([(52, 70), (64, 24), (96, 56)], BROWN_L, sw=7), poly([(204, 70), (192, 24), (160, 56)], BROWN_L, sw=7),
                                            circle(96, 110, 32, WHITE), circle(160, 110, 32, WHITE), circle(96, 112, 14, OUT, None), circle(160, 112, 14, OUT, None),
                                            poly([(118, 140), (138, 140), (128, 162)], AMBER, sw=5), path("M76,190 C100,170 156,170 180,190", "none", darken(BROWN_L), 6)])
P("rabbit_bunny", "animals pets kids", lambda: [ellipse(96, 60, 20, 52, WHITE), ellipse(160, 60, 20, 52, WHITE), ellipse(96, 60, 9, 36, PINK, None), ellipse(160, 60, 9, 36, PINK, None),
                                                circle(128, 150, 74, WHITE, sw=8), circle(102, 140, 9, OUT, None), circle(154, 140, 9, OUT, None), ellipse(128, 166, 10, 7, PINK, None)])
P("turtle_slow", "animals nature", lambda: [ellipse(54, 170, 32, 24, GREEN, sw=7), ellipse(134, 150, 92, 66, GREEN_D, sw=8), path("M42,150 C42,90 226,90 226,150 Z", LIME, sw=8),
                                            poly(reg_pts(134, 118, 22, 6, 0), GREEN, OUT, 4), *[ellipse(x, 196, 18, 14, GREEN, sw=6) for x in (84, 184)], circle(46, 164, 5, OUT, None)])
P("snail_slow", "animals nature productivity", lambda: [path("M20,210 L210,210 C230,210 236,196 220,190 L80,190 C60,190 40,170 40,150 L40,110 C40,96 60,96 60,110 L60,150 Z", "#a3e635", sw=7),
                                                        circle(140, 140, 62, AMBER), pline([(140 + (6 + i * 1.2) * math.cos(i * 0.35), 140 + (6 + i * 1.2) * math.sin(i * 0.35)) for i in range(40)], BROWN, 6)])
P("lion_face", "animals leader", lambda: [*[circle(128 + 92 * math.cos(math.radians(a)), 128 + 92 * math.sin(math.radians(a)), 34, AMBER) for a in range(0, 360, 30)],
                                          circle(128, 128, 90, ORANGE, None), circle(128, 132, 74, YELLOW), circle(102, 118, 9, OUT, None), circle(154, 118, 9, OUT, None),
                                          poly([(116, 146), (140, 146), (128, 160)], BROWN, sw=4), path("M128,160 C120,176 106,176 100,170 M128,160 C136,176 150,176 156,170", "none", OUT, 5)])
P("elephant", "animals nature", lambda: [ellipse(140, 140, 90, 66, GRAY), circle(74, 110, 48, GRAY), path("M40,120 C30,160 30,200 50,220 C60,200 56,170 64,140 Z", GRAY, sw=7),
                                         ellipse(96, 104, 30, 40, SILVER), *[rect(x, 180, 26, 50, GRAY, 6) for x in (100, 146, 186)], circle(70, 100, 7, OUT, None)])
P("shark_fin", "animals ocean danger", lambda: [path("M60,200 C100,190 130,120 150,40 C170,100 186,170 220,200 Z", GRAY_D, sw=8), path("M10,206 C60,190 100,222 140,206 C180,190 220,222 250,206 L250,246 L10,246 Z", BLUE, sw=6)])
P("penguin", "animals nature", lambda: [ellipse(128, 140, 76, 100, INK, sw=0), ellipse(128, 156, 52, 76, WHITE, None), circle(108, 92, 9, WHITE, None), circle(148, 92, 9, WHITE, None),
                                        circle(110, 94, 4, OUT, None), circle(146, 94, 4, OUT, None), poly([(116, 110), (140, 110), (128, 126)], ORANGE, None),
                                        ellipse(98, 236, 22, 10, ORANGE, None), ellipse(158, 236, 22, 10, ORANGE, None)])
P("chicken", "animals agriculture food", lambda: [ellipse(130, 150, 82, 70, WHITE), circle(84, 92, 40, WHITE), path("M66,56 C70,40 84,46 84,56 C90,40 104,46 100,60", RED, sw=5),
                                                  poly([(44, 92), (20, 102), (46, 108)], AMBER, sw=5), circle(76, 86, 6, OUT, None), path("M180,120 C220,96 230,150 200,160", WHITE, sw=7),
                                                  line(110, 216, 110, 240, AMBER, 6), line(150, 216, 150, 240, AMBER, 6)])
P("cow", "animals agriculture", lambda: [ellipse(140, 136, 96, 62, WHITE), path("M90,100 C100,120 130,110 120,90 Z", OUT, None), path("M170,150 C190,170 210,140 196,130 Z", OUT, None),
                                         rect(50, 74, 70, 74, WHITE, 26), ellipse(84, 140, 34, 22, PINK), poly([(50, 80), (34, 60), (64, 74)], CREAM, sw=5),
                                         circle(70, 102, 6, OUT, None), *[rect(x, 184, 20, 50, WHITE, 6) for x in (90, 130, 176, 206)]])
P("horse", "animals agriculture history", lambda: [path("M70,110 L90,40 C110,30 130,40 128,60 L136,100 L210,104 C230,110 236,140 220,160 L216,232 L198,232 L194,170 L120,170 L114,232 "
                                                        "L96,232 L94,160 C70,150 60,130 70,110 Z", BROWN_L, sw=8), path("M88,44 C70,60 60,90 70,110", "none", OUT, 10), circle(100, 62, 6, OUT, None)])
P("whale_big", "animals ocean", lambda: [path("M20,140 C20,90 80,64 140,72 C200,80 226,110 226,140 C226,190 170,210 110,206 C60,204 20,180 20,140 Z", BLUE, sw=8),
                                         path("M214,124 C232,96 246,84 252,70 C238,82 228,100 218,112", BLUE, sw=6), path("M34,168 C80,190 160,196 214,166 L204,186 C150,210 80,204 40,184 Z", SKY, None),
                                         circle(70, 124, 8, OUT, None)])
P("ant_worker", "animals productivity", lambda: [circle(60, 140, 28, BROWN), circle(118, 140, 22, BROWN), ellipse(186, 140, 46, 36, BROWN),
                                                 *[line(118, 150, x, 214, OUT, 5) for x in (90, 120, 150)], path("M46,118 C40,90 30,80 20,76 M60,114 C60,86 66,72 76,64", "none", OUT, 5)])
P("spider_web", "spooky nature", lambda: [*[line(128, 128, 128 + 120 * math.cos(math.radians(a)), 128 + 120 * math.sin(math.radians(a)), SILVER, 4) for a in range(0, 360, 45)],
                                          *[poly(reg_pts(128, 128, r, 8, 22.5), "none", SILVER, 4) for r in (30, 60, 90, 116)], circle(128, 164, 16, OUT, None)])

# =========================================================================== food & drink
P("apple_red", "food health education", lambda: [path("M128,66 C90,40 30,60 34,130 C38,190 84,236 128,214 C172,236 218,190 222,130 C226,60 166,40 128,66 Z", RED, sw=8),
                                                  line(128, 66, 136, 26, BROWN, 9), path("M140,40 C160,20 196,24 200,40 C178,54 156,52 140,40 Z", GREEN, sw=6), hl_ellipse(76, 110, 14, 26, 0.4, 20)])
P("banana", "food health", lambda: [path("M40,70 C40,170 120,226 226,186 C210,176 200,170 196,160 C120,186 80,140 70,64 Z", YELLOW, sw=8), rect(32, 56, 24, 22, BROWN_L, 5)])
P("burger", "food", lambda: [path("M30,110 C30,50 226,50 226,110 Z", AMBER, sw=8), *[ellipse(x, 76, 6, 3, CREAM, None) for x in (90, 128, 166, 110, 150)],
                             path("M24,112 L232,112 L220,128 L200,118 L180,130 L160,118 L140,130 L120,118 L100,130 L80,118 L60,130 L40,118 Z", GREEN, sw=6),
                             rect(28, 128, 200, 30, BROWN, 14), rect(24, 156, 208, 16, YELLOW, 6), path("M30,170 L226,170 C226,206 30,206 30,170 Z", AMBER, sw=8)])
P("pizza_slice", "food", lambda: [path("M128,236 L30,50 C90,20 166,20 226,50 Z", YELLOW, sw=8), path("M30,50 C90,20 166,20 226,50 L216,70 C160,44 96,44 40,70 Z", AMBER, sw=6),
                                  *[circle(x, y, r, RED, OUT, 5) for x, y, r in ((100, 90, 16), (156, 100, 14), (128, 150, 15), (110, 190, 10))]])
P("french_fries", "food", lambda: [*[rect(70 + i * 22, 30 + (i % 2) * 20, 18, 110, YELLOW, 4) for i in range(6)], path("M54,96 L202,96 L184,236 L72,236 Z", RED, sw=8),
                                   poly(star_pts(128, 170, 30, 13), YELLOW, None)])
P("hotdog", "food", lambda: [g([rect(20, 96, 216, 64, AMBER, 32), rect(14, 110, 228, 36, RED_D, 18), path("M40,128 C60,112 80,144 100,128 C120,112 140,144 160,128 C180,112 200,144 220,128",
                                                                                                         "none", YELLOW, 6)], "rotate(-20 128 128)")])
P("donut", "food", lambda: [circle(128, 128, 100, TAN), path("M40,120 C40,60 216,60 216,120 C230,170 200,200 128,200 C56,200 26,170 40,120 Z", PINK, None),
                            circle(128, 128, 32, "#16213a"), *[rect(x, y, 14, 5, c, 2, None, transform=f"rotate({a} {x} {y})") for x, y, c, a in
                                                               ((80, 90, YELLOW, 30), (150, 80, SKY, -20), (180, 120, WHITE, 60), (70, 140, GREEN, -40), (110, 70, WHITE, 10), (170, 160, YELLOW, 20))]])
P("ice_cream", "food summer", lambda: [poly([(80, 120), (176, 120), (128, 240)], TAN, sw=8), *[line(96 + i * 16, 124, 128, 236, darken(TAN), 3) for i in range(5)],
                                       circle(104, 104, 34, PINK), circle(152, 104, 34, CREAM), circle(128, 64, 36, BROWN_L), circle(128, 24, 10, RED)])
P("birthday_cake", "food celebration holiday", lambda: [rect(36, 120, 184, 100, PINK, 14), path("M36,140 C60,160 80,130 104,150 C128,170 150,130 174,150 C196,166 210,140 220,140", "none", WHITE, 8),
                                                        rect(26, 212, 204, 20, SILVER, 6), *[rect(x, 76, 14, 44, c, 4) for x, c in ((76, SKY), (121, YELLOW), (166, GREEN))],
                                                        *[path(drop_d(x + 7, 60, 12), ORANGE, None) for x in (76, 121, 166)]])
P("cupcake", "food celebration", lambda: [path("M60,130 L196,130 L178,236 L78,236 Z", SKY, sw=8), *[line(x, 134, x - 4, 232, darken(SKY), 4) for x in (90, 118, 146, 174)],
                                          path(cloud_d(128, 100, 70), PINK, sw=8), circle(128, 36, 16, RED)])
P("cookie", "food", lambda: [circle(128, 128, 100, TAN), *[circle(x, y, r, BROWN, None) for x, y, r in ((90, 90, 12), (150, 80, 10), (170, 140, 13), (110, 160, 11), (140, 190, 9), (70, 140, 8))]])
P("coffee_cup", "food productivity morning", lambda: [path("M50,90 L190,90 L176,226 L64,226 Z", WHITE, sw=8), path("M188,110 C236,110 236,180 180,180", "none", OUT, 10),
                                                      rect(42, 80, 156, 22, BROWN, 6), *[path(f"M{x},70 C{x - 14},50 {x + 14},40 {x},20", "none", GRAY, 6, op=0.8) for x in (90, 128, 166)],
                                                      rect(70, 130, 100, 40, BROWN_L, 6, None)])
P("tea_cup", "food relaxation", lambda: [path("M40,110 L196,110 C196,180 160,210 118,210 C76,210 40,180 40,110 Z", TEAL, sw=8), path("M194,124 C230,124 230,170 186,170", "none", OUT, 9),
                                         ellipse(118, 222, 96, 14, SILVER), line(150, 110, 170, 40, OUT, 4), rect(160, 40, 26, 26, YELLOW, 3, OUT, 4)])
P("water_bottle", "food health fitness", lambda: [rect(96, 14, 64, 30, BLUE, 8), rect(80, 44, 96, 192, GLASS, 22), rect(80, 120, 96, 80, BLUE, 0, None, op=0.5),
                                                  hl("M94,60 L106,60 L106,200 L94,200 Z", 0.5)])
P("soda_can", "food", lambda: [rect(70, 30, 116, 200, RED, 18), ellipse(128, 32, 58, 12, SILVER), rect(70, 100, 116, 60, WHITE, 0, None), text(128, 142, "FIZZ", 30, RED),
                               hl("M84,50 L98,50 L98,214 L84,214 Z", 0.4)])
P("juice_glass", "food health", lambda: [path("M60,50 L196,50 L180,236 L76,236 Z", GLASS, sw=8), path("M66,100 L190,100 L180,236 L76,236 Z", ORANGE, None), line(150, 20, 130, 160, PINK, 10),
                                         circle(186, 60, 26, YELLOW, sw=6)])
P("milk_carton", "food kids", lambda: [poly([(66, 70), (128, 26), (190, 70), (190, 236), (66, 236)], WHITE, sw=8), poly([(66, 70), (128, 26), (190, 70)], SKY, sw=7),
                                       rect(86, 120, 84, 70, SKY, 6), text(128, 166, "MILK", 22, WHITE)])
P("egg_fried", "food breakfast", lambda: [path("M40,120 C30,60 100,40 140,56 C200,40 240,100 220,150 C210,200 150,220 110,206 C60,214 30,180 40,120 Z", WHITE, sw=8),
                                          circle(130, 130, 40, YELLOW), hl_ellipse(118, 118, 12, 7, 0.6, -30)])
P("bread_loaf", "food", lambda: [path("M30,120 C20,70 80,46 128,50 C176,46 236,70 226,120 C220,140 210,140 210,150 L210,226 L46,226 L46,150 C46,140 36,140 30,120 Z", TAN, sw=8),
                                 *[path(f"M{x},90 C{x + 10},110 {x + 10},130 {x},150", "none", BROWN_L, 6) for x in (90, 128, 166)]])
P("cheese_wedge", "food", lambda: [poly([(20, 180), (230, 90), (236, 200), (24, 230)], YELLOW, sw=8), poly([(20, 180), (230, 90), (180, 70)], GOLD, sw=7),
                                   *[circle(x, y, r, AMBER, None) for x, y, r in ((80, 200, 12), (150, 170, 16), (200, 190, 10))]])
P("carrot", "food health agriculture", lambda: [path("M60,200 C40,220 30,214 36,196 L150,70 C170,52 200,80 184,102 Z", ORANGE, sw=8), *[line(x, y, x + 20, y + 12, darken(ORANGE), 5)
                                                                                                                                for x, y in ((90, 150), (120, 116), (70, 180))],
                                                path("M170,80 C170,40 200,20 220,24 C210,50 200,70 184,90 Z", GREEN, sw=6), path("M180,90 C210,80 236,90 244,110 C220,112 200,104 186,100 Z", GREEN, sw=6)])
P("broccoli", "food health", lambda: [path("M110,140 L96,230 L160,230 L146,140 Z", LIME, sw=7), *[circle(x, y, r, GREEN, sw=7) for x, y, r in ((80, 110, 44), (128, 80, 50), (176, 110, 44), (128, 130, 40))]])
P("tomato", "food agriculture", lambda: [circle(128, 140, 96, RED, sw=8), poly(star_pts(128, 54, 40, 14, 5), GREEN, sw=5), hl_ellipse(90, 110, 18, 28, 0.35, 20)])
P("avocado", "food health", lambda: [path("M128,20 C170,20 210,110 210,160 C210,210 170,236 128,236 C86,236 46,210 46,160 C46,110 86,20 128,20 Z", GREEN_D, sw=8),
                                     path("M128,40 C160,40 192,116 192,160 C192,200 162,218 128,218 C94,218 64,200 64,160 C64,116 96,40 128,40 Z", "#bef264", None),
                                     circle(128, 160, 34, BROWN)])
P("watermelon_slice", "food summer", lambda: [path("M16,90 C40,220 216,220 240,90 Z", GREEN, sw=8), path("M32,96 C56,200 200,200 224,96 Z", RED, None),
                                              *[ellipse(x, y, 5, 9, OUT, None) for x, y in ((90, 130), (128, 150), (166, 130), (110, 110), (146, 110))]])
P("grapes", "food", lambda: [*[circle(x, y, 28, PURPLE) for x, y in ((90, 90), (146, 90), (118, 134), (74, 134), (162, 134), (100, 178), (146, 178), (124, 218))],
                             line(118, 64, 128, 20, BROWN, 8), path("M128,40 C160,20 196,30 200,50 C170,60 146,54 128,40 Z", GREEN, sw=6)])
P("strawberry", "food", lambda: [path("M128,236 C60,180 34,120 50,84 C66,56 110,64 128,74 C146,64 190,56 206,84 C222,120 196,180 128,236 Z", RED, sw=8),
                                 *[ellipse(x, y, 4, 7, YELLOW, None) for x, y in ((90, 110), (128, 120), (166, 110), (110, 160), (146, 160), (128, 200))],
                                 poly(star_pts(128, 66, 48, 16, 6), GREEN, sw=5)])
P("lemon", "food health", lambda: [ellipse(128, 128, 104, 76, YELLOW, transform="rotate(-25 128 128)"), ellipse(36, 160, 14, 10, YELLOW, OUT, 5), hl_ellipse(96, 100, 24, 12, 0.45, -25)])
P("chicken_leg", "food", lambda: [path("M40,120 C30,60 100,30 150,60 C190,84 180,140 140,156 C110,170 60,170 40,120 Z", BROWN_L, sw=8), rect(140, 140, 70, 26, CREAM, 10, transform="rotate(35 175 153)"),
                                  circle(214, 196, 18, CREAM), circle(196, 214, 18, CREAM)])
P("steak", "food", lambda: [path("M30,120 C20,60 120,40 180,60 C240,80 236,160 190,190 C140,220 50,200 30,120 Z", RED_D, sw=8), path("M60,120 C70,90 130,80 170,100", "none", PINK, 8),
                            ellipse(160, 140, 22, 18, CREAM, None)])
P("noodle_bowl", "food", lambda: [path("M20,120 L236,120 C236,190 190,230 128,230 C66,230 20,190 20,120 Z", RED, sw=8), *[path(f"M{60 + i * 22},120 C{50 + i * 22},90 {70 + i * 22},70 {64 + i * 22},50", "none", YELLOW, 6)
                                                                                                                      for i in range(6)],
                                  line(150, 20, 220, 110, BROWN, 8), line(170, 16, 236, 104, BROWN, 8), ellipse(80, 118, 22, 10, WHITE, OUT, 4)])
P("rice_bowl", "food", lambda: [path("M20,130 L236,130 C236,196 190,232 128,232 C66,232 20,196 20,130 Z", WHITE, sw=8), path(cloud_d(128, 116, 80), CREAM, sw=7),
                                path("M40,150 L216,150", "none", BLUE, 6)])
P("salad_bowl", "food health", lambda: [path("M20,130 L236,130 C236,196 190,232 128,232 C66,232 20,196 20,130 Z", TEAL, sw=8), *[circle(x, y, r, c) for x, y, r, c in
                                                                                                                                ((80, 116, 26, GREEN), (130, 100, 30, LIME), (176, 118, 24, GREEN), (110, 126, 14, RED), (156, 128, 12, RED))]])
P("sushi_roll", "food", lambda: [circle(90, 150, 66, OUT, None), circle(90, 150, 56, WHITE, None), circle(90, 150, 26, ORANGE, None), circle(90, 150, 12, GREEN, None),
                                 rect(150, 130, 90, 50, WHITE, 20), rect(150, 110, 90, 30, ORANGE, 12)])
P("candy_sweet", "food kids holiday", lambda: [poly([(40, 128), (10, 96), (10, 160)], PINK, sw=7), poly([(216, 128), (246, 96), (246, 160)], PINK, sw=7), circle(128, 128, 76, PINK, sw=8),
                                               path("M90,90 C120,110 100,160 140,170", "none", WHITE, 12)])
P("chocolate_bar", "food", lambda: [rect(40, 30, 176, 200, BROWN, 12), *[rect(56 + c * 52, 46 + r * 46, 40, 36, darken(BROWN, 0.85), 6, OUT, 4) for r in range(4) for c in range(3)],
                                    path("M40,150 L216,110 L216,230 L40,230 Z", RED, sw=8)])
P("honey_jar", "food nature", lambda: [rect(54, 80, 148, 156, AMBER, 30), rect(66, 40, 124, 44, BROWN_L, 10), rect(80, 130, 96, 60, CREAM, 8), text(128, 170, "HONEY", 20, BROWN)])
P("salt_shaker", "food cooking", lambda: [path("M80,80 C80,40 176,40 176,80 L184,230 L72,230 Z", WHITE, sw=8), *[circle(x, 56, 5, OUT, None) for x in (108, 128, 148)], rect(72, 80, 112, 20, SILVER, 6)])
P("frying_pan", "food cooking", lambda: [ellipse(110, 130, 96, 70, GRAY_D), ellipse(110, 126, 78, 54, SLATE, None), rect(196, 116, 60, 22, BROWN, 8),
                                         path("M70,120 C66,96 100,88 116,98 C140,90 156,116 146,136 C140,160 108,164 94,154 C74,158 64,140 70,120 Z", WHITE, None),
                                         circle(108, 124, 16, YELLOW, None)])
P("cooking_pot", "food cooking", lambda: [rect(40, 100, 176, 120, RED, 18), rect(30, 86, 196, 24, RED_D, 8), rect(108, 60, 40, 26, GRAY_D, 8), rect(10, 130, 30, 18, OUT, 6, None),
                                          rect(216, 130, 30, 18, OUT, 6, None), *[path(f"M{x},50 C{x - 12},34 {x + 12},24 {x},8", "none", GRAY, 6, op=0.7) for x in (80, 176)]])
P("fork_knife", "food cooking", lambda: [rect(66, 110, 24, 130, SILVER, 10), path("M54,24 L54,96 C54,116 102,116 102,96 L102,24", "none", OUT, 0),
                                         *[rect(x, 20, 10, 80, SILVER, 4) for x in (52, 73, 94)], rect(52, 90, 52, 30, SILVER, 10),
                                         path("M170,20 C200,40 206,110 190,130 L190,240 L166,240 L166,20 Z", SILVER, sw=7)])
P("chef_knife", "food cooking", lambda: [g([path("M30,140 L190,100 L200,140 L30,150 Z", SILVER, sw=7), rect(196, 108, 60, 30, BROWN, 8)], "rotate(-20 128 128)")])
P("pizza_box", "food delivery", lambda: [poly([(20, 120), (128, 80), (236, 120), (128, 160)], TAN, sw=7), poly([(20, 120), (128, 160), (128, 220), (20, 180)], BROWN_L, sw=7),
                                         poly([(236, 120), (128, 160), (128, 220), (236, 180)], darken(TAN), sw=7), circle(128, 118, 22, RED, OUT, 4)])
P("lunch_box", "food kids education", lambda: [rect(30, 90, 196, 136, BLUE, 18), path("M90,90 L90,60 C90,46 166,46 166,60 L166,90", "none", OUT, 12), rect(30, 150, 196, 10, OUT, 0, None)])
P("baby_bottle", "family kids", lambda: [path("M110,40 C110,16 146,16 146,40 Z", AMBER, sw=7), rect(94, 40, 68, 24, SKY, 6), rect(80, 64, 96, 170, WHITE, 26),
                                         *[line(80, y, 104, y, OUT, 4) for y in (110, 140, 170)], rect(80, 150, 96, 84, CREAM, 0, None, op=0.8)])
P("popcorn_bucket", "food entertainment", lambda: [*[circle(x, y, 26, CREAM) for x, y in ((70, 70), (110, 50), (150, 54), (190, 72), (130, 84), (90, 96), (170, 96))],
                                                   path("M40,100 L216,100 L196,236 L60,236 Z", WHITE, sw=8), *[path(f"M{60 + i * 34},100 L{68 + i * 30},236 L{86 + i * 30},236 L{80 + i * 34},100 Z", RED, None)
                                                                                                             for i in range(0, 5, 2)]])
