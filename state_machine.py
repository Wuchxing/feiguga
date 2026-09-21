from enum import Enum


class PetState(str, Enum):
    STANDARD = "standard"
    SIT = "sit"
    WAVE = "wave"
    EAT = "eat"
    ROLL = "roll"
    SLEEPY = "sleepy"
    CRY = "cry"
    ANGRY = "angry"
    HAPPY = "happy"
    JOG = "jog"
    RUN = "run"
    JUMP = "jump"
    CLIMB_DOWN = "climb_down"
    COVER_MOUTH = "cover_mouth"


STATE_ASSETS = {
    PetState.STANDARD: "01-core-standard.png",
    PetState.SIT: "02-pose-sit.png",
    PetState.WAVE: "03-pose-wave.png",
    PetState.EAT: "04-pose-eat.png",
    PetState.ROLL: "05-pose-roll.png",
    PetState.SLEEPY: "06-exp-sleepy.png",
    PetState.CRY: "19-exp-cry-action-v2.png",
    PetState.ANGRY: "08-exp-angry.png",
    PetState.HAPPY: "09-exp-happy.png",
    PetState.JOG: "14-move-jog.png",
    PetState.RUN: "15-move-run.png",
    PetState.JUMP: "16-move-jump.png",
    PetState.CLIMB_DOWN: "20-move-climb-back-v2.png",
    PetState.COVER_MOUTH: "18-interact-cover-mouth.png",
}


class PetStateMachine:
    """保存当前状态，并根据无操作时长计算自然待机状态。"""

    def __init__(self):
        self.current = PetState.STANDARD
        self.locked = False

    def set(self, state: PetState, force: bool = False) -> bool:
        if self.locked and not force:
            return False
        changed = state != self.current
        self.current = state
        return changed

    @staticmethod
    def idle_state(seconds: float) -> PetState:
        if seconds < 120:
            return PetState.STANDARD
        if seconds < 300:
            return PetState.SIT
        return PetState.SLEEPY
