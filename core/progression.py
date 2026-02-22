"""
Nihongo Quest - Progression System
====================================
Handles XP / leveling, SRS-based character mastery tracking, monument
completion scoring, and adaptive lesson recommendations.

Pure Python — no Ursina imports — for easy testing and reuse.
"""

from __future__ import annotations

import math
import time
import logging
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

from nihongo_quest.config import (
    BASE_XP_PER_LEVEL,
    XP_GROWTH_FACTOR,
    MAX_PLAYER_LEVEL,
    XP_REWARDS,
    SRS_STAGES,
    MONUMENTS,
    TOTAL_MONUMENTS,
    DIFFICULTY_SETTINGS,
    DEFAULT_DIFFICULTY,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SRS mastery stages
# ---------------------------------------------------------------------------

class MasteryStage(IntEnum):
    """
    Ordered stages for spaced-repetition mastery.
    Higher value = more mastered.
    """
    NEW       = 0
    LEARNING  = 1
    REVIEW    = 2
    MASTERED  = 3


STAGE_NAMES = {
    MasteryStage.NEW:      "new",
    MasteryStage.LEARNING: "learning",
    MasteryStage.REVIEW:   "review",
    MasteryStage.MASTERED: "mastered",
}

_NAME_TO_STAGE = {v: k for k, v in STAGE_NAMES.items()}


def _stage_from_name(name: str) -> MasteryStage:
    """Convert a stage name string back to the enum."""
    return _NAME_TO_STAGE.get(name, MasteryStage.NEW)


# ---------------------------------------------------------------------------
# XP / Leveling helpers
# ---------------------------------------------------------------------------

def xp_required_for_level(level: int) -> int:
    """
    Return the *total cumulative* XP needed to reach ``level``.

    Level 1 requires 0 XP (starting level).
    Level 2 requires ``BASE_XP_PER_LEVEL`` XP, and each subsequent level
    requires ``XP_GROWTH_FACTOR`` times more than the previous.

    Parameters
    ----------
    level : int
        Target level (1-based).  Clamped to ``[1, MAX_PLAYER_LEVEL]``.

    Returns
    -------
    int
    """
    level = max(1, min(level, MAX_PLAYER_LEVEL))
    if level <= 1:
        return 0
    total = 0.0
    for lv in range(2, level + 1):
        total += BASE_XP_PER_LEVEL * (XP_GROWTH_FACTOR ** (lv - 2))
    return int(math.ceil(total))


def xp_for_next_level(current_level: int) -> int:
    """
    Return the *incremental* XP needed to advance from ``current_level``
    to ``current_level + 1``.
    """
    current_level = max(1, min(current_level, MAX_PLAYER_LEVEL - 1))
    return xp_required_for_level(current_level + 1) - xp_required_for_level(current_level)


def level_from_xp(total_xp: int) -> int:
    """
    Given total accumulated XP, return the player's current level.
    """
    total_xp = max(0, total_xp)
    for lv in range(1, MAX_PLAYER_LEVEL + 1):
        if xp_required_for_level(lv + 1) > total_xp:
            return lv
    return MAX_PLAYER_LEVEL


def xp_progress_in_level(total_xp: int) -> Tuple[int, int]:
    """
    Return ``(xp_into_current_level, xp_needed_for_next_level)``.

    Useful for drawing a progress bar.
    """
    lv = level_from_xp(total_xp)
    base = xp_required_for_level(lv)
    needed = xp_for_next_level(lv)
    return (total_xp - base, needed)


def calculate_xp_reward(reward_key: str, difficulty: str = DEFAULT_DIFFICULTY) -> int:
    """
    Look up the base XP for *reward_key* and apply the difficulty multiplier.

    Parameters
    ----------
    reward_key : str
        One of the keys in ``config.XP_REWARDS``.
    difficulty : str
        Difficulty name.

    Returns
    -------
    int
    """
    base = XP_REWARDS.get(reward_key, 0)
    mult = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])["xp_multiplier"]
    return int(math.ceil(base * mult))


# ---------------------------------------------------------------------------
# SRS Character / Item Tracker
# ---------------------------------------------------------------------------

class SRSItem:
    """
    Tracks the mastery state of a single learnable item (character, word,
    grammar point, etc.) using a simplified spaced-repetition model.

    Progression through stages is based on *consecutive correct answers*.
    An incorrect answer resets the consecutive counter and may demote the
    stage.
    """

    def __init__(
        self,
        item_id: str,
        stage: MasteryStage = MasteryStage.NEW,
        consecutive_correct: int = 0,
        total_correct: int = 0,
        total_attempts: int = 0,
        last_reviewed: float = 0.0,
        next_review: float = 0.0,
    ) -> None:
        self.item_id = item_id
        self.stage = stage
        self.consecutive_correct = consecutive_correct
        self.total_correct = total_correct
        self.total_attempts = total_attempts
        self.last_reviewed = last_reviewed
        self.next_review = next_review

    # ---- Serialization ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage":                STAGE_NAMES[self.stage],
            "consecutive":          self.consecutive_correct,
            "total_correct":        self.total_correct,
            "total_attempts":       self.total_attempts,
            "last_reviewed":        self.last_reviewed,
            "next_review":          self.next_review,
        }

    @classmethod
    def from_dict(cls, item_id: str, data: Dict[str, Any]) -> SRSItem:
        return cls(
            item_id=item_id,
            stage=_stage_from_name(data.get("stage", "new")),
            consecutive_correct=data.get("consecutive", 0),
            total_correct=data.get("total_correct", 0),
            total_attempts=data.get("total_attempts", 0),
            last_reviewed=data.get("last_reviewed", 0.0),
            next_review=data.get("next_review", 0.0),
        )

    # ---- Review logic -------------------------------------------------------

    def record_answer(self, correct: bool, consecutive_to_master: int = 5,
                      srs_interval_mult: float = 1.0) -> MasteryStage:
        """
        Record a review answer and update the item's mastery state.

        Parameters
        ----------
        correct : bool
            Whether the player answered correctly.
        consecutive_to_master : int
            How many consecutive correct answers are needed to advance
            one stage.  Derived from the difficulty setting.
        srs_interval_mult : float
            Multiplier applied to the base SRS review interval.

        Returns
        -------
        MasteryStage
            The stage *after* applying this answer.
        """
        now = time.time()
        self.total_attempts += 1
        self.last_reviewed = now

        if correct:
            self.total_correct += 1
            self.consecutive_correct += 1

            # Advance stage when streak threshold is met
            if self.consecutive_correct >= consecutive_to_master:
                if self.stage < MasteryStage.MASTERED:
                    self.stage = MasteryStage(self.stage + 1)
                    self.consecutive_correct = 0  # reset streak for next stage
                    logger.debug("Item '%s' promoted to %s", self.item_id, STAGE_NAMES[self.stage])
        else:
            self.consecutive_correct = 0
            # Demote one stage on miss (but never below NEW)
            if self.stage > MasteryStage.NEW:
                self.stage = MasteryStage(self.stage - 1)
                logger.debug("Item '%s' demoted to %s", self.item_id, STAGE_NAMES[self.stage])

        # Schedule next review
        base_hours = SRS_STAGES.get(STAGE_NAMES[self.stage], 0)
        interval_seconds = base_hours * 3600 * srs_interval_mult
        self.next_review = now + interval_seconds

        return self.stage

    def is_due_for_review(self) -> bool:
        """Return True if the item should be reviewed now."""
        if self.stage == MasteryStage.NEW:
            return True  # New items are always "due"
        return time.time() >= self.next_review

    @property
    def accuracy(self) -> float:
        """Lifetime accuracy as a ratio 0.0 – 1.0."""
        if self.total_attempts == 0:
            return 0.0
        return self.total_correct / self.total_attempts


# ---------------------------------------------------------------------------
# Progression Tracker  (operates on a full save-data dict)
# ---------------------------------------------------------------------------

class ProgressionTracker:
    """
    High-level helper that reads/writes SRS data from/to the save-data
    dictionary and provides aggregated progress queries.
    """

    def __init__(self, save_data: Dict[str, Any]) -> None:
        """
        Parameters
        ----------
        save_data : dict
            A reference to the live save-data dictionary.  Mutations will
            be reflected in the dict (no copy is made).
        """
        self._data = save_data
        self._difficulty = save_data.get("difficulty", DEFAULT_DIFFICULTY)
        self._diff_settings = DIFFICULTY_SETTINGS.get(
            self._difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY]
        )

    # ---- SRS access ---------------------------------------------------------

    def get_srs_item(self, script: str, item_id: str) -> SRSItem:
        """
        Fetch (or create) the SRS item for a character in the given script.

        Parameters
        ----------
        script : str
            ``"hiragana"``, ``"katakana"``, or ``"kanji"``.
        item_id : str
            The character/word string, e.g. ``"あ"`` or ``"食"``.

        Returns
        -------
        SRSItem
        """
        mc = self._data.setdefault("mastered_characters", {})
        script_dict = mc.setdefault(script, {})

        if item_id in script_dict and isinstance(script_dict[item_id], dict):
            return SRSItem.from_dict(item_id, script_dict[item_id])
        else:
            return SRSItem(item_id=item_id)

    def save_srs_item(self, script: str, item: SRSItem) -> None:
        """Persist an SRSItem back into the save data."""
        mc = self._data.setdefault("mastered_characters", {})
        script_dict = mc.setdefault(script, {})
        script_dict[item.item_id] = item.to_dict()

    def record_character_answer(self, script: str, item_id: str, correct: bool) -> MasteryStage:
        """
        Convenience: load item, record answer, save, return new stage.
        """
        item = self.get_srs_item(script, item_id)
        new_stage = item.record_answer(
            correct=correct,
            consecutive_to_master=self._diff_settings["consecutive_correct_to_master"],
            srs_interval_mult=self._diff_settings["srs_interval_mult"],
        )
        self.save_srs_item(script, item)
        return new_stage

    # ---- Due items ----------------------------------------------------------

    def get_due_items(self, script: str, limit: int = 20) -> List[SRSItem]:
        """
        Return up to *limit* items in *script* that are due for review,
        sorted with the most overdue first.
        """
        mc = self._data.get("mastered_characters", {})
        script_dict = mc.get(script, {})
        now = time.time()

        items: List[SRSItem] = []
        for item_id, info in script_dict.items():
            if not isinstance(info, dict):
                continue
            srs = SRSItem.from_dict(item_id, info)
            if srs.is_due_for_review():
                items.append(srs)

        # Sort: most overdue first (lowest next_review)
        items.sort(key=lambda s: s.next_review)
        return items[:limit]

    def get_new_items_count(self, script: str) -> int:
        """Count items that are still at the NEW stage."""
        mc = self._data.get("mastered_characters", {})
        script_dict = mc.get(script, {})
        return sum(
            1 for info in script_dict.values()
            if isinstance(info, dict) and info.get("stage") == "new"
        )

    # ---- Monument completion ------------------------------------------------

    def monument_completion_percentage(self, monument_id: int) -> float:
        """
        Calculate what fraction of a monument's content has been completed.

        Measures lessons + minigames with matching category prefixes against
        an expected count.  Returns 0.0 – 100.0.
        """
        if monument_id not in MONUMENTS:
            return 0.0

        category = MONUMENTS[monument_id]["category"]
        prefix = f"{category}_"

        lesson_count = sum(
            1 for lid in self._data.get("completed_lessons", [])
            if lid.startswith(prefix)
        )
        minigame_count = sum(
            1 for mid in self._data.get("completed_minigames", [])
            if mid.startswith(prefix)
        )

        # Also count mastered characters for character-based monuments
        mastered_count = 0
        if category in ("hiragana", "katakana"):
            script_dict = self._data.get("mastered_characters", {}).get(category, {})
            mastered_count = sum(
                1 for info in script_dict.values()
                if isinstance(info, dict) and info.get("stage") == "mastered"
            )
        elif category.startswith("kanji"):
            script_dict = self._data.get("mastered_characters", {}).get("kanji", {})
            mastered_count = sum(
                1 for info in script_dict.values()
                if isinstance(info, dict) and info.get("stage") == "mastered"
            )

        # Weighted score: lessons (30%) + minigames (30%) + mastery (40%)
        # Use expected counts for normalization
        expected_lessons = 5
        expected_minigames = 3
        expected_mastery = self._expected_mastery_count(category)

        lesson_pct = min(1.0, lesson_count / expected_lessons) if expected_lessons else 0.0
        minigame_pct = min(1.0, minigame_count / expected_minigames) if expected_minigames else 0.0
        mastery_pct = min(1.0, mastered_count / expected_mastery) if expected_mastery else 0.0

        weighted = (lesson_pct * 0.30) + (minigame_pct * 0.30) + (mastery_pct * 0.40)
        return round(weighted * 100, 1)

    @staticmethod
    def _expected_mastery_count(category: str) -> int:
        """Return the expected number of items to master for a given category."""
        expectations = {
            "hiragana":             46,
            "katakana":             46,
            "grammar_basic":        20,
            "vocabulary_basic":     200,
            "verbs":                50,
            "kanji_n5":             100,
            "listening":            30,
            "grammar_intermediate": 40,
            "kanji_intermediate":   350,
            "reading":              25,
            "conversation":         20,
            "advanced":             60,
            "immersion":            30,
        }
        return expectations.get(category, 30)

    # ---- Weakness analysis & recommendations --------------------------------

    def get_weakest_areas(self) -> List[Dict[str, Any]]:
        """
        Analyze the player's progress and return a list of weak areas
        sorted from weakest to strongest.

        Each entry is a dict with ``category``, ``monument_id``,
        ``monument_name``, ``completion``, and ``reason``.
        """
        weaknesses: List[Dict[str, Any]] = []

        for mid in range(TOTAL_MONUMENTS):
            # Only consider unlocked or in-progress monuments
            # (We check up to current_monument + 1 for "next up" recommendations)
            current = self._data.get("current_monument", 0)
            if mid > current + 1:
                continue

            completion = self.monument_completion_percentage(mid)
            if completion >= 100.0:
                continue  # Fully done — not weak

            category = MONUMENTS[mid]["category"]
            reason = self._diagnose_weakness(category)

            weaknesses.append({
                "category":      category,
                "monument_id":   mid,
                "monument_name": MONUMENTS[mid]["name"],
                "completion":    completion,
                "reason":        reason,
            })

        weaknesses.sort(key=lambda w: w["completion"])
        return weaknesses

    def _diagnose_weakness(self, category: str) -> str:
        """Produce a human-readable reason why a category is weak."""
        prefix = f"{category}_"
        lessons_done = sum(
            1 for lid in self._data.get("completed_lessons", [])
            if lid.startswith(prefix)
        )
        minigames_done = sum(
            1 for mid in self._data.get("completed_minigames", [])
            if mid.startswith(prefix)
        )

        if lessons_done == 0:
            return "No lessons started yet."
        if minigames_done == 0:
            return "Lessons started but no minigames attempted."

        # Check for low-accuracy characters in this category
        low_accuracy = self._count_low_accuracy_items(category)
        if low_accuracy > 0:
            return f"{low_accuracy} item(s) with low accuracy — more practice needed."

        return "In progress — keep going!"

    def _count_low_accuracy_items(self, category: str, threshold: float = 0.5) -> int:
        """Count SRS items under the accuracy threshold."""
        script = category
        if category.startswith("kanji"):
            script = "kanji"
        elif category not in ("hiragana", "katakana"):
            return 0  # Non-character categories don't have SRS items (yet)

        script_dict = self._data.get("mastered_characters", {}).get(script, {})
        count = 0
        for info in script_dict.values():
            if not isinstance(info, dict):
                continue
            attempts = info.get("total_attempts", 0)
            correct = info.get("total_correct", 0)
            if attempts >= 3 and (correct / attempts) < threshold:
                count += 1
        return count

    def recommend_next_lesson(self) -> Optional[Dict[str, Any]]:
        """
        Determine the single best lesson for the player to do next.

        Strategy:
        1. If there are items due for SRS review, recommend a review session
           in the weakest script.
        2. If the current monument has incomplete lessons, recommend the next
           unfinished lesson.
        3. If all lessons in the current monument are done but minigames
           remain, recommend a minigame.
        4. If the current monument is fully complete and the next is unlocked,
           recommend starting the next monument.

        Returns
        -------
        dict or None
            ``{"type": "review"|"lesson"|"minigame"|"new_monument",
               "category": str, "monument_id": int, "detail": str}``
        """
        current = self._data.get("current_monument", 0)
        category = MONUMENTS[current]["category"]

        # 1) Check for due SRS reviews
        for script in ("hiragana", "katakana", "kanji"):
            due = self.get_due_items(script, limit=1)
            if due:
                return {
                    "type":         "review",
                    "category":     script,
                    "monument_id":  current,
                    "detail":       f"Review {script} characters — {len(self.get_due_items(script, limit=100))} item(s) due.",
                }

        # 2) Incomplete lessons in current monument
        prefix = f"{category}_"
        completed_lessons = set(self._data.get("completed_lessons", []))
        # Assume lessons are numbered: category_lesson_1, category_lesson_2, ...
        for n in range(1, 6):  # Up to 5 lessons per monument
            lesson_id = f"{prefix}lesson_{n}"
            if lesson_id not in completed_lessons:
                return {
                    "type":         "lesson",
                    "category":     category,
                    "monument_id":  current,
                    "detail":       f"Continue with lesson {n} at {MONUMENTS[current]['name']}.",
                }

        # 3) Incomplete minigames in current monument
        completed_minigames = set(self._data.get("completed_minigames", []))
        for n in range(1, 4):  # Up to 3 minigames per monument
            mg_id = f"{prefix}minigame_{n}"
            if mg_id not in completed_minigames:
                return {
                    "type":         "minigame",
                    "category":     category,
                    "monument_id":  current,
                    "detail":       f"Play minigame {n} at {MONUMENTS[current]['name']} to prove mastery.",
                }

        # 4) Current monument complete — recommend next
        next_id = current + 1
        if next_id < TOTAL_MONUMENTS:
            return {
                "type":         "new_monument",
                "category":     MONUMENTS[next_id]["category"],
                "monument_id":  next_id,
                "detail":       f"Advance to {MONUMENTS[next_id]['name']} ({MONUMENTS[next_id]['name_jp']})!",
            }

        # Everything done!
        return None

    # ---- XP helpers ---------------------------------------------------------

    def award_xp(self, reward_key: str) -> Dict[str, Any]:
        """
        Award XP for an event, applying difficulty scaling.

        Reads/writes ``player_xp`` and ``player_level`` keys on the save data.

        Returns
        -------
        dict
            ``{"xp_gained": int, "new_total_xp": int, "level": int,
               "leveled_up": bool, "old_level": int}``
        """
        xp_gained = calculate_xp_reward(reward_key, self._difficulty)
        total_xp = self._data.get("player_xp", 0) + xp_gained
        old_level = self._data.get("player_level", 1)
        new_level = level_from_xp(total_xp)

        self._data["player_xp"] = total_xp
        self._data["player_level"] = new_level

        leveled_up = new_level > old_level
        if leveled_up:
            logger.info("Player leveled up! %d -> %d", old_level, new_level)

        return {
            "xp_gained":    xp_gained,
            "new_total_xp": total_xp,
            "level":        new_level,
            "leveled_up":   leveled_up,
            "old_level":    old_level,
        }

    def get_level_info(self) -> Dict[str, Any]:
        """
        Return the player's current level information.

        Returns
        -------
        dict
            ``{"level": int, "total_xp": int, "xp_in_level": int,
               "xp_for_next": int, "progress_pct": float}``
        """
        total_xp = self._data.get("player_xp", 0)
        level = level_from_xp(total_xp)
        xp_in, xp_need = xp_progress_in_level(total_xp)
        pct = round(xp_in / xp_need * 100, 1) if xp_need else 100.0

        return {
            "level":        level,
            "total_xp":     total_xp,
            "xp_in_level":  xp_in,
            "xp_for_next":  xp_need,
            "progress_pct": pct,
        }

    # ---- Bulk stats ---------------------------------------------------------

    def get_full_stats(self) -> Dict[str, Any]:
        """
        Comprehensive stats blob for dashboards, achievements, etc.
        """
        mastery_counts = {"hiragana": 0, "katakana": 0, "kanji": 0}
        total_counts = {"hiragana": 0, "katakana": 0, "kanji": 0}

        mc = self._data.get("mastered_characters", {})
        for script in ("hiragana", "katakana", "kanji"):
            script_dict = mc.get(script, {})
            total_counts[script] = len(script_dict)
            mastery_counts[script] = sum(
                1 for info in script_dict.values()
                if isinstance(info, dict) and info.get("stage") == "mastered"
            )

        monument_progress = {}
        for mid in range(TOTAL_MONUMENTS):
            monument_progress[mid] = {
                "name":       MONUMENTS[mid]["name"],
                "completion": self.monument_completion_percentage(mid),
            }

        return {
            "level_info":         self.get_level_info(),
            "mastery_counts":     mastery_counts,
            "total_tracked":      total_counts,
            "vocabulary_count":   len(self._data.get("vocabulary_learned", [])),
            "grammar_count":      len(self._data.get("grammar_learned", [])),
            "lessons_completed":  len(self._data.get("completed_lessons", [])),
            "minigames_completed": len(self._data.get("completed_minigames", [])),
            "monument_progress":  monument_progress,
            "weakest_areas":      self.get_weakest_areas(),
            "recommendation":     self.recommend_next_lesson(),
            "difficulty":         self._difficulty,
        }
