from ursina import *
import math


class PlayerCharacter(Entity):
    """
    Player character entity for the Nihongo Quest overworld.
    Built from Ursina primitives: head sphere, body cube, arms, legs, hair, eyes.
    Approximately 2 units tall.
    """

    def __init__(self, appearance_data=None, position=(0, 0, 0), **kwargs):
        super().__init__(position=position, **kwargs)

        # Default appearance if none provided
        self._appearance_data = appearance_data or {
            'skin_color': color.rgb(255, 220, 185),
            'hair_color': color.rgb(40, 30, 20),
            'hair_style': 'short',
            'eye_color': color.rgb(60, 40, 20),
            'outfit_color': color.rgb(50, 80, 160),
            'outfit_accent': color.rgb(200, 50, 50),
        }

        # Movement state
        self._target_pos = None
        self._move_speed = 5
        self._is_moving = False

        # Animation state
        self._anim_time = 0.0
        self._bob_speed = 3.0
        self._bob_height = 0.03
        self._walk_bob_speed = 8.0
        self._walk_bob_height = 0.06
        self._arm_swing_angle = 25.0

        # Body part references
        self._parts = {}

        # Build the character
        self._build_character()

    def _build_character(self):
        """Construct the 3D character from primitives."""
        data = self._appearance_data

        skin = data.get('skin_color', color.rgb(255, 220, 185))
        hair_col = data.get('hair_color', color.rgb(40, 30, 20))
        hair_style = data.get('hair_style', 'short')
        eye_col = data.get('eye_color', color.rgb(60, 40, 20))
        outfit_col = data.get('outfit_color', color.rgb(50, 80, 160))
        accent_col = data.get('outfit_accent', color.rgb(200, 50, 50))

        # ── Body (torso) ── centered at y=0.7, size 0.6 wide x 0.7 tall x 0.35 deep
        self._parts['body'] = Entity(
            parent=self,
            model='cube',
            color=outfit_col,
            scale=(0.6, 0.7, 0.35),
            position=(0, 0.7, 0),
        )

        # Outfit accent belt
        self._parts['belt'] = Entity(
            parent=self,
            model='cube',
            color=accent_col,
            scale=(0.62, 0.08, 0.36),
            position=(0, 0.45, 0),
        )

        # ── Head ── sphere on top of body
        self._parts['head'] = Entity(
            parent=self,
            model='sphere',
            color=skin,
            scale=(0.45, 0.45, 0.45),
            position=(0, 1.35, 0),
        )

        # ── Eyes ── two small spheres on face
        self._parts['eye_left'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=eye_col,
            scale=(0.15, 0.15, 0.08),
            position=(-0.2, 0.05, 0.45),
        )
        self._parts['eye_right'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=eye_col,
            scale=(0.15, 0.15, 0.08),
            position=(0.2, 0.05, 0.45),
        )

        # Eye whites (slightly behind pupils)
        self._parts['eye_white_left'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=color.white,
            scale=(0.2, 0.2, 0.06),
            position=(-0.2, 0.05, 0.42),
        )
        self._parts['eye_white_right'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=color.white,
            scale=(0.2, 0.2, 0.06),
            position=(0.2, 0.05, 0.42),
        )

        # ── Hair ── varies by style
        self._build_hair(hair_col, hair_style)

        # ── Arms ── two cubes hanging from shoulders
        self._parts['arm_left'] = Entity(
            parent=self,
            model='cube',
            color=outfit_col,
            scale=(0.18, 0.55, 0.18),
            position=(-0.4, 0.72, 0),
            origin_y=0.5,
        )
        # Hand
        self._parts['hand_left'] = Entity(
            parent=self._parts['arm_left'],
            model='sphere',
            color=skin,
            scale=(0.6, 0.3, 0.6),
            position=(0, -0.55, 0),
        )

        self._parts['arm_right'] = Entity(
            parent=self,
            model='cube',
            color=outfit_col,
            scale=(0.18, 0.55, 0.18),
            position=(0.4, 0.72, 0),
            origin_y=0.5,
        )
        self._parts['hand_right'] = Entity(
            parent=self._parts['arm_right'],
            model='sphere',
            color=skin,
            scale=(0.6, 0.3, 0.6),
            position=(0, -0.55, 0),
        )

        # ── Legs ── two cubes below body
        self._parts['leg_left'] = Entity(
            parent=self,
            model='cube',
            color=color.rgb(40, 40, 60),
            scale=(0.22, 0.5, 0.22),
            position=(-0.15, 0.25, 0),
            origin_y=0.5,
        )
        # Foot
        self._parts['foot_left'] = Entity(
            parent=self._parts['leg_left'],
            model='cube',
            color=color.rgb(80, 50, 30),
            scale=(0.8, 0.25, 1.2),
            position=(0, -0.55, 0.05),
        )

        self._parts['leg_right'] = Entity(
            parent=self,
            model='cube',
            color=color.rgb(40, 40, 60),
            scale=(0.22, 0.5, 0.22),
            position=(0.15, 0.25, 0),
            origin_y=0.5,
        )
        self._parts['foot_right'] = Entity(
            parent=self._parts['leg_right'],
            model='cube',
            color=color.rgb(80, 50, 30),
            scale=(0.8, 0.25, 1.2),
            position=(0, -0.55, 0.05),
        )

    def _build_hair(self, hair_col, hair_style):
        """Build hair geometry based on style."""
        # Remove old hair if it exists
        for key in list(self._parts.keys()):
            if key.startswith('hair'):
                destroy(self._parts[key])
                del self._parts[key]

        head = self._parts['head']

        if hair_style == 'short':
            self._parts['hair_top'] = Entity(
                parent=head,
                model='sphere',
                color=hair_col,
                scale=(1.08, 0.6, 1.05),
                position=(0, 0.3, -0.05),
            )
        elif hair_style == 'long':
            self._parts['hair_top'] = Entity(
                parent=head,
                model='sphere',
                color=hair_col,
                scale=(1.1, 0.6, 1.1),
                position=(0, 0.3, -0.05),
            )
            self._parts['hair_back'] = Entity(
                parent=head,
                model='cube',
                color=hair_col,
                scale=(0.85, 1.6, 0.4),
                position=(0, -0.3, -0.35),
            )
        elif hair_style == 'spiky':
            self._parts['hair_top'] = Entity(
                parent=head,
                model='sphere',
                color=hair_col,
                scale=(1.15, 0.75, 1.1),
                position=(0, 0.35, -0.05),
            )
            # Spikes
            for i, angle in enumerate(range(0, 360, 45)):
                rad = math.radians(angle)
                self._parts[f'hair_spike_{i}'] = Entity(
                    parent=head,
                    model='cube',
                    color=hair_col,
                    scale=(0.12, 0.3, 0.12),
                    position=(
                        math.sin(rad) * 0.35,
                        0.55,
                        math.cos(rad) * 0.35,
                    ),
                    rotation=(0, 0, -math.degrees(math.atan2(math.sin(rad), 1)) * 0.5),
                )
        elif hair_style == 'ponytail':
            self._parts['hair_top'] = Entity(
                parent=head,
                model='sphere',
                color=hair_col,
                scale=(1.08, 0.55, 1.05),
                position=(0, 0.3, -0.05),
            )
            self._parts['hair_tie'] = Entity(
                parent=head,
                model='sphere',
                color=color.rgb(200, 50, 50),
                scale=(0.2, 0.2, 0.2),
                position=(0, 0.15, -0.5),
            )
            self._parts['hair_tail'] = Entity(
                parent=head,
                model='cube',
                color=hair_col,
                scale=(0.25, 1.0, 0.2),
                position=(0, -0.4, -0.5),
            )
        else:
            # Default / bald-ish
            self._parts['hair_top'] = Entity(
                parent=head,
                model='sphere',
                color=hair_col,
                scale=(1.05, 0.4, 1.02),
                position=(0, 0.35, -0.05),
            )

    def move_to(self, target_pos, speed=5):
        """Begin smooth movement toward a target position."""
        if isinstance(target_pos, (list, tuple)):
            self._target_pos = Vec3(*target_pos)
        else:
            self._target_pos = Vec3(target_pos)
        self._move_speed = speed
        self._is_moving = True

        # Face the target direction
        direction = self._target_pos - self.position
        if direction.length() > 0.01:
            angle = math.degrees(math.atan2(direction.x, direction.z))
            self.rotation_y = angle

    def update(self):
        """Handle movement animation and idle/walk animation each frame."""
        self._anim_time += time.dt

        if self._is_moving and self._target_pos is not None:
            self._do_movement()
            self.walk_animation()
        else:
            self.idle_animation()

    def _do_movement(self):
        """Smoothly move toward target using lerp."""
        direction = self._target_pos - self.position
        dist = direction.length()

        if dist < 0.1:
            self.position = self._target_pos
            self._is_moving = False
            self._target_pos = None
            # Reset arm rotations after stopping
            if 'arm_left' in self._parts:
                self._parts['arm_left'].rotation_x = 0
            if 'arm_right' in self._parts:
                self._parts['arm_right'].rotation_x = 0
            if 'leg_left' in self._parts:
                self._parts['leg_left'].rotation_x = 0
            if 'leg_right' in self._parts:
                self._parts['leg_right'].rotation_x = 0
            return

        move_amount = min(self._move_speed * time.dt, dist)
        move_vec = direction.normalized() * move_amount
        self.position += move_vec

    def idle_animation(self):
        """Subtle bobbing when standing still."""
        bob = math.sin(self._anim_time * self._bob_speed) * self._bob_height
        if 'body' in self._parts:
            self._parts['body'].y = 0.7 + bob
        if 'head' in self._parts:
            self._parts['head'].y = 1.35 + bob

    def walk_animation(self):
        """Bobbing + arm/leg swing while moving."""
        t = self._anim_time * self._walk_bob_speed
        bob = abs(math.sin(t)) * self._walk_bob_height

        if 'body' in self._parts:
            self._parts['body'].y = 0.7 + bob
        if 'head' in self._parts:
            self._parts['head'].y = 1.35 + bob

        # Arm swing
        swing = math.sin(t) * self._arm_swing_angle
        if 'arm_left' in self._parts:
            self._parts['arm_left'].rotation_x = swing
        if 'arm_right' in self._parts:
            self._parts['arm_right'].rotation_x = -swing

        # Leg swing (opposite to arms)
        leg_swing = math.sin(t) * 20
        if 'leg_left' in self._parts:
            self._parts['leg_left'].rotation_x = -leg_swing
        if 'leg_right' in self._parts:
            self._parts['leg_right'].rotation_x = leg_swing

    def set_appearance(self, appearance_data):
        """Update all visual parts based on new appearance data."""
        self._appearance_data = appearance_data

        # Destroy all existing parts
        for key in list(self._parts.keys()):
            if self._parts[key] is not None:
                destroy(self._parts[key])
        self._parts.clear()

        # Rebuild
        self._build_character()

    def show(self):
        """Make the character visible."""
        self.enabled = True
        for part in self._parts.values():
            if part is not None:
                part.enabled = True

    def hide(self):
        """Make the character invisible."""
        self.enabled = False
        for part in self._parts.values():
            if part is not None:
                part.enabled = False

    @property
    def is_moving(self):
        return self._is_moving

    def destroy_character(self):
        """Clean up all child entities."""
        for key in list(self._parts.keys()):
            if self._parts[key] is not None:
                destroy(self._parts[key])
        self._parts.clear()
        destroy(self)
