"""
Nihongo Quest - Reusable UI Components
=======================================
Japanese-themed styled components built with the Ursina engine.
Consistent dark-red and gold color palette throughout.
"""

from ursina import *
import math

# ── Global Color Scheme ──────────────────────────────────────────────────────
BG_DARK      = color.rgb(20, 12, 28)
ACCENT_RED   = color.rgb(139, 0, 0)
ACCENT_GOLD  = color.rgb(255, 215, 0)
TEXT_WHITE    = color.rgb(240, 240, 240)
PANEL_BG     = color.rgba(0, 0, 0, 180)

# Derived / secondary palette
ACCENT_RED_LIGHT   = color.rgb(180, 30, 30)
ACCENT_RED_DARK    = color.rgb(100, 0, 0)
ACCENT_GOLD_DIM    = color.rgb(200, 170, 0)
HOVER_GLOW         = color.rgb(255, 235, 120)
TEXT_GREY           = color.rgb(160, 160, 160)
SAKURA_PINK        = color.rgb(255, 183, 197)
PANEL_BG_LIGHT     = color.rgba(30, 18, 40, 200)


# ═══════════════════════════════════════════════════════════════════════════════
#  StyledButton
# ═══════════════════════════════════════════════════════════════════════════════
class StyledButton(Button):
    """
    A polished button with Japanese theming.
    Dark-red background, gold text, hover scale-up and colour lighten.
    """

    def __init__(self, text='Button', position=(0, 0), scale=(.4, .065),
                 on_click=None, parent=camera.ui, font_size=18,
                 enabled=True, **kwargs):

        super().__init__(
            text=text,
            position=position,
            scale=scale,
            color=ACCENT_RED,
            highlight_color=ACCENT_RED_LIGHT,
            pressed_color=ACCENT_RED_DARK,
            text_color=ACCENT_GOLD,
            parent=parent,
            enabled=enabled,
            **kwargs,
        )

        self.text_entity.font_size = font_size
        self.on_click_callback = on_click
        self._base_scale = Vec2(*scale)
        self._hover_scale = self._base_scale * 1.05
        self._is_hovered = False

        # Subtle gold bottom-border accent
        self.border_accent = Entity(
            parent=self,
            model='quad',
            color=ACCENT_GOLD,
            scale=(1, 0.04),
            position=(0, -0.48),
            z=-0.01,
        )

    def on_mouse_enter(self):
        self._is_hovered = True
        self.animate_scale(self._hover_scale, duration=0.15, curve=curve.out_expo)
        self.animate_color(ACCENT_RED_LIGHT, duration=0.15)
        self.text_entity.color = HOVER_GLOW

    def on_mouse_exit(self):
        self._is_hovered = False
        self.animate_scale(self._base_scale, duration=0.15, curve=curve.out_expo)
        self.animate_color(ACCENT_RED, duration=0.15)
        self.text_entity.color = ACCENT_GOLD

    def on_click(self):
        if self.on_click_callback:
            self.on_click_callback()


# ═══════════════════════════════════════════════════════════════════════════════
#  StyledPanel
# ═══════════════════════════════════════════════════════════════════════════════
class StyledPanel(Entity):
    """
    Semi-transparent dark panel used as a backdrop for menus / dialogs.
    """

    def __init__(self, position=(0, 0), scale=(.5, .5),
                 panel_color=PANEL_BG, parent=camera.ui, **kwargs):

        super().__init__(
            parent=parent,
            model='quad',
            color=panel_color,
            position=position,
            scale=scale,
            **kwargs,
        )

        # Thin gold border lines (top + bottom)
        self.top_border = Entity(
            parent=self, model='quad', color=ACCENT_GOLD,
            scale=(1, 0.008 / scale[1] if scale[1] else 0.008),
            position=(0, 0.5), z=-0.01,
        )
        self.bottom_border = Entity(
            parent=self, model='quad', color=ACCENT_GOLD,
            scale=(1, 0.008 / scale[1] if scale[1] else 0.008),
            position=(0, -0.5), z=-0.01,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  TitleText
# ═══════════════════════════════════════════════════════════════════════════════
class TitleText(Entity):
    """
    Large title with a shadow layer underneath for a brush-stroke aesthetic.
    """

    def __init__(self, text='Title', position=(0, .35), font_size=60,
                 text_color=ACCENT_GOLD, parent=camera.ui, **kwargs):

        super().__init__(parent=parent, position=position, **kwargs)

        # Shadow (offset dark text behind the main text)
        self.shadow = Text(
            text=text,
            parent=self,
            font_size=font_size,
            color=color.rgba(0, 0, 0, 200),
            origin=(0, 0),
            position=(0.003, -0.003),
            z=0.01,
        )

        # Main text
        self.label = Text(
            text=text,
            parent=self,
            font_size=font_size,
            color=text_color,
            origin=(0, 0),
            position=(0, 0),
        )

    @property
    def text(self):
        return self.label.text

    @text.setter
    def text(self, value):
        self.label.text = value
        self.shadow.text = value


# ═══════════════════════════════════════════════════════════════════════════════
#  InfoText
# ═══════════════════════════════════════════════════════════════════════════════
class InfoText(Text):
    """
    Smaller informational text — used for descriptions, stats, hints, etc.
    """

    def __init__(self, text='', position=(0, 0), font_size=16,
                 text_color=TEXT_WHITE, parent=camera.ui, origin=(0, 0),
                 **kwargs):
        super().__init__(
            text=text,
            position=position,
            font_size=font_size,
            color=text_color,
            parent=parent,
            origin=origin,
            **kwargs,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  ProgressBar
# ═══════════════════════════════════════════════════════════════════════════════
class ProgressBar(Entity):
    """
    Horizontal bar that fills from left to right.
    Gradient appearance from ACCENT_RED (empty) to ACCENT_GOLD (full).
    """

    def __init__(self, position=(0, 0), scale=(.3, .025), value=0.0,
                 show_text=True, parent=camera.ui, **kwargs):

        super().__init__(parent=parent, position=position, **kwargs)

        self.bar_width, self.bar_height = scale

        # Background track
        self.bg = Entity(
            parent=self,
            model='quad',
            color=color.rgba(40, 25, 50, 220),
            scale=(self.bar_width, self.bar_height),
            origin=(-0.5, 0),
            z=0.01,
        )

        # Fill bar
        self.fill = Entity(
            parent=self,
            model='quad',
            color=ACCENT_RED,
            scale=(0, self.bar_height),
            origin=(-0.5, 0),
            z=0,
        )

        # Percentage label
        self.label = None
        if show_text:
            self.label = Text(
                text='0%',
                parent=self,
                font_size=14,
                color=TEXT_WHITE,
                origin=(0, 0),
                position=(self.bar_width / 2, 0),
                z=-0.01,
            )

        self.value = value
        self._update_fill()

    # noinspection PyAttributeOutsideInit
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = max(0.0, min(1.0, v))
        self._update_fill()

    def _update_fill(self):
        t = self._value
        self.fill.scale_x = self.bar_width * t

        # Lerp colour from red -> gold
        r = int(139 + (255 - 139) * t)
        g = int(0 + 215 * t)
        b = 0
        self.fill.color = color.rgb(r, g, b)

        if self.label:
            self.label.text = f'{int(t * 100)}%'

    def animate_value(self, target, duration=0.5):
        """Smoothly animate to a target value (0-1)."""
        self.animate('_value', target, duration=duration, curve=curve.out_expo)
        invoke(self._update_fill, delay=duration)


# ═══════════════════════════════════════════════════════════════════════════════
#  StarRating
# ═══════════════════════════════════════════════════════════════════════════════
class StarRating(Entity):
    """
    Displays 1-5 stars.  Filled stars are gold; empty stars are dim grey.
    Stars are rendered as text characters.
    """

    def __init__(self, rating=0, max_stars=5, position=(0, 0),
                 font_size=24, parent=camera.ui, **kwargs):

        super().__init__(parent=parent, position=position, **kwargs)

        self.max_stars = max_stars
        self._stars = []
        spacing = 0.035

        for i in range(max_stars):
            star = Text(
                text='*',
                parent=self,
                font_size=font_size,
                color=TEXT_GREY,
                origin=(0, 0),
                position=(i * spacing - (max_stars - 1) * spacing / 2, 0),
            )
            self._stars.append(star)

        self.rating = rating

    @property
    def rating(self):
        return self._rating

    @rating.setter
    def rating(self, value):
        self._rating = max(0, min(self.max_stars, value))
        for i, star in enumerate(self._stars):
            star.color = ACCENT_GOLD if i < self._rating else TEXT_GREY


# ═══════════════════════════════════════════════════════════════════════════════
#  ModalDialog
# ═══════════════════════════════════════════════════════════════════════════════
class ModalDialog(Entity):
    """
    Centred popup with title, message body, confirm and cancel buttons.
    Blocks interaction with elements behind it via a full-screen overlay.
    """

    def __init__(self, title='Confirm', message='Are you sure?',
                 confirm_text='Yes', cancel_text='No',
                 on_confirm=None, on_cancel=None,
                 parent=camera.ui, **kwargs):

        super().__init__(parent=parent, **kwargs)

        # Full-screen dim overlay
        self.overlay = Entity(
            parent=self,
            model='quad',
            color=color.rgba(0, 0, 0, 150),
            scale=(2, 2),
            z=0.1,
        )

        # Dialog panel
        self.panel = StyledPanel(
            parent=self,
            scale=(.5, .28),
            panel_color=color.rgba(25, 15, 35, 240),
            z=0,
        )

        # Title
        self.title_text = Text(
            text=title,
            parent=self,
            font_size=26,
            color=ACCENT_GOLD,
            origin=(0, 0),
            position=(0, 0.08),
            z=-0.01,
        )

        # Message body
        self.message_text = Text(
            text=message,
            parent=self,
            font_size=18,
            color=TEXT_WHITE,
            origin=(0, 0),
            position=(0, 0.01),
            z=-0.01,
        )

        # Buttons
        self.confirm_btn = StyledButton(
            text=confirm_text,
            parent=self,
            position=(-0.1, -0.08),
            scale=(.16, .05),
            font_size=16,
            on_click=self._on_confirm,
        )
        self.cancel_btn = StyledButton(
            text=cancel_text,
            parent=self,
            position=(0.1, -0.08),
            scale=(.16, .05),
            font_size=16,
            on_click=self._on_cancel,
        )

        self._on_confirm_cb = on_confirm
        self._on_cancel_cb = on_cancel

    def _on_confirm(self):
        if self._on_confirm_cb:
            self._on_confirm_cb()
        self.dismiss()

    def _on_cancel(self):
        if self._on_cancel_cb:
            self._on_cancel_cb()
        self.dismiss()

    def dismiss(self):
        self.animate('alpha', 0, duration=0.15)
        destroy(self, delay=0.2)


# ═══════════════════════════════════════════════════════════════════════════════
#  TransitionScreen
# ═══════════════════════════════════════════════════════════════════════════════
class TransitionScreen(Entity):
    """
    Full-screen fade-to-black (and back) used when switching between screens.
    Usage:
        t = TransitionScreen()
        t.fade_out(on_complete=my_callback)   # screen goes black
        t.fade_in()                           # screen fades back to clear
    """

    def __init__(self, parent=camera.ui, **kwargs):

        super().__init__(
            parent=parent,
            model='quad',
            color=color.rgba(0, 0, 0, 0),
            scale=(2, 2),
            z=-0.5,          # in front of everything
            **kwargs,
        )
        self.visible = True

    def fade_out(self, duration=0.4, on_complete=None):
        """Fade screen to black."""
        self.z = -0.5
        self.animate_color(color.rgba(0, 0, 0, 255), duration=duration,
                           curve=curve.in_out_expo)
        if on_complete:
            invoke(on_complete, delay=duration)

    def fade_in(self, duration=0.4, on_complete=None):
        """Fade screen from black back to transparent."""
        self.color = color.rgba(0, 0, 0, 255)
        self.z = -0.5
        self.animate_color(color.rgba(0, 0, 0, 0), duration=duration,
                           curve=curve.in_out_expo)
        if on_complete:
            invoke(on_complete, delay=duration)
        invoke(self._send_back, delay=duration)

    def _send_back(self):
        """Move behind everything once fully transparent."""
        self.z = 10
