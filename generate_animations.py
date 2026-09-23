"""从透明角色姿势生成 14 组、每组 60 帧的局部形变动画。

动画采用 4 个关键相位（0/15/30/45）之间的连续补间。形变作用于
角色身体的不同高度区域，而不是移动整个窗口或抖动整幅贴图。
"""
import math
from pathlib import Path

from PIL import Image

from state_machine import PetState, STATE_ASSETS

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "assets_processed"
OUTPUT = ROOT / "animations"
FRAME_COUNT = 60
FRAME_SIZE = 256

# head_x, head_y, torso_x, torso_y, feet_x, feet_y, lean
PROFILES = {
    PetState.STANDARD: (1.0, 1.2, 1.3, 1.8, 0.4, 0.3, 0.2),
    PetState.SIT: (1.0, 2.2, 0.7, 1.0, 0.2, 0.2, 0.6),
    PetState.WAVE: (2.4, 1.0, 1.8, 1.0, 0.2, 0.2, 1.0),
    PetState.EAT: (0.8, 3.0, 1.0, 1.4, 0.2, 0.2, 0.5),
    PetState.ROLL: (3.0, 2.0, 3.0, 2.0, 2.0, 1.0, 4.0),
    PetState.SLEEPY: (2.0, 3.8, 0.8, 1.0, 0.2, 0.2, 2.0),
    PetState.CRY: (2.4, 2.4, 2.8, 1.8, 0.3, 0.3, 1.4),
    PetState.ANGRY: (1.5, 1.0, 2.5, 1.4, 3.6, 2.8, 1.2),
    PetState.HAPPY: (2.2, 2.8, 2.4, 3.2, 2.0, 2.2, 1.4),
    PetState.JOG: (2.0, 2.0, 3.2, 2.8, 5.0, 3.8, 2.4),
    PetState.RUN: (3.0, 2.6, 4.5, 3.5, 7.0, 5.0, 4.0),
    PetState.JUMP: (1.4, 3.0, 2.0, 5.0, 3.0, 6.0, 1.0),
    PetState.CLIMB_DOWN: (1.0, 1.0, 2.8, 2.4, 5.0, 4.5, 1.2),
    PetState.COVER_MOUTH: (1.0, 1.4, 1.5, 1.0, 0.2, 0.2, 0.5),
}


def _displacement(state: PetState, x: float, y: float, phase: float):
    hx, hy, tx, ty, fx, fy, lean = PROFILES[state]
    wave = math.sin(phase)
    alternate = math.sin(phase * 2)
    if y < 0.38:
        dx = hx * wave + lean * (0.38 - y) * wave
        dy = hy * math.cos(phase)
    elif y < 0.76:
        dx = tx * wave * (1 if x < 0.5 else -0.75)
        dy = ty * alternate
    else:
        dx = fx * alternate * (1 if x < 0.5 else -1)
        dy = fy * math.sin(phase + (0 if x < 0.5 else math.pi))
    if state == PetState.JUMP:
        dy -= abs(wave) * 4
    elif state == PetState.CLIMB_DOWN:
        dy += (phase / math.tau) * 3
    return dx, dy


def _warp(image: Image.Image, state: PetState, frame: int) -> Image.Image:
    phase = frame / FRAME_COUNT * math.tau
    grid = 8
    step = FRAME_SIZE // grid
    points = {}
    for gy in range(grid + 1):
        for gx in range(grid + 1):
            x, y = gx * step, gy * step
            dx, dy = _displacement(state, gx / grid, gy / grid, phase)
            points[gx, gy] = (x - dx, y - dy)
    mesh = []
    for gy in range(grid):
        for gx in range(grid):
            left, top = gx * step, gy * step
            right = FRAME_SIZE if gx == grid - 1 else (gx + 1) * step
            bottom = FRAME_SIZE if gy == grid - 1 else (gy + 1) * step
            quad = (
                # Pillow QUAD 顺序：左上、左下、右下、右上。
                *points[gx, gy], *points[gx, gy + 1],
                *points[gx + 1, gy + 1], *points[gx + 1, gy],
            )
            mesh.append(((left, top, right, bottom), quad))
    return image.transform(image.size, Image.Transform.MESH, mesh,
                           Image.Resampling.BICUBIC)


def _prepare(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    image.thumbnail((FRAME_SIZE - 8, FRAME_SIZE - 8), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE))
    canvas.alpha_composite(image, ((FRAME_SIZE - image.width) // 2,
                                   (FRAME_SIZE - image.height) // 2))
    return canvas


def main():
    for state in PetState:
        base = _prepare(SOURCE / STATE_ASSETS[state])
        target = OUTPUT / state.value
        target.mkdir(parents=True, exist_ok=True)
        print(f"生成 {state.value}: {FRAME_COUNT} 帧")
        for frame in range(FRAME_COUNT):
            _warp(base, state, frame).save(
                target / f"frame_{frame:03d}.png", optimize=True
            )
    print(f"动画生成完成：{OUTPUT}")


if __name__ == "__main__":
    main()
