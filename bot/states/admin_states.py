from aiogram.fsm.state import State, StatesGroup


class AddMovieStates(StatesGroup):
    title = State()
    genre = State()
    description = State()
    poster = State()
    video = State()
    add_code = State()


class AddCodeStates(StatesGroup):
    code = State()


class BroadcastStates(StatesGroup):
    message = State()
    confirm = State()


class AddAdStates(StatesGroup):
    content = State()
    button_text = State()
    button_url = State()


class AddChannelStates(StatesGroup):
    channel_id = State()
