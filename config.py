"""
Nihongo Quest - Game Configuration
===================================
Central configuration constants for the Nihongo Quest 3D Japanese learning
adventure game. All tunable parameters, color schemes, monument definitions,
and difficulty presets live here.
"""

import os

# ---------------------------------------------------------------------------
# Window & Display
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Nihongo Quest"
GAME_VERSION = "0.1.0"
FULLSCREEN_DEFAULT = False
FPS_CAP = 60
VSYNC = True

# ---------------------------------------------------------------------------
# Paths & Saves
# ---------------------------------------------------------------------------
# Cross-platform but targeting Windows (AppData/Local)
_home = os.path.expanduser("~")
if os.name == "nt":
    SAVE_BASE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.join(_home, "AppData", "Local")),
                                 "NihongoQuest")
else:
    SAVE_BASE_DIR = os.path.join(_home, ".local", "share", "NihongoQuest")

SAVE_DIR = os.path.join(SAVE_BASE_DIR, "saves")
SETTINGS_FILE = os.path.join(SAVE_BASE_DIR, "settings.json")
LOG_DIR = os.path.join(SAVE_BASE_DIR, "logs")

MAX_SAVE_SLOTS = 6

# ---------------------------------------------------------------------------
# Color Schemes  (Japanese-themed palette)
# ---------------------------------------------------------------------------
# Colors are stored as (R, G, B, A) floats 0-1, suitable for Ursina's Color.

COLORS = {
    # --- Primary UI ---
    "sakura_pink":      (0.94, 0.69, 0.75, 1.0),   # Cherry blossom pink
    "sakura_light":     (0.98, 0.85, 0.88, 1.0),   # Lighter cherry blossom
    "indigo":           (0.14, 0.12, 0.36, 1.0),   # Deep indigo (ai-iro)
    "indigo_light":     (0.27, 0.25, 0.52, 1.0),   # Lighter indigo
    "vermillion":       (0.85, 0.20, 0.12, 1.0),   # Torii gate red (shu-iro)
    "vermillion_dark":  (0.65, 0.14, 0.08, 1.0),   # Darker vermillion

    # --- Accent / Nature ---
    "matcha_green":     (0.44, 0.60, 0.32, 1.0),   # Matcha / bamboo green
    "matcha_dark":      (0.28, 0.42, 0.18, 1.0),   # Deeper matcha
    "wisteria":         (0.55, 0.44, 0.69, 1.0),   # Fuji (wisteria) purple
    "sky_blue":         (0.53, 0.75, 0.87, 1.0),   # Sora-iro (sky color)
    "gold":             (0.85, 0.72, 0.30, 1.0),   # Kin-iro (gold)
    "gold_bright":      (0.95, 0.82, 0.35, 1.0),   # Brighter gold for highlights

    # --- Neutrals ---
    "sumi_black":       (0.12, 0.11, 0.10, 1.0),   # Ink black (sumi)
    "washi_white":      (0.96, 0.94, 0.90, 1.0),   # Japanese paper white
    "stone_gray":       (0.55, 0.53, 0.50, 1.0),   # Stone gray
    "warm_cream":       (0.93, 0.89, 0.80, 1.0),   # Warm parchment cream

    # --- Semantic ---
    "correct":          (0.20, 0.72, 0.35, 1.0),   # Green for correct answers
    "incorrect":        (0.85, 0.22, 0.18, 1.0),   # Red for incorrect answers
    "highlight":        (1.00, 0.88, 0.30, 1.0),   # Yellow highlight
    "disabled":         (0.50, 0.48, 0.46, 0.6),   # Grayed-out / disabled
    "xp_bar":           (0.30, 0.65, 0.90, 1.0),   # XP progress bar blue
    "health_bar":       (0.80, 0.25, 0.20, 1.0),   # Health / streak bar

    # --- Backgrounds ---
    "bg_menu":          (0.08, 0.07, 0.18, 1.0),   # Dark menu background
    "bg_dialog":        (0.10, 0.09, 0.14, 0.92),  # Semi-transparent dialog
    "bg_panel":         (0.16, 0.14, 0.22, 0.95),  # Panel background
}

# ---------------------------------------------------------------------------
# Monuments  (learning stages mapped to in-world locations)
# ---------------------------------------------------------------------------
# Each monument is a dict with an id, name, Japanese name, description,
# the category of content it teaches, and the required minigame group
# that must be completed to unlock it.

MONUMENTS = {
    0:  {
        "name":         "Hiragana Temple",
        "name_jp":      "ひらがな寺",
        "description":  "The foundation of Japanese writing. Master the 46 basic hiragana characters.",
        "category":     "hiragana",
        "unlock_requires": None,  # Always unlocked
    },
    1:  {
        "name":         "Katakana Shrine",
        "name_jp":      "カタカナ神社",
        "description":  "Learn katakana, used for foreign words and emphasis.",
        "category":     "katakana",
        "unlock_requires": "hiragana",
    },
    2:  {
        "name":         "Grammar Garden",
        "name_jp":      "文法庭園",
        "description":  "Discover basic Japanese sentence structures and particles.",
        "category":     "grammar_basic",
        "unlock_requires": "katakana",
    },
    3:  {
        "name":         "Vocabulary Village",
        "name_jp":      "語彙の村",
        "description":  "Build your first 200 essential Japanese words.",
        "category":     "vocabulary_basic",
        "unlock_requires": "grammar_basic",
    },
    4:  {
        "name":         "Verb Dojo",
        "name_jp":      "動詞道場",
        "description":  "Master verb conjugations: masu, te-form, past tense, and more.",
        "category":     "verbs",
        "unlock_requires": "vocabulary_basic",
    },
    5:  {
        "name":         "Kanji Castle N5",
        "name_jp":      "漢字城 N5",
        "description":  "Learn the ~100 kanji required for JLPT N5.",
        "category":     "kanji_n5",
        "unlock_requires": "verbs",
    },
    6:  {
        "name":         "Listening Lake",
        "name_jp":      "聴解の湖",
        "description":  "Train your ear with native-speed listening exercises.",
        "category":     "listening",
        "unlock_requires": "kanji_n5",
    },
    7:  {
        "name":         "Grammar Grove",
        "name_jp":      "文法の森",
        "description":  "Intermediate grammar: conditionals, passive, causative.",
        "category":     "grammar_intermediate",
        "unlock_requires": "listening",
    },
    8:  {
        "name":         "Kanji Keep N4/N3",
        "name_jp":      "漢字砦 N4/N3",
        "description":  "Conquer ~350 intermediate kanji for JLPT N4 and N3.",
        "category":     "kanji_intermediate",
        "unlock_requires": "grammar_intermediate",
    },
    9:  {
        "name":         "Reading Realm",
        "name_jp":      "読解の国",
        "description":  "Practice reading passages, short stories, and articles.",
        "category":     "reading",
        "unlock_requires": "kanji_intermediate",
    },
    10: {
        "name":         "Conversation Court",
        "name_jp":      "会話の宮廷",
        "description":  "Role-play real-life conversations and dialogues.",
        "category":     "conversation",
        "unlock_requires": "reading",
    },
    11: {
        "name":         "Advanced Academy",
        "name_jp":      "上級学院",
        "description":  "Advanced grammar, nuance, and keigo (polite language).",
        "category":     "advanced",
        "unlock_requires": "conversation",
    },
    12: {
        "name":         "Immersion Island",
        "name_jp":      "没入島",
        "description":  "Full-immersion challenges: no English, only Japanese.",
        "category":     "immersion",
        "unlock_requires": "advanced",
    },
}

# Convenience: monument id -> name string
MONUMENT_NAMES = {mid: m["name"] for mid, m in MONUMENTS.items()}

# Convenience: category -> monument id  (reverse lookup)
CATEGORY_TO_MONUMENT = {m["category"]: mid for mid, m in MONUMENTS.items()}

TOTAL_MONUMENTS = len(MONUMENTS)

# ---------------------------------------------------------------------------
# Difficulty Settings
# ---------------------------------------------------------------------------
# Each difficulty adjusts timers, hints, SRS intervals, and scoring.

DIFFICULTY_SETTINGS = {
    "easy": {
        "label":                "Easy",
        "label_jp":             "やさしい",
        "description":          "Relaxed pace with extra hints. Great for absolute beginners.",
        "timer_multiplier":     1.5,    # 50% more time on timed challenges
        "hint_count":           3,      # Hints available per question
        "srs_interval_mult":    0.8,    # SRS intervals are shorter (more review)
        "xp_multiplier":        0.8,    # Slightly less XP
        "minigame_lives":       5,      # Lives in minigames
        "show_romaji":          True,   # Show romaji alongside kana
        "show_furigana":        True,   # Show furigana above kanji
        "consecutive_correct_to_master": 6,  # Answers needed for mastery
    },
    "normal": {
        "label":                "Normal",
        "label_jp":             "ふつう",
        "description":          "Balanced challenge for steady learners.",
        "timer_multiplier":     1.0,
        "hint_count":           2,
        "srs_interval_mult":    1.0,
        "xp_multiplier":        1.0,
        "minigame_lives":       3,
        "show_romaji":          False,
        "show_furigana":        True,
        "consecutive_correct_to_master": 5,
    },
    "hard": {
        "label":                "Hard",
        "label_jp":             "むずかしい",
        "description":          "Minimal assistance. Prove your Japanese mastery.",
        "timer_multiplier":     0.75,
        "hint_count":           1,
        "srs_interval_mult":    1.3,    # Longer intervals (less review)
        "xp_multiplier":        1.3,    # Bonus XP reward
        "minigame_lives":       2,
        "show_romaji":          False,
        "show_furigana":        False,
        "consecutive_correct_to_master": 4,
    },
    "extreme": {
        "label":                "Extreme",
        "label_jp":             "鬼",
        "description":          "No hints. Strict timing. Only for the fearless.",
        "timer_multiplier":     0.5,
        "hint_count":           0,
        "srs_interval_mult":    1.6,
        "xp_multiplier":        1.8,
        "minigame_lives":       1,
        "show_romaji":          False,
        "show_furigana":        False,
        "consecutive_correct_to_master": 3,
    },
}

DEFAULT_DIFFICULTY = "normal"

# ---------------------------------------------------------------------------
# XP & Leveling
# ---------------------------------------------------------------------------
BASE_XP_PER_LEVEL = 100          # XP needed for level 1 -> 2
XP_GROWTH_FACTOR = 1.15          # Each level requires 15% more XP
MAX_PLAYER_LEVEL = 100

# XP rewards (base values, multiplied by difficulty xp_multiplier)
XP_REWARDS = {
    "lesson_complete":      50,
    "minigame_complete":    80,
    "minigame_perfect":     150,   # Bonus for zero mistakes
    "character_mastered":   20,
    "word_mastered":        25,
    "grammar_mastered":     40,
    "monument_complete":    500,
    "daily_streak_bonus":   30,    # Per day of streak
    "first_try_correct":    15,
    "review_complete":      25,
}

# ---------------------------------------------------------------------------
# SRS (Spaced Repetition System) Intervals — in hours
# ---------------------------------------------------------------------------
SRS_STAGES = {
    "new":       0,       # Just introduced
    "learning":  4,       # Review after 4 hours
    "review":    24,      # Review after 1 day
    "mastered":  168,     # Review after 7 days (maintenance)
}

# ---------------------------------------------------------------------------
# Character Creation Defaults
# ---------------------------------------------------------------------------
CHARACTER_CREATION = {
    "body_types":    ["slim", "average", "athletic", "stocky"],
    "hair_styles":   ["short", "medium", "long", "ponytail", "bun", "spiky", "braids"],
    "hair_colors":   ["black", "brown", "auburn", "blonde", "white", "blue", "pink", "red"],
    "eye_colors":    ["brown", "hazel", "blue", "green", "amber", "gray", "violet"],
    "skin_tones":    ["fair", "light", "medium", "tan", "olive", "brown", "dark"],
    "outfit_styles": ["casual", "school_uniform", "traditional", "adventurer", "modern"],
}

# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
MASTER_VOLUME = 0.8
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.7
VOICE_VOLUME = 0.9

# ---------------------------------------------------------------------------
# Gameplay Constants
# ---------------------------------------------------------------------------
OVERWORLD_CAMERA_HEIGHT = 12.0
OVERWORLD_CAMERA_ANGLE = 45.0
DIALOG_TEXT_SPEED = 0.03         # Seconds per character in dialog boxes
AUTO_SAVE_INTERVAL = 300         # Auto-save every 5 minutes (seconds)
MAX_DAILY_STREAK = 365           # Cap display at 1 year
