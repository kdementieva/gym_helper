from aiogram.fsm.state import State, StatesGroup


class WorkoutStates(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_correction = State()