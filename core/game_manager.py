"""
Nihongo Quest - Game Manager
==============================
Central singleton that owns all runtime game state: current scene, player
progress, monument unlocks, and learning statistics.

This module is **pure Python** (no Ursina imports) so it can be unit-tested
without a GPU or windowing system.
"""

from __future__ import annotations

import logging
import time
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set

from config import (
    MONUMENTS,
    TOTAL_MONUMENTS,
    DIFFICULTY_SETTINGS,
    DEFAULT_DIFFICULTY,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Game states
# ---------------------------------------------------------------------------

class GameState(Enum):
    """All possible high-level states the game can be in."""
    MENU               = auto()
    CHARACTER_CREATION  = auto()
    OVERWORLD           = auto()
    MINIGAME            = auto()
    LESSON              = auto()
    DIALOG              = auto()
    PAUSED              = auto()
    LOADING             = auto()
    SETTINGS            = auto()


# ---------------------------------------------------------------------------
# Monument unlock requirements (category -> monument id that must clear it)
# The value is the *category string* whose minigames must all be completed.
# ---------------------------------------------------------------------------

_UNLOCK_CHAIN: Dict[int, Optional[str]] = {
    mid: mdata["unlock_requires"] for mid, mdata in MONUMENTS.items()
}

# Reverse lookup: category -> monument id that *teaches* it
_CATEGORY_TO_MONUMENT: Dict[str, int] = {
    mdata["category"]: mid for mid, mdata in MONUMENTS.items()
}


# ---------------------------------------------------------------------------
# Singleton Game Manager
# ---------------------------------------------------------------------------

class GameManager:
    """
    Singleton that holds all mutable game state.

    Access via ``GameManager.instance()`` or simply instantiate — repeated
    calls return the same object.
    """

    _instance: Optional[GameManager] = None

    # ---- Singleton mechanics ------------------------------------------------

    def __new__(cls, *args: Any, **kwargs: Any) -> GameManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def instance(cls) -> GameManager:
        """Return the singleton (creating it if needed)."""
        if cls._instance is None:
            cls()
        return cls._instance  # type: ignore[return-value]

    @classmethod
    def reset(cls) -> None:
        """Destroy the singleton.  Useful in tests."""
        cls._instance = None

    # ---- Initialization -----------------------------------------------------

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        # State machine
        self._current_state: GameState = GameState.MENU
        self._previous_state: Optional[GameState] = None
        self._state_callbacks: Dict[GameState, List[Callable[[], None]]] = {
            state: [] for state in GameState
        }

        # Save data (loaded from disk or freshly created)
        self._save_data: Optional[Dict[str, Any]] = None

        # Session tracking
        self._session_start: float = time.time()
        self._session_paused_at: Optional[float] = None
        self._accumulated_pause_time: float = 0.0

    # ---- Properties ---------------------------------------------------------

    @property
    def current_state(self) -> GameState:
        return self._current_state

    @property
    def previous_state(self) -> Optional[GameState]:
        return self._previous_state

    @property
    def current_save_data(self) -> Optional[Dict[str, Any]]:
        return self._save_data

    @property
    def player_progress(self) -> Dict[str, Any]:
        """Convenience accessor for key progress fields from save data."""
        if self._save_data is None:
            return {}
        return {
            "current_monument":    self._save_data.get("current_monument", 0),
            "completed_lessons":   list(self._save_data.get("completed_lessons", [])),
            "completed_minigames": list(self._save_data.get("completed_minigames", [])),
            "mastered_characters": self._save_data.get("mastered_characters", {}),
            "vocabulary_learned":  list(self._save_data.get("vocabulary_learned", [])),
            "grammar_learned":     list(self._save_data.get("grammar_learned", [])),
            "difficulty":          self._save_data.get("difficulty", DEFAULT_DIFFICULTY),
        }

    @property
    def current_monument(self) -> int:
        if self._save_data is None:
            return 0
        return self._save_data.get("current_monument", 0)

    @current_monument.setter
    def current_monument(self, value: int) -> None:
        if self._save_data is not None:
            self._save_data["current_monument"] = value

    @property
    def difficulty(self) -> str:
        if self._save_data is None:
            return DEFAULT_DIFFICULTY
        return self._save_data.get("difficulty", DEFAULT_DIFFICULTY)

    @property
    def difficulty_settings(self) -> Dict[str, Any]:
        return DIFFICULTY_SETTINGS.get(self.difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])

    # ---- State transitions --------------------------------------------------

    def transition_to(self, new_state: GameState) -> None:
        """
        Transition to a new game state, firing all registered callbacks.

        Parameters
        ----------
        new_state : GameState
            The state to enter.
        """
        if new_state == self._current_state:
            logger.debug("Already in state %s — no transition.", new_state.name)
            return

        old_state = self._current_state
        logger.info("State transition: %s -> %s", old_state.name, new_state.name)

        # Handle pause timing
        if new_state == GameState.PAUSED:
            self._session_paused_at = time.time()
        elif old_state == GameState.PAUSED and self._session_paused_at is not None:
            self._accumulated_pause_time += time.time() - self._session_paused_at
            self._session_paused_at = None

        self._previous_state = old_state
        self._current_state = new_state

        # Fire callbacks
        for callback in self._state_callbacks.get(new_state, []):
            try:
                callback()
            except Exception as exc:
                logger.error("Callback error on entering %s: %s", new_state.name, exc)

    def on_state_enter(self, state: GameState, callback: Callable[[], None]) -> None:
        """Register *callback* to run whenever the game enters *state*."""
        self._state_callbacks[state].append(callback)

    def remove_state_callback(self, state: GameState, callback: Callable[[], None]) -> None:
        """Unregister a previously registered callback."""
        try:
            self._state_callbacks[state].remove(callback)
        except ValueError:
            pass

    def return_to_previous_state(self) -> None:
        """Convenience: go back to whatever state we were in before."""
        if self._previous_state is not None:
            self.transition_to(self._previous_state)

    # ---- Save data management -----------------------------------------------

    def load_save_data(self, data: Dict[str, Any]) -> None:
        """
        Inject save data into the manager (usually right after loading from disk).

        Parameters
        ----------
        data : dict
            A full save-data dictionary (see ``save_system._default_save_data``).
        """
        self._save_data = data
        self._session_start = time.time()
        self._accumulated_pause_time = 0.0
        logger.info("Save data loaded for player '%s'.", data.get("player_name", "???"))

    def clear_save_data(self) -> None:
        """Unload the current save data (e.g. returning to main menu)."""
        self._save_data = None

    def get_session_play_time(self) -> float:
        """Return seconds played in the *current session* (pauses excluded)."""
        elapsed = time.time() - self._session_start - self._accumulated_pause_time
        if self._session_paused_at is not None:
            elapsed -= time.time() - self._session_paused_at
        return max(0.0, elapsed)

    def get_total_play_time(self) -> float:
        """
        Return total play time including all previous sessions plus the
        current one (in seconds).
        """
        saved = 0.0
        if self._save_data is not None:
            saved = self._save_data.get("total_play_time", 0.0)
        return saved + self.get_session_play_time()

    def update_play_time_in_save(self) -> None:
        """Flush current session time into ``_save_data['total_play_time']``."""
        if self._save_data is not None:
            self._save_data["total_play_time"] = self.get_total_play_time()
            # Reset session accounting so we don't double-count
            self._session_start = time.time()
            self._accumulated_pause_time = 0.0

    # ---- Monument / progression queries -------------------------------------

    def is_monument_unlocked(self, monument_id: int) -> bool:
        """
        Determine whether the player has earned access to a monument.

        Monument 0 is always unlocked.  Every other monument requires that
        all minigames of the *previous* monument's category have been completed.

        Parameters
        ----------
        monument_id : int
            The monument index (0-based).

        Returns
        -------
        bool
        """
        if monument_id < 0 or monument_id >= TOTAL_MONUMENTS:
            return False
        if monument_id == 0:
            return True
        if self._save_data is None:
            return False

        required_category = _UNLOCK_CHAIN.get(monument_id)
        if required_category is None:
            return True  # No prerequisite defined — treat as unlocked

        completed: List[str] = self._save_data.get("completed_minigames", [])
        return self._category_minigames_complete(required_category, completed)

    def get_unlocked_monuments(self) -> List[int]:
        """Return a sorted list of all currently unlocked monument ids."""
        return [mid for mid in range(TOTAL_MONUMENTS) if self.is_monument_unlocked(mid)]

    def get_highest_unlocked_monument(self) -> int:
        """Return the id of the highest unlocked monument."""
        unlocked = self.get_unlocked_monuments()
        return unlocked[-1] if unlocked else 0

    def _category_minigames_complete(self, category: str, completed: List[str]) -> bool:
        """
        Check if all minigames for *category* are present in *completed*.

        Convention: minigame ids are prefixed with ``"<category>_"`` and end
        with ``"_minigame_<n>"``.  We consider a category complete when at
        least one minigame whose id starts with ``<category>_`` exists in
        *completed*.

        For early development (before concrete minigame ids are defined), we
        simply check that any id starting with the category prefix has been
        completed.  This keeps the unlock system functional while content is
        still being authored.
        """
        prefix = f"{category}_"
        return any(mg_id.startswith(prefix) for mg_id in completed)

    # ---- Record progress helpers --------------------------------------------

    def complete_lesson(self, lesson_id: str) -> None:
        """Mark a lesson as completed (idempotent)."""
        if self._save_data is None:
            return
        lessons: List[str] = self._save_data.setdefault("completed_lessons", [])
        if lesson_id not in lessons:
            lessons.append(lesson_id)
            logger.info("Lesson completed: %s", lesson_id)

    def complete_minigame(self, minigame_id: str) -> None:
        """Mark a minigame as completed (idempotent)."""
        if self._save_data is None:
            return
        minigames: List[str] = self._save_data.setdefault("completed_minigames", [])
        if minigame_id not in minigames:
            minigames.append(minigame_id)
            logger.info("Minigame completed: %s", minigame_id)

    def learn_vocabulary(self, word: str) -> None:
        """Add a word to the learned vocabulary list (idempotent)."""
        if self._save_data is None:
            return
        vocab: List[str] = self._save_data.setdefault("vocabulary_learned", [])
        if word not in vocab:
            vocab.append(word)

    def learn_grammar(self, grammar_point: str) -> None:
        """Add a grammar point to the learned list (idempotent)."""
        if self._save_data is None:
            return
        grammar: List[str] = self._save_data.setdefault("grammar_learned", [])
        if grammar_point not in grammar:
            grammar.append(grammar_point)

    # ---- Mastery stats ------------------------------------------------------

    def get_mastery_percentages(self) -> Dict[str, float]:
        """
        Return mastery percentages for hiragana, katakana, and kanji.

        "Mastered" means a character has reached the ``mastered`` SRS stage
        (see ``progression.py``).

        Returns
        -------
        dict
            ``{"hiragana": 0-100, "katakana": 0-100, "kanji": 0-100}``
        """
        # Total character counts for reference
        totals = {
            "hiragana": 46,   # Basic hiragana
            "katakana": 46,   # Basic katakana
            "kanji":    200,  # Rough total taught across all kanji monuments
        }

        result: Dict[str, float] = {}
        mc = {}
        if self._save_data is not None:
            mc = self._save_data.get("mastered_characters", {})

        for script, total in totals.items():
            chars = mc.get(script, {})
            mastered_count = sum(
                1 for info in chars.values()
                if isinstance(info, dict) and info.get("stage") == "mastered"
            )
            result[script] = round(mastered_count / total * 100, 1) if total else 0.0

        return result

    def get_monument_completion(self, monument_id: int) -> float:
        """
        Calculate the completion percentage for a specific monument.

        Completion is measured as the ratio of completed lessons and
        minigames whose ids are prefixed with the monument's category.

        Returns
        -------
        float
            0.0 – 100.0
        """
        if monument_id not in MONUMENTS or self._save_data is None:
            return 0.0

        category = MONUMENTS[monument_id]["category"]
        prefix = f"{category}_"

        completed_lessons = [
            lid for lid in self._save_data.get("completed_lessons", [])
            if lid.startswith(prefix)
        ]
        completed_minigames = [
            mid for mid in self._save_data.get("completed_minigames", [])
            if mid.startswith(prefix)
        ]

        total_completed = len(completed_lessons) + len(completed_minigames)

        # Until content is fully authored, estimate expected content per monument
        # as 5 lessons + 3 minigames = 8 items.  This keeps the bar meaningful
        # during development and is easily overridden later.
        expected_items = 8
        return min(100.0, round(total_completed / expected_items * 100, 1))

    def get_overall_completion(self) -> float:
        """
        Average completion percentage across all monuments.
        """
        if self._save_data is None:
            return 0.0
        percentages = [self.get_monument_completion(mid) for mid in range(TOTAL_MONUMENTS)]
        return round(sum(percentages) / len(percentages), 1) if percentages else 0.0

    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Aggregate statistics suitable for a player dashboard.

        Returns
        -------
        dict
            Includes mastery percentages, counts, completion, and play time.
        """
        mastery = self.get_mastery_percentages()

        vocab_count = 0
        grammar_count = 0
        lessons_count = 0
        minigames_count = 0

        if self._save_data is not None:
            vocab_count = len(self._save_data.get("vocabulary_learned", []))
            grammar_count = len(self._save_data.get("grammar_learned", []))
            lessons_count = len(self._save_data.get("completed_lessons", []))
            minigames_count = len(self._save_data.get("completed_minigames", []))

        return {
            "mastery":              mastery,
            "vocabulary_count":     vocab_count,
            "grammar_count":        grammar_count,
            "lessons_completed":    lessons_count,
            "minigames_completed":  minigames_count,
            "overall_completion":   self.get_overall_completion(),
            "total_play_time":      self.get_total_play_time(),
            "current_monument":     self.current_monument,
            "highest_unlocked":     self.get_highest_unlocked_monument(),
            "difficulty":           self.difficulty,
        }
