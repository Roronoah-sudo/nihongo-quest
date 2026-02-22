"""
Nihongo Quest - Save File Selection Screen
============================================
Displays a 2x3 grid of save slots.  Occupied slots show player info;
empty slots invite the player to start a new adventure.
"""

from ursina import *
from datetime import datetime

from ui.components import (
    StyledButton, StyledPanel, TitleText, InfoText, ProgressBar,
    ModalDialog, TransitionScreen,
    BG_DARK, ACCENT_RED, ACCENT_GOLD, TEXT_WHITE, PANEL_BG,
    ACCENT_GOLD_DIM, TEXT_GREY, PANEL_BG_LIGHT,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  SaveSlot (single card in the grid)
# ═══════════════════════════════════════════════════════════════════════════════
class SaveSlotCard(Entity):
    """
    One save-slot card.  Renders differently for occupied vs empty.
    """

    def __init__(self, slot_index, save_data=None,
                 on_click_occupied=None, on_click_empty=None,
                 parent=camera.ui, **kwargs):

        super().__init__(parent=parent, **kwargs)

        self.slot_index = slot_index
        self.save_data = save_data
        self.on_click_occupied = on_click_occupied
        self.on_click_empty = on_click_empty

        self._card_width = 0.34
        self._card_height = 0.19

        # Card background (clickable)
        self.card_bg = Button(
            parent=self,
            model='quad',
            color=color.rgba(30, 18, 42, 230),
            highlight_color=color.rgba(50, 30, 65, 240),
            pressed_color=color.rgba(70, 40, 85, 250),
            scale=(self._card_width, self._card_height),
            on_click=self._handle_click,
        )

        # Gold border (thin top line)
        Entity(
            parent=self.card_bg, model='quad', color=ACCENT_GOLD,
            scale=(1, 0.015), position=(0, 0.5), z=-0.01,
        )

        # Slot number badge (top-left)
        self.slot_badge = Text(
            text=f'Slot {slot_index + 1}',
            parent=self.card_bg,
            font_size=13,
            color=ACCENT_GOLD_DIM,
            origin=(-0.5, 0.5),
            position=(-0.47, 0.44),
            z=-0.01,
        )

        # Content gets built based on save_data
        self._content_entities = []
        self._build_content()

    def _clear_content(self):
        for e in self._content_entities:
            destroy(e)
        self._content_entities.clear()

    def _build_content(self):
        self._clear_content()

        if self.save_data:
            self._build_occupied()
        else:
            self._build_empty()

    def _build_empty(self):
        # Large "+" icon
        plus = Text(
            text='+',
            parent=self.card_bg,
            font_size=36,
            color=TEXT_GREY,
            origin=(0, 0),
            position=(0, 0.05),
            z=-0.01,
        )
        self._content_entities.append(plus)

        label = Text(
            text='Empty Slot',
            parent=self.card_bg,
            font_size=15,
            color=TEXT_GREY,
            origin=(0, 0),
            position=(0, -0.25),
            z=-0.01,
        )
        self._content_entities.append(label)

    def _build_occupied(self):
        d = self.save_data

        # Player name
        name = Text(
            text=d.get('player_name', 'Unknown'),
            parent=self.card_bg,
            font_size=18,
            color=TEXT_WHITE,
            origin=(-0.5, 0.5),
            position=(-0.47, 0.3),
            z=-0.01,
        )
        self._content_entities.append(name)

        # Current monument
        monument = Text(
            text=d.get('monument_name', '---'),
            parent=self.card_bg,
            font_size=13,
            color=ACCENT_GOLD_DIM,
            origin=(-0.5, 0.5),
            position=(-0.47, 0.1),
            z=-0.01,
        )
        self._content_entities.append(monument)

        # Play time
        seconds = d.get('play_time_seconds', 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        playtime_str = f'{hours}h {minutes:02d}m'
        pt = Text(
            text=playtime_str,
            parent=self.card_bg,
            font_size=12,
            color=TEXT_GREY,
            origin=(0.5, 0.5),
            position=(0.47, 0.3),
            z=-0.01,
        )
        self._content_entities.append(pt)

        # Last played date
        last_played = d.get('last_played', '')
        if last_played:
            try:
                dt = datetime.fromisoformat(last_played)
                last_played = dt.strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                pass
        lp = Text(
            text=last_played,
            parent=self.card_bg,
            font_size=11,
            color=TEXT_GREY,
            origin=(0.5, 0.5),
            position=(0.47, 0.1),
            z=-0.01,
        )
        self._content_entities.append(lp)

        # Completion progress bar
        completion = d.get('completion', 0.0)
        bar = ProgressBar(
            parent=self.card_bg,
            position=(0, -0.3),
            scale=(0.8 * self._card_width, 0.03),
            value=completion,
            show_text=True,
        )
        # ProgressBar is an Entity so its position is relative to card_bg's
        # local coords (normalised).  We place it at the bottom.
        bar.position = (0, -0.3)
        self._content_entities.append(bar)

    def _handle_click(self):
        if self.save_data and self.on_click_occupied:
            self.on_click_occupied(self.slot_index, self.save_data)
        elif not self.save_data and self.on_click_empty:
            self.on_click_empty(self.slot_index)

    def refresh(self, save_data):
        self.save_data = save_data
        self._build_content()


# ═══════════════════════════════════════════════════════════════════════════════
#  SaveSelectScreen
# ═══════════════════════════════════════════════════════════════════════════════
class SaveSelectScreen(Entity):
    """
    Screen that shows 6 save slots in a 2-column x 3-row grid.

    Parameters:
        save_data_list : list of 6 items (dict or None per slot)
        on_load        : callback(slot_index, data)  -- load an occupied slot
        on_new_game    : callback(slot_index)         -- create in an empty slot
        on_delete      : callback(slot_index)         -- delete save data
        on_back        : callback()                   -- return to main menu
    """

    NUM_SLOTS = 6
    GRID_COLS = 2
    GRID_ROWS = 3

    def __init__(self, save_data_list=None, on_load=None,
                 on_new_game=None, on_delete=None, on_back=None,
                 **kwargs):
        super().__init__(parent=camera.ui, **kwargs)

        self.save_data_list = save_data_list or [None] * self.NUM_SLOTS
        self.on_load = on_load
        self.on_new_game = on_new_game
        self.on_delete = on_delete
        self.on_back = on_back

        self._active_modal = None
        self._slot_action_panel = None
        self._slot_cards = []
        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # Background
        self.bg = Entity(
            parent=self, model='quad', color=BG_DARK,
            scale=(2, 2), z=1,
        )

        # Title
        self.title = TitleText(
            text='Save Files',
            position=(0, 0.41),
            font_size=36,
            parent=self,
        )

        # Subtitle
        self.subtitle = InfoText(
            text='Select a slot to load or begin a new adventure',
            position=(0, 0.34),
            font_size=14,
            text_color=ACCENT_GOLD_DIM,
            parent=self,
        )

        # Build slot grid
        self._build_grid()

        # Back button
        self.back_btn = StyledButton(
            text='Back',
            position=(0, -0.42),
            scale=(0.2, 0.055),
            on_click=self._handle_back,
            parent=self,
            font_size=16,
        )

        # Transition helper
        self.transition = TransitionScreen(parent=self)
        self.transition.z = -1

    def _build_grid(self):
        """Create 6 slot cards arranged in a 2x3 grid."""
        for card in self._slot_cards:
            destroy(card)
        self._slot_cards.clear()

        col_spacing = 0.38
        row_spacing = 0.22
        start_x = -col_spacing / 2
        start_y = 0.2

        for idx in range(self.NUM_SLOTS):
            col = idx % self.GRID_COLS
            row = idx // self.GRID_COLS
            x = start_x + col * col_spacing
            y = start_y - row * row_spacing

            save_data = self.save_data_list[idx] if idx < len(self.save_data_list) else None

            card = SaveSlotCard(
                slot_index=idx,
                save_data=save_data,
                on_click_occupied=self._on_slot_occupied,
                on_click_empty=self._on_slot_empty,
                parent=self,
                position=(x, y),
            )
            self._slot_cards.append(card)

    # ── Slot Interactions ────────────────────────────────────────────────────
    def _on_slot_occupied(self, slot_index, data):
        """Show Load / Delete / Cancel options for an occupied slot."""
        self._dismiss_slot_action()

        panel = Entity(parent=self, z=-0.2)

        # Dim overlay
        overlay = Entity(
            parent=panel, model='quad',
            color=color.rgba(0, 0, 0, 140), scale=(2, 2), z=0.1,
        )

        # Action panel background
        bg = StyledPanel(
            parent=panel,
            scale=(0.34, 0.22),
            panel_color=color.rgba(25, 15, 35, 245),
            z=0,
        )

        header = Text(
            text=f'Slot {slot_index + 1}: {data.get("player_name", "Unknown")}',
            parent=panel, font_size=18, color=ACCENT_GOLD,
            origin=(0, 0), position=(0, 0.06), z=-0.01,
        )

        load_btn = StyledButton(
            text='Load', parent=panel,
            position=(-0.1, -0.01), scale=(0.12, 0.045), font_size=14,
            on_click=lambda si=slot_index, d=data: self._load_slot(si, d),
        )
        delete_btn = StyledButton(
            text='Delete', parent=panel,
            position=(0.1, -0.01), scale=(0.12, 0.045), font_size=14,
            on_click=lambda si=slot_index: self._confirm_delete(si),
        )
        cancel_btn = StyledButton(
            text='Cancel', parent=panel,
            position=(0, -0.07), scale=(0.12, 0.045), font_size=14,
            on_click=self._dismiss_slot_action,
        )

        self._slot_action_panel = panel

    def _dismiss_slot_action(self):
        if self._slot_action_panel:
            destroy(self._slot_action_panel)
            self._slot_action_panel = None

    def _load_slot(self, slot_index, data):
        self._dismiss_slot_action()
        if self.on_load:
            self.transition.fade_out(
                on_complete=lambda: self.on_load(slot_index, data))

    def _confirm_delete(self, slot_index):
        self._dismiss_slot_action()
        self._active_modal = ModalDialog(
            title='Delete Save?',
            message=f'Permanently delete Slot {slot_index + 1}?',
            confirm_text='Delete',
            cancel_text='Cancel',
            on_confirm=lambda: self._delete_slot(slot_index),
            on_cancel=None,
            parent=self,
        )

    def _delete_slot(self, slot_index):
        self._active_modal = None
        if self.on_delete:
            self.on_delete(slot_index)
        # Clear local data and refresh card
        if slot_index < len(self.save_data_list):
            self.save_data_list[slot_index] = None
        if slot_index < len(self._slot_cards):
            self._slot_cards[slot_index].refresh(None)

    def _on_slot_empty(self, slot_index):
        if self.on_new_game:
            self.transition.fade_out(
                on_complete=lambda: self.on_new_game(slot_index))

    def _handle_back(self):
        if self.on_back:
            self.transition.fade_out(on_complete=self.on_back)

    # ── Public API ───────────────────────────────────────────────────────────
    def refresh_slots(self, save_data_list=None):
        """Reload all slot cards with fresh data."""
        if save_data_list is not None:
            self.save_data_list = save_data_list
        for idx, card in enumerate(self._slot_cards):
            data = self.save_data_list[idx] if idx < len(self.save_data_list) else None
            card.refresh(data)

    def show(self):
        self.enabled = True
        self.transition.fade_in(duration=0.4)

    def hide(self):
        def _do_hide():
            self.enabled = False
        self.transition.fade_out(duration=0.3, on_complete=_do_hide)


# ═══════════════════════════════════════════════════════════════════════════════
#  Stand-alone test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = Ursina(title='Nihongo Quest - Save Select', borderless=False)
    window.color = BG_DARK

    # Example save data
    test_saves = [
        {
            'player_name': 'Sakura',
            'monument_name': 'Fushimi Inari Shrine',
            'play_time_seconds': 7260,
            'last_played': '2026-02-20T14:30:00',
            'completion': 0.35,
        },
        {
            'player_name': 'Tanuki',
            'monument_name': 'Kinkaku-ji Temple',
            'play_time_seconds': 18900,
            'last_played': '2026-02-18T09:15:00',
            'completion': 0.72,
        },
        None,
        {
            'player_name': 'Kitsune',
            'monument_name': 'Tokyo Tower',
            'play_time_seconds': 3600,
            'last_played': '2026-01-05T20:00:00',
            'completion': 0.12,
        },
        None,
        None,
    ]

    screen = SaveSelectScreen(
        save_data_list=test_saves,
        on_load=lambda i, d: print(f'Load slot {i}: {d["player_name"]}'),
        on_new_game=lambda i: print(f'New game in slot {i}'),
        on_delete=lambda i: print(f'Deleted slot {i}'),
        on_back=lambda: print('Back to main menu'),
    )
    screen.show()

    app.run()
