"""
Nihongo Quest - Save System
============================
Robust JSON-based save/load system with 6 save slots.
Saves are stored in the user's local application data directory.
Handles corruption, missing files, and partial data gracefully.
"""

import json
import os
import shutil
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Use project config for paths and limits
from config import SAVE_DIR, MAX_SAVE_SLOTS, DEFAULT_DIFFICULTY

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default save data template
# ---------------------------------------------------------------------------

def _default_save_data(slot: int) -> Dict[str, Any]:
    """Return a fresh save-data dictionary with all fields at their defaults."""
    return {
        "slot":                 slot,
        "player_name":          "",
        "character_appearance": {
            "body_type":   "average",
            "hair_style":  "short",
            "hair_color":  "black",
            "eye_color":   "brown",
            "skin_tone":   "medium",
            "outfit_style": "casual",
        },
        "current_monument":     0,
        "completed_lessons":    [],
        "completed_minigames":  [],
        "mastered_characters":  {
            "hiragana": {},   # e.g. {"あ": {"stage": "mastered", "consecutive": 5, ...}}
            "katakana": {},
            "kanji":    {},
        },
        "vocabulary_learned":   [],
        "grammar_learned":      [],
        "total_play_time":      0.0,
        "last_played":          None,
        "difficulty":           DEFAULT_DIFFICULTY,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _slot_filename(slot: int) -> str:
    """Return the JSON filename for a given slot number."""
    return f"save_slot_{slot}.json"


def _slot_filepath(slot: int) -> str:
    """Return the full file path for a given slot number."""
    return os.path.join(SAVE_DIR, _slot_filename(slot))


def _backup_filepath(slot: int) -> str:
    """Return the path of the backup file for a slot."""
    return os.path.join(SAVE_DIR, f"save_slot_{slot}.bak.json")


def _validate_slot(slot: int) -> None:
    """Raise ValueError if the slot number is out of range."""
    if not isinstance(slot, int) or slot < 1 or slot > MAX_SAVE_SLOTS:
        raise ValueError(
            f"Invalid save slot {slot!r}. Must be an integer between 1 and {MAX_SAVE_SLOTS}."
        )


def _ensure_save_directory() -> None:
    """Create the save directory tree if it does not already exist."""
    os.makedirs(SAVE_DIR, exist_ok=True)


def _validate_save_data(data: Dict[str, Any], slot: int) -> Dict[str, Any]:
    """
    Validate and repair loaded save data.

    Missing keys are filled in from the default template so that the rest
    of the application never has to deal with KeyError on save-data fields.
    Extra keys are preserved (forward-compatibility).
    """
    template = _default_save_data(slot)

    # Ensure every expected key exists
    for key, default_value in template.items():
        if key not in data:
            logger.warning("Save slot %d missing key '%s' — using default.", slot, key)
            data[key] = default_value

    # Ensure mastered_characters sub-keys exist
    mc = data.get("mastered_characters")
    if not isinstance(mc, dict):
        data["mastered_characters"] = template["mastered_characters"]
    else:
        for sub_key in ("hiragana", "katakana", "kanji"):
            if sub_key not in mc or not isinstance(mc[sub_key], dict):
                mc[sub_key] = {}

    # Ensure list fields are actually lists
    for list_key in ("completed_lessons", "completed_minigames",
                     "vocabulary_learned", "grammar_learned"):
        if not isinstance(data.get(list_key), list):
            data[list_key] = []

    # Ensure numeric fields are numeric
    if not isinstance(data.get("total_play_time"), (int, float)):
        data["total_play_time"] = 0.0
    if not isinstance(data.get("current_monument"), int):
        data["current_monument"] = 0

    # Force the slot field to match the requested slot
    data["slot"] = slot

    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_game(slot: int, data: Dict[str, Any]) -> bool:
    """
    Persist game data to the given save slot.

    Parameters
    ----------
    slot : int
        Slot number (1 through MAX_SAVE_SLOTS).
    data : dict
        Game-state dictionary.  The ``slot`` and ``last_played`` fields
        are set/overwritten automatically.

    Returns
    -------
    bool
        ``True`` if the save succeeded, ``False`` otherwise.
    """
    _validate_slot(slot)
    _ensure_save_directory()

    filepath = _slot_filepath(slot)
    backup = _backup_filepath(slot)

    # Stamp metadata
    data["slot"] = slot
    data["last_played"] = datetime.now(timezone.utc).isoformat()

    # If an existing save is present, create a backup first
    if os.path.isfile(filepath):
        try:
            shutil.copy2(filepath, backup)
        except OSError as exc:
            logger.warning("Could not create backup for slot %d: %s", slot, exc)

    # Write to a temporary file, then atomically rename to avoid half-writes
    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

        # Atomic replace (works on Windows with os.replace since Python 3.3)
        os.replace(tmp_path, filepath)
        logger.info("Game saved to slot %d.", slot)
        return True

    except (OSError, TypeError, ValueError) as exc:
        logger.error("Failed to save slot %d: %s", slot, exc)
        # Clean up the temp file if it lingers
        if os.path.isfile(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False


def load_game(slot: int) -> Optional[Dict[str, Any]]:
    """
    Load game data from the given save slot.

    If the primary save file is corrupted, the system attempts to load
    from the backup file instead.

    Parameters
    ----------
    slot : int
        Slot number (1 through MAX_SAVE_SLOTS).

    Returns
    -------
    dict or None
        The save-data dictionary, or ``None`` if no valid save exists.
    """
    _validate_slot(slot)

    filepath = _slot_filepath(slot)
    backup = _backup_filepath(slot)

    # Try primary, then backup
    for path, label in ((filepath, "primary"), (backup, "backup")):
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError(f"Top-level JSON is {type(data).__name__}, expected dict.")
            data = _validate_save_data(data, slot)
            logger.info("Loaded slot %d from %s file.", slot, label)

            # If we had to fall back to backup, re-save to fix the primary
            if label == "backup":
                logger.warning("Slot %d primary was corrupt — restored from backup.", slot)
                save_game(slot, data)

            return data

        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            logger.warning("Corrupt %s save for slot %d: %s", label, slot, exc)
            continue

    logger.info("No valid save found for slot %d.", slot)
    return None


def delete_save(slot: int) -> bool:
    """
    Delete all save files (primary + backup) for the given slot.

    Parameters
    ----------
    slot : int
        Slot number (1 through MAX_SAVE_SLOTS).

    Returns
    -------
    bool
        ``True`` if at least one file was removed, ``False`` if nothing existed.
    """
    _validate_slot(slot)

    removed_any = False
    for path in (_slot_filepath(slot), _backup_filepath(slot)):
        if os.path.isfile(path):
            try:
                os.remove(path)
                removed_any = True
            except OSError as exc:
                logger.error("Could not delete %s: %s", path, exc)

    if removed_any:
        logger.info("Deleted save slot %d.", slot)
    return removed_any


def does_save_exist(slot: int) -> bool:
    """
    Check whether a save file exists for the given slot.

    Parameters
    ----------
    slot : int
        Slot number (1 through MAX_SAVE_SLOTS).

    Returns
    -------
    bool
    """
    _validate_slot(slot)
    return os.path.isfile(_slot_filepath(slot))


def get_all_saves() -> Dict[int, Optional[Dict[str, Any]]]:
    """
    Return a mapping of every slot number to its save data (or ``None``).

    Returns
    -------
    dict[int, dict | None]
        Keys are slot numbers 1 through MAX_SAVE_SLOTS.
    """
    result: Dict[int, Optional[Dict[str, Any]]] = {}
    for slot in range(1, MAX_SAVE_SLOTS + 1):
        try:
            result[slot] = load_game(slot)
        except Exception as exc:
            logger.error("Unexpected error loading slot %d: %s", slot, exc)
            result[slot] = None
    return result


def create_new_save(slot: int, player_name: str, character_appearance: Dict[str, str],
                    difficulty: str = DEFAULT_DIFFICULTY) -> Dict[str, Any]:
    """
    Convenience: create a brand-new save with initial values and persist it.

    Parameters
    ----------
    slot : int
        Slot number.
    player_name : str
        The player's chosen name.
    character_appearance : dict
        Dict of appearance customization choices.
    difficulty : str
        Difficulty key (``"easy"``, ``"normal"``, ``"hard"``, ``"extreme"``).

    Returns
    -------
    dict
        The newly created save-data dictionary.
    """
    _validate_slot(slot)

    data = _default_save_data(slot)
    data["player_name"] = player_name
    data["character_appearance"] = character_appearance
    data["difficulty"] = difficulty

    save_game(slot, data)
    return data


def get_save_summary(slot: int) -> Optional[Dict[str, Any]]:
    """
    Return a lightweight summary of a save slot for the load-game UI.

    Returns
    -------
    dict or None
        Contains ``slot``, ``player_name``, ``current_monument``,
        ``total_play_time``, ``last_played``, and ``difficulty``.
    """
    data = load_game(slot)
    if data is None:
        return None

    return {
        "slot":             data["slot"],
        "player_name":      data.get("player_name", "???"),
        "current_monument": data.get("current_monument", 0),
        "total_play_time":  data.get("total_play_time", 0.0),
        "last_played":      data.get("last_played"),
        "difficulty":       data.get("difficulty", DEFAULT_DIFFICULTY),
    }
