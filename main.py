"""
Nihongo Quest - Main Entry Point
==================================
A 3D Japanese learning adventure game.

This module creates the Ursina application, initializes all systems,
and wires screen transitions together.

Usage:
    python main.py
"""

import sys
import os
import logging
import time

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so imports like
# "from nihongo_quest.core.save_system import ..." work regardless of cwd.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_PROJECT_ROOT)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Configuration & core imports (pure Python — no GPU needed yet)
# ---------------------------------------------------------------------------
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, GAME_VERSION,
    FULLSCREEN_DEFAULT, FPS_CAP, VSYNC,
    SAVE_BASE_DIR, LOG_DIR, MAX_SAVE_SLOTS, MONUMENTS,
)
from core.save_system import (
    save_game, load_game, delete_save, get_all_saves,
    does_save_exist, create_new_save,
)
from core.game_manager import GameManager, GameState
from core.progression import ProgressionTracker

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "nihongo_quest.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("nihongo_quest")
logger.info("=" * 60)
logger.info(f"  Nihongo Quest {GAME_VERSION} starting")
logger.info("=" * 60)

# ---------------------------------------------------------------------------
# Ursina application init
# ---------------------------------------------------------------------------
from ursina import *

app = Ursina(
    title=WINDOW_TITLE,
    borderless=False,
    fullscreen=FULLSCREEN_DEFAULT,
    development_mode=False,
    size=(WINDOW_WIDTH, WINDOW_HEIGHT),
    vsync=VSYNC,
)
window.fps_counter.enabled = False
window.exit_button.enabled = False

# ---------------------------------------------------------------------------
# Import screens & UI (these need Ursina to be initialized)
# ---------------------------------------------------------------------------
from screens.main_menu import MainMenu
from screens.save_select import SaveSelectScreen
from screens.character_creation import CharacterCreation
from screens.settings_screen import SettingsScreen
from screens.lesson_select import LessonSelectScreen
from ui.hud import HUD
from ui.dialog_box import DialogBox
from ui.components import BG_DARK, TransitionScreen

# Overworld and entities — imported with fallback in case agent hasn't finished
try:
    from screens.overworld import Overworld
    HAS_OVERWORLD = True
except ImportError:
    HAS_OVERWORLD = False
    logger.warning("Overworld module not found — using placeholder")

# ═══════════════════════════════════════════════════════════════════════════════
#  NihongoQuestApp — master controller
# ═══════════════════════════════════════════════════════════════════════════════

class NihongoQuestApp:
    """
    Top-level application controller.

    Owns all screen instances and manages transitions between them.
    Delegates game-state logic to GameManager and save/load to save_system.
    """

    def __init__(self):
        # ── Game manager (singleton) ──────────────────────────────────────
        self.gm = GameManager.instance()
        self.current_save_data = None
        self.current_slot = None
        self.progression = None

        # ── Background ────────────────────────────────────────────────────
        window.color = BG_DARK

        # ── Global transition overlay ─────────────────────────────────────
        self.transition = TransitionScreen(parent=camera.ui)
        self.transition.z = -10  # In front of everything

        # ── Instantiate all screens (hidden by default) ───────────────────
        self.main_menu = MainMenu(
            on_new_game=self._on_new_game,
            on_continue=self._on_continue,
            on_load_game=self._on_load_game,
            on_settings=self._on_settings_from_menu,
            on_quit=self._on_quit,
        )

        self.save_select = SaveSelectScreen(
            on_load=self._on_load_slot,
            on_new_game=self._on_new_game_slot,
            on_delete=self._on_delete_slot,
            on_back=self._on_back_to_menu,
        )

        self.character_creation = CharacterCreation()

        self.settings_screen = SettingsScreen(
            on_back=self._on_back_to_menu,
        )

        self.lesson_select = None  # Created dynamically when entering a monument
        self.hud = HUD()
        self.dialog = DialogBox()

        self.overworld = None  # Created when entering overworld

        # ── Hide everything initially ─────────────────────────────────────
        self._hide_all_screens()

        # ── Show main menu ────────────────────────────────────────────────
        self._show_main_menu()

        logger.info("NihongoQuestApp initialized")

    # ═══════════════════════════════════════════════════════════════════════
    #  Screen management helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _hide_all_screens(self):
        """Hide every screen. Called before showing a new one."""
        self.main_menu.enabled = False
        for child in getattr(self.main_menu, '_children_entities', []):
            child.enabled = False
        self.save_select.hide() if hasattr(self.save_select, 'hide') else None
        self.character_creation.hide() if hasattr(self.character_creation, 'hide') else None
        self.settings_screen.hide() if hasattr(self.settings_screen, 'hide') else None
        self.hud.hide() if hasattr(self.hud, 'hide') else None
        self.dialog.hide() if hasattr(self.dialog, 'hide') else None
        if self.overworld and hasattr(self.overworld, 'hide'):
            self.overworld.hide()
        if self.lesson_select and hasattr(self.lesson_select, 'hide'):
            self.lesson_select.hide()

    def _show_main_menu(self):
        """Transition to the main menu."""
        self._hide_all_screens()
        self.gm.transition_to(GameState.MENU)
        self.main_menu.show()
        logger.info("Showing main menu")

    # ═══════════════════════════════════════════════════════════════════════
    #  Main Menu callbacks
    # ═══════════════════════════════════════════════════════════════════════

    def _on_new_game(self):
        """New Game clicked — find first empty slot, open character creation."""
        logger.info("New Game requested")
        saves = get_all_saves()
        # Find first empty slot
        slot = None
        for i in range(1, MAX_SAVE_SLOTS + 1):
            if saves.get(i) is None:
                slot = i
                break
        if slot is None:
            # All slots full — go to save select so user can delete one
            self._on_load_game()
            return
        self._start_character_creation(slot)

    def _on_continue(self):
        """Continue clicked — load most recent save."""
        logger.info("Continue requested")
        saves = get_all_saves()
        # Find most recently played save
        best_slot = None
        best_time = ""
        for slot_num, data in saves.items():
            if data is not None:
                lp = data.get("last_played", "") or ""
                if lp > best_time:
                    best_time = lp
                    best_slot = slot_num
        if best_slot is not None:
            self._load_and_enter_overworld(best_slot)
        else:
            # No saves exist — start new game
            self._on_new_game()

    def _on_load_game(self):
        """Load Game clicked — show save select screen."""
        logger.info("Load Game requested")
        self._hide_all_screens()
        self.gm.transition_to(GameState.LOADING)
        saves = get_all_saves()
        save_list = [saves.get(i) for i in range(1, MAX_SAVE_SLOTS + 1)]
        self.save_select.refresh_slots(save_list) if hasattr(self.save_select, 'refresh_slots') else None
        self.save_select.show()

    def _on_settings_from_menu(self):
        """Settings clicked from main menu."""
        logger.info("Settings requested from menu")
        self._hide_all_screens()
        self.gm.transition_to(GameState.SETTINGS)
        self.settings_screen.show()

    def _on_quit(self):
        """Quit clicked."""
        logger.info("Quit requested")
        if self.current_save_data and self.current_slot:
            save_game(self.current_slot, self.current_save_data)
        application.quit()

    # ═══════════════════════════════════════════════════════════════════════
    #  Save Select callbacks
    # ═══════════════════════════════════════════════════════════════════════

    def _on_load_slot(self, slot_index, data=None):
        """User selected an existing save to load.
        slot_index is 0-based from SaveSelectScreen; convert to 1-based."""
        slot = slot_index + 1
        logger.info(f"Loading save slot {slot}")
        self._load_and_enter_overworld(slot)

    def _on_new_game_slot(self, slot_index):
        """User clicked an empty slot — create new game in that slot.
        slot_index is 0-based from SaveSelectScreen; convert to 1-based."""
        slot = slot_index + 1
        logger.info(f"New game in slot {slot}")
        self._start_character_creation(slot)

    def _on_delete_slot(self, slot_index):
        """User confirmed deletion of a save slot.
        slot_index is 0-based from SaveSelectScreen; convert to 1-based."""
        slot = slot_index + 1
        logger.info(f"Deleting save slot {slot}")
        delete_save(slot)
        # Refresh the save select screen
        saves = get_all_saves()
        save_list = [saves.get(i) for i in range(1, MAX_SAVE_SLOTS + 1)]
        self.save_select.refresh_slots(save_list) if hasattr(self.save_select, 'refresh_slots') else None

    def _on_back_to_menu(self):
        """Back button from any sub-screen — return to main menu."""
        self._show_main_menu()

    # ═══════════════════════════════════════════════════════════════════════
    #  Character Creation
    # ═══════════════════════════════════════════════════════════════════════

    def _start_character_creation(self, slot):
        """Open the character creation screen for a given save slot."""
        self._hide_all_screens()
        self.gm.transition_to(GameState.CHARACTER_CREATION)
        self.current_slot = slot

        # Wire up the character creation's start button
        self.character_creation.show(slot)

        # Override the on_start callback to capture character data
        original_start = getattr(self.character_creation, '_on_start_adventure', None)

        def _on_creation_complete():
            char_data = self.character_creation.get_character_data()
            player_name = char_data.get('name', 'Player') or 'Player'
            appearance = {
                'skin_tone': char_data.get('skin_tone', 0),
                'hair_style': char_data.get('hair_style', 0),
                'hair_color': char_data.get('hair_color', 'Black'),
                'eye_color': char_data.get('eye_color', 'Brown'),
                'outfit_color': char_data.get('outfit_color', 'Red'),
            }
            logger.info(f"Character created: {player_name} in slot {slot}")

            # Create the save file
            create_new_save(slot, player_name, appearance, 'normal')
            self._load_and_enter_overworld(slot)

        # Attach our callback
        self.character_creation.on_start = _on_creation_complete

        logger.info(f"Character creation started for slot {slot}")

    # ═══════════════════════════════════════════════════════════════════════
    #  Overworld
    # ═══════════════════════════════════════════════════════════════════════

    def _load_and_enter_overworld(self, slot):
        """Load a save file and enter the overworld."""
        self._hide_all_screens()

        # Load save data
        self.current_save_data = load_game(slot)
        if self.current_save_data is None:
            logger.error(f"Failed to load save slot {slot}")
            self._show_main_menu()
            return

        self.current_slot = slot
        self.gm.load_save_data(self.current_save_data)
        self.gm.transition_to(GameState.OVERWORLD)

        # Create progression tracker
        self.progression = ProgressionTracker(self.current_save_data)

        # Show HUD
        self.hud.show()
        self.hud.update_stats(self.current_save_data)

        # Create and show overworld
        if HAS_OVERWORLD:
            try:
                if self.overworld:
                    self.overworld.hide()
                self.overworld = Overworld(
                    on_enter_monument=self._on_enter_monument,
                )
                self.overworld.show(self.current_save_data)
            except Exception as e:
                logger.error(f"Overworld creation failed: {e}")
                self._show_overworld_fallback()
        else:
            self._show_overworld_fallback()

        # Show welcome dialog for new games
        if self.current_save_data.get('total_play_time', 0) < 1.0:
            player_name = self.current_save_data.get('player_name', 'Player')
            invoke(self._show_welcome_dialog, player_name, delay=0.5)

        logger.info(f"Entered overworld — slot {slot}, monument {self.current_save_data.get('current_monument', 0)}")

    def _show_overworld_fallback(self):
        """Simple fallback if overworld module isn't available."""
        logger.info("Using fallback overworld display")

        # Create a simple monument selection UI
        self._fallback_entities = []

        title = Text(
            text="Nihongo Quest - Overworld",
            position=(0, 0.42),
            origin=(0, 0),
            scale=2,
            color=color.rgb(255, 215, 0),
            parent=camera.ui,
        )
        self._fallback_entities.append(title)

        subtitle = Text(
            text="Select a Monument to Begin Learning",
            position=(0, 0.35),
            origin=(0, 0),
            scale=1.2,
            color=color.rgb(200, 200, 200),
            parent=camera.ui,
        )
        self._fallback_entities.append(subtitle)

        # Create monument buttons in a grid
        monuments_per_row = 4
        start_x = -0.45
        start_y = 0.2
        btn_width = 0.22
        btn_height = 0.12
        padding = 0.02

        for mid, mdata in MONUMENTS.items():
            row = mid // monuments_per_row
            col = mid % monuments_per_row
            x = start_x + col * (btn_width + padding)
            y = start_y - row * (btn_height + padding)

            is_unlocked = self.gm.is_monument_unlocked(mid)

            btn_color = color.rgb(139, 0, 0) if is_unlocked else color.rgb(60, 60, 60)
            text_color = color.rgb(255, 215, 0) if is_unlocked else color.rgb(120, 120, 120)

            btn = Button(
                text=f"{mdata['name_jp']}\n{mdata['name']}",
                position=(x, y),
                scale=(btn_width, btn_height),
                color=btn_color,
                text_color=text_color,
                parent=camera.ui,
                origin=(-0.5, 0.5),
            )

            if is_unlocked:
                monument_id = mid  # Capture for closure
                btn.on_click = lambda m=monument_id: self._on_enter_monument(m)
            else:
                btn.tooltip = Tooltip(f"Complete {MONUMENTS.get(mid - 1, {}).get('name', '???')} to unlock")

            self._fallback_entities.append(btn)

        # Back to menu button
        back_btn = Button(
            text="Save & Return to Menu",
            position=(0, -0.42),
            scale=(0.3, 0.06),
            color=color.rgb(80, 80, 80),
            text_color=color.white,
            parent=camera.ui,
        )
        back_btn.on_click = self._save_and_return_to_menu
        self._fallback_entities.append(back_btn)

    def _show_welcome_dialog(self, player_name):
        """Show a welcome dialog for new players."""
        self.dialog.show()
        self.dialog.show_dialog(
            speaker="Sensei",
            text=f"Welcome, {player_name}! I am your guide on this journey "
                 f"to master the Japanese language. Your adventure begins at "
                 f"the Hiragana Temple. Click on it to start learning!",
            portrait_color=color.rgb(200, 200, 220),
        )

    # ═══════════════════════════════════════════════════════════════════════
    #  Monument / Lesson / Minigame flow
    # ═══════════════════════════════════════════════════════════════════════

    def _on_enter_monument(self, monument_id):
        """Called when the player enters a monument."""
        if not self.gm.is_monument_unlocked(monument_id):
            logger.info(f"Monument {monument_id} is locked")
            return

        logger.info(f"Entering monument {monument_id}: {MONUMENTS[monument_id]['name']}")
        self.gm.transition_to(GameState.LESSON)

        # Hide overworld
        if self.overworld and hasattr(self.overworld, 'hide'):
            self.overworld.hide()
        if hasattr(self, '_fallback_entities'):
            for e in self._fallback_entities:
                destroy(e)
            self._fallback_entities = []

        # Show lesson select
        try:
            if self.lesson_select:
                self.lesson_select.hide()
            self.lesson_select = LessonSelectScreen(
                monument_id=monument_id,
                save_data=self.current_save_data,
                on_back=self._on_back_to_overworld,
                on_minigame_complete=self._on_minigame_complete,
            )
            self.lesson_select.show(monument_id, self.current_save_data)
        except Exception as e:
            logger.error(f"Failed to show lesson select: {e}")
            self._on_back_to_overworld()

    def _on_back_to_overworld(self):
        """Return from lesson select to overworld."""
        if self.lesson_select:
            self.lesson_select.hide()
            self.lesson_select = None

        # Auto-save
        if self.current_save_data and self.current_slot:
            save_game(self.current_slot, self.current_save_data)

        self._load_and_enter_overworld(self.current_slot)

    def _on_minigame_complete(self, score, max_score, correct_items, wrong_items):
        """Called when a minigame finishes."""
        logger.info(f"Minigame complete: {score}/{max_score}")

        # Award XP through progression system
        if self.progression:
            if score == max_score:
                self.progression.award_xp('minigame_perfect')
            else:
                self.progression.award_xp('minigame_complete')

            # Update mastery for correct items
            for item in correct_items:
                if isinstance(item, str) and len(item) <= 3:
                    self.progression.record_character_answer('hiragana', item, True)

        # Update HUD
        self.hud.update_stats(self.current_save_data)

        # Show notification
        percentage = int(score / max_score * 100) if max_score > 0 else 0
        self.hud.show_notification(f"Score: {score}/{max_score} ({percentage}%)")

        # Auto-save
        if self.current_save_data and self.current_slot:
            save_game(self.current_slot, self.current_save_data)

    def _save_and_return_to_menu(self):
        """Save current progress and return to main menu."""
        if self.current_save_data and self.current_slot:
            # Update play time
            self.gm.update_play_time_in_save()
            save_game(self.current_slot, self.current_save_data)
            logger.info(f"Game saved to slot {self.current_slot}")

        # Clean up fallback entities
        if hasattr(self, '_fallback_entities'):
            for e in self._fallback_entities:
                destroy(e)
            self._fallback_entities = []

        self.current_save_data = None
        self.current_slot = None
        self._show_main_menu()


# ═══════════════════════════════════════════════════════════════════════════════
#  Global update function
# ═══════════════════════════════════════════════════════════════════════════════

game_app = None


def update():
    """Called every frame by Ursina."""
    if game_app and game_app.character_creation:
        if hasattr(game_app.character_creation, 'update') and game_app.gm.current_state == GameState.CHARACTER_CREATION:
            game_app.character_creation.update()


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logger.info("Starting Nihongo Quest application")

    # Set up scene lighting
    DirectionalLight(parent=Entity(), y=10, z=-10, shadows=False, color=color.white)
    AmbientLight(color=color.rgba(100, 100, 100, 255))

    # Create the master app controller
    game_app = NihongoQuestApp()

    logger.info("Running main loop")
    app.run()
