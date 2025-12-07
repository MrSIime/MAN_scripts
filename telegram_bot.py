import os
import sys
import importlib
from pathlib import Path
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram import Router

# --- Configuration ---
API_TOKEN = '8037003535:AAHrKOtyOI_kc2Jd9qJMEC_7oVxLWIAIJYw'
ROOT = Path(__file__).resolve().parent
TMP_DIR = ROOT / 'tmp'
TMP_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT))  # щоб можна було імпортувати Prototype_* як пакети

# Метадані по прототипах: чи потрібен користувацький ключ
PROTOTYPES = {
    '1': {'module': 'Prototype_1', 'needs_key': False},
    '2': {'module': 'Prototype_2', 'needs_key': True},
    '3': {'module': 'Prototype_3', 'needs_key': False},
    '4': {'module': 'Prototype_4', 'needs_key': True},
}


class Form(StatesGroup):
    choosing_proto = State()
    choosing_action = State()
    waiting_image = State()
    waiting_text = State()
    waiting_key = State()


def import_module_for(proto_id: str):
    info = PROTOTYPES.get(proto_id)
    if not info:
        return None
    return importlib.import_module(info['module'])


def is_uncompressed_image(message: Message) -> bool:
    # Telegram sends photos in the `photo` field (compressed). If user sends as `document` with image mime,
    # it's typically uncompressed (original file). We enforce document with image mime.
    if message.document and message.document.mime_type and message.document.mime_type.startswith('image'):
        return True
    return False


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('Prototype 1', callback_data='proto_1'),
        types.InlineKeyboardButton('Prototype 2', callback_data='proto_2'),
        types.InlineKeyboardButton('Prototype 3', callback_data='proto_3'),
        types.InlineKeyboardButton('Prototype 4', callback_data='proto_4'),
    )
    await message.answer('Оберіть прототип:', reply_markup=kb)
    await state.set_state(Form.choosing_proto)


@router.callback_query(lambda c: c.data and c.data.startswith('proto_'), StateFilter(Form.choosing_proto))
async def proto_chosen(cb: CallbackQuery, state: FSMContext):
    proto_id = cb.data.split('_', 1)[1]
    await state.update_data(proto=proto_id)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Encode', callback_data='action_encode'))
    kb.add(types.InlineKeyboardButton('Decode', callback_data='action_decode'))

    # edit original message
    if cb.message:
        await cb.message.edit_text(f'Ви обрали Prototype {proto_id}. Тепер оберіть дію.', reply_markup=kb)
    await state.set_state(Form.choosing_action)


@router.callback_query(lambda c: c.data and c.data.startswith('action_'), StateFilter(Form.choosing_action))
async def action_chosen(cb: CallbackQuery, state: FSMContext):
    action = cb.data.split('_', 1)[1]
    await state.update_data(action=action)

    await cb.message.answer('Відправте зображення без стиснення як "Document" (натисніть "Attach file" -> файл, не фото).')
    await state.set_state(Form.waiting_image)


@router.message(StateFilter(Form.waiting_image))
async def receive_image(message: Message, state: FSMContext):
    # Перевірка на те, що зображення надіслане як документ і має image mime-type
    if not is_uncompressed_image(message):
        await message.reply('Будь ласка, надішліть зображення як документ без стиснення (натисніть "Attach file" -> файл, не фото).')
        return

    data = await state.get_data()
    user_dir = TMP_DIR / str(message.from_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # зберігаємо вхідне зображення
    filename = message.document.file_name or 'input_image'
    in_path = user_dir / filename
    await message.document.download(destination_file=str(in_path))

    await state.update_data(image_path=str(in_path))

    data = await state.get_data()
    proto = data.get('proto')
    needs_key = PROTOTYPES[proto]['needs_key']

    if data.get('action') == 'encode':
        await message.answer('Тепер надішліть текст повідомлення або завантажте .txt файл із текстом, який потрібно вбудувати.')
        await state.set_state(Form.waiting_text)
    else:
        if needs_key:
            await message.answer('Цей прототип вимагає ключа. Введіть числовий ключ:')
            await state.set_state(Form.waiting_key)
        else:
            # запустити декодування без ключа
            await message.answer('Починаю декодування...')
            await process_decode(message.from_user.id, state)


@router.message(StateFilter(Form.waiting_text))
async def receive_text(message: Message, state: FSMContext):
    user_dir = TMP_DIR / str(message.from_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    text_path = user_dir / 'input_text.bin'

    if message.text and not message.document:
        # текст у повідомленні
        (user_dir / 'text_message.txt').write_text(message.text, encoding='utf-8')
        text_path = user_dir / 'text_message.txt'
    elif message.document:
        # файл -- зберігаємо бінарно
        filename = message.document.file_name or 'text_input'
        text_path = user_dir / filename
        await message.document.download(destination_file=str(text_path))
    else:
        await message.reply('Надішліть текст або текстовий файл.')
        return

    await state.update_data(text_path=str(text_path))

    data = await state.get_data()
    needs_key = PROTOTYPES[data['proto']]['needs_key']
    if needs_key:
        await message.answer('Введіть числовий ключ (ціле число):')
        await state.set_state(Form.waiting_key)
    else:
        await message.answer('Починаю кодування...')
        await process_encode(message.from_user.id, state)


@router.message(StateFilter(Form.waiting_key))
async def receive_key(message: Message, state: FSMContext):
    txt = message.text.strip()
    try:
        key = int(txt)
    except Exception:
        await message.reply('Ключ має бути цілим числом. Спробуйте ще раз.')
        return

    await state.update_data(key=key)
    data = await state.get_data()
    if data.get('action') == 'encode':
        await message.answer('Починаю кодування...')
        await process_encode(message.from_user.id, state)
    else:
        await message.answer('Починаю декодування...')
        await process_decode(message.from_user.id, state)


async def process_encode(user_id: int, state: FSMContext):
    data = await state.get_data()
    proto = data['proto']
    module = import_module_for(proto)
    user_dir = TMP_DIR / str(user_id)
    in_image = data['image_path']
    in_text = data.get('text_path')
    out_image = user_dir / 'out_image.png'

    try:
        # викликаємо функцію encode з модулю; різні прототипи мають різні сигнатури
        if PROTOTYPES[proto]['needs_key']:
            key = data.get('key')
            module.encode(in_image, in_text, str(out_image), key)
        else:
            # прототипи без ключа мають сигнатуру (image, text, out)
            module.encode(in_image, in_text, str(out_image))

        # надсилаємо файл як документ, щоб Telegram не стиснув його
        await bot.send_document(user_id, types.InputFile(str(out_image)))
        await bot.send_message(user_id, 'Готово — результат надіслано як файл (без стиснення).')
    except Exception as e:
        await bot.send_message(user_id, f'Під час кодування сталася помилка: {e}')
    finally:
        await state.clear()


async def process_decode(user_id: int, state: FSMContext):
    data = await state.get_data()
    proto = data['proto']
    module = import_module_for(proto)
    user_dir = TMP_DIR / str(user_id)
    in_image = data['image_path']
    out_text = user_dir / 'decoded_output'

    try:
        if PROTOTYPES[proto]['needs_key']:
            key = data.get('key')
            module.decode(in_image, str(out_text), key)
        else:
            module.decode(in_image, str(out_text))

        # Якщо файл існує, надішлемо як документ
        if out_text.exists():
            await bot.send_document(user_id, types.InputFile(str(out_text)))
            await bot.send_message(user_id, 'Готово — результат надіслано.')
        else:
            await bot.send_message(user_id, 'Декодування завершилось без створення файлу (можливо помилка).')
    except Exception as e:
        await bot.send_message(user_id, f'Під час декодування сталася помилка: {e}')
    finally:
        await state.clear()


@router.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.reply('Операція скасована.')


async def main():
    print('Starting bot...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
