from io import BytesIO
from aiogram.types import BotCommand
from aiogram.filters import Command

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from app.config import TELEGRAM_BOT_TOKEN
from app.database import SessionLocal
from app.schemas.workout import WorkoutData

from app.router import router_message

from app.services.media_groups import collect_media_group

from app.modes.research import graph
from app.modes.chat import chat_message
from app.modes.workouts import (
    parse_workout,
    analyze_workout,
    parse_workout_images,
    format_workout,
    correct_workout,
)
from app.modes.language import (
    normalize_language,
    create_welcome_message,
    system_message,
)

from app.services.users import (
    get_or_create_user,
    set_preferred_language,
)
from app.services.workouts import save_workout
from app.services.conversation import (
    save_message,
    get_recent_messages,
    to_langchain_messages,
)

from app.utils.text import clean_telegram_text

from app.states.workout import WorkoutStates
from app.states.users import UserStates


dp = Dispatcher()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def setup_bot_commands():
    await bot.set_my_commands([
        BotCommand(
            command="start",
            description="Start Gym Helper",
        ),
        BotCommand(
            command="language",
            description="Change language",
        ),
    ])


workout_confirmation_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅",
                callback_data="workout_save",
            ),
            InlineKeyboardButton(
                text="✏️",
                callback_data="workout_edit",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌",
                callback_data="workout_cancel",
            ),
        ],
    ]
)


async def add_workout_to_draft(
    state: FSMContext,
    new_workout: WorkoutData,
) -> WorkoutData:
    data = await state.get_data()

    existing_data = data.get("workout_data")

    if existing_data is None:
        merged_workout = new_workout

    else:
        existing_workout = WorkoutData.model_validate(
            existing_data
        )

        existing_workout.exercises.extend(
            new_workout.exercises
        )

        for index, exercise in enumerate(
            existing_workout.exercises,
            start=1,
        ):
            exercise.exercise_order = index

        merged_workout = existing_workout

    await state.update_data(
        workout_data=merged_workout.model_dump(
            mode="json"
        )
    )

    await state.set_state(
        WorkoutStates.waiting_for_confirmation
    )

    return merged_workout


async def show_workout_preview(
    message: Message,
    state: FSMContext,
    preview: str,
):
    data = await state.get_data()

    preview_message_id = data.get("preview_message_id")

    if preview_message_id:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=preview_message_id,
            text=clean_telegram_text(preview),
            reply_markup=workout_confirmation_keyboard,
        )
    else:
        sent_message = await message.answer(
            clean_telegram_text(preview),
            reply_markup=workout_confirmation_keyboard,
        )

        await state.update_data(
            preview_message_id=sent_message.message_id
        )

async def process_workout_images(
    messages: list[Message],
    state: FSMContext,
):
    image_bytes_list = []

    for message in messages:
        photo = message.photo[-1]

        file = await bot.get_file(
            photo.file_id
        )

        buffer = BytesIO()

        await bot.download_file(
            file.file_path,
            destination=buffer,
        )

        image_bytes_list.append(
            buffer.getvalue()
        )

    workout_data = await parse_workout_images(
        image_bytes_list
    )

    await state.update_data(
        workout_data=workout_data.model_dump(
            mode="json"
        )
    )

    await state.set_state(
        WorkoutStates.waiting_for_confirmation
    )

    preview = format_workout(
        workout_data
    )

    await show_workout_preview(
        message=messages[-1],
        state=state,
        preview=preview,
    )

@dp.message(Command("language"))
async def change_language_handler(
    message: Message,
    state: FSMContext,
):
    await state.set_state(
        UserStates.waiting_for_language
    )

    await message.answer(
        "🌍 Type your preferred language:"
    )

@dp.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    tg_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    language_code = message.from_user.language_code

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language_code=message.from_user.language_code,
        )

        language = user.preferred_language

        if language:
            await state.clear()

            welcome = await create_welcome_message(
                language=language,
                first_name=message.from_user.first_name,
            )

            await message.answer(
                clean_telegram_text(welcome)
            )
            return

        await state.set_state(
            UserStates.waiting_for_language
        )

        await message.answer(
            "🌍 Type your preferred language:"
        )


@dp.message(
    UserStates.waiting_for_language,
    F.text,
)
async def language_handler(
    message: Message,
    state: FSMContext,
):
    language = await normalize_language(
        message.text
    )

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language_code=message.from_user.language_code,
        )

        await set_preferred_language(
            session=session,
            user=user,
            language=language,
        )

    await state.clear()

    welcome_message = await create_welcome_message(
        language=language,
        first_name=message.from_user.first_name,
    )

    await message.answer(
        clean_telegram_text(welcome_message)
    )


@dp.message(
    WorkoutStates.waiting_for_correction,
    F.text,
)
async def workout_correction_handler(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    workout_data = WorkoutData.model_validate(
        data["workout_data"]
    )

    corrected_workout = await correct_workout(
        workout=workout_data,
        correction=message.text,
    )

    await state.update_data(
        workout_data=corrected_workout.model_dump(
            mode="json"
        )
    )

    await state.set_state(
        WorkoutStates.waiting_for_confirmation
    )
    preview = format_workout(
        corrected_workout
    )

    await show_workout_preview(
        message=message,
        state=state,
        preview=preview,
    )


@dp.message(F.text)
async def text_handler(message: Message, state: FSMContext):
    user_input = message.text

    tg_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    language_code = message.from_user.language_code

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            tg_id,
            username,
            first_name,
            language_code,
        )

        db_history = await get_recent_messages(
            session=session,
            user_id=user.id,
            limit=10,
        )

        history = to_langchain_messages(
            db_history
        )

        route = await router_message(
            user_input,
            history,
        )

        if route == "CHAT":
            response, _ = await chat_message(
                user_input,
                history,
                user.preferred_language,
            )

        elif route == "WORKOUT_LOG":
            workout_data = await parse_workout(
                user_input
            )

            workout_data = await add_workout_to_draft(
                state=state,
                new_workout=workout_data,
            )

            preview = format_workout(
                workout=workout_data
            )

            await show_workout_preview(
                message=message,
                state=state,
                preview=preview,
            )

            return

        elif route == "WORKOUT_ANALYSIS":
            response = await analyze_workout(
                message=user_input,
                history=history,
                session=session,
                user_id=user.id,
                language=user.preferred_language,
            )

        elif route == "RESEARCH":
            researching_message = await system_message(
                user.preferred_language,
                (
                    "Tell the user briefly that you are "
                    "searching for information."
                ),
            )

            await message.answer(
                clean_telegram_text(
                    researching_message
                )
            )

            result = await graph.ainvoke({
                "goal": user_input,
                "steps": [],
                "completed_tasks": [],
                "finished": False,
                "iteration": 0,
                "final_answer": "",
                "language": user.preferred_language,
            })

            response = result["final_answer"]

        else:
            response, _ = await chat_message(
                user_input,
                history,
                user.preferred_language,
            )

        response = clean_telegram_text(
            response
        )

        await save_message(
            session,
            user.id,
            "user",
            user_input,
        )

        await save_message(
            session,
            user.id,
            "assistant",
            response,
        )

        await message.answer(
            response
        )


@dp.message(F.photo)
async def photo_handler(
    message: Message,
    state: FSMContext,
):
    if message.media_group_id:
        await collect_media_group(
            message,
            lambda messages: process_workout_images(
                messages,
                state,
            ),
        )
        return

    await process_workout_images(
        [message],
        state,
    )

@dp.callback_query(
    WorkoutStates.waiting_for_confirmation,
    F.data == "workout_save",
)
async def save_workout_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()

    workout_data = WorkoutData.model_validate(
        data["workout_data"]
    )

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            tg_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            language_code=callback.from_user.language_code,
        )

        await save_workout(
            session=session,
            user_id=user.id,
            data=workout_data,
        )

        response = await system_message(
            user.preferred_language,
            (
                "Tell the user that their workout "
                "has been saved successfully. Include ✅."
            ),
        )

    await state.clear()

    await callback.message.edit_text(
        clean_telegram_text(response)
    )

    await callback.answer()


@dp.callback_query(
    WorkoutStates.waiting_for_confirmation,
    F.data == "workout_cancel",
)
async def cancel_workout_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    async with SessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            tg_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            language_code=callback.from_user.language_code,
        )

        response = await system_message(
            user.preferred_language,
            (
                "Tell the user briefly that the "
                "workout was not saved."
            ),
        )

    await state.clear()

    await callback.message.edit_text(
        clean_telegram_text(response)
    )

    await callback.answer()


@dp.callback_query(
    WorkoutStates.waiting_for_confirmation,
    F.data == "workout_edit",
)
async def edit_workout_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    async with SessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            tg_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            language_code=callback.from_user.language_code,
        )

        response = await system_message(
            user.preferred_language,
            (
                "Ask the user to describe what should be "
                "corrected in the recognized workout. "
                "Give one short example of a correction, "
                "such as changing the number of repetitions "
                "in one set."
            ),
        )

    await state.set_state(
        WorkoutStates.waiting_for_correction
    )

    await callback.message.answer(
        clean_telegram_text(response)
    )

    await callback.answer()