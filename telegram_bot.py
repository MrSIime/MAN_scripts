import os
import sys
import importlib
from pathlib import Path
import asyncio
import shutil
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import Router

# --- Configuration ---
API_TOKEN = ''
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


def import_module_for(proto_id: str, module_name: str = 'encoder'):
    """Import encoder or decoder module from a Prototype directory."""
    info = PROTOTYPES.get(proto_id)
    if not info:
        return None
    proto_module_path = f"{info['module']}.{module_name}"
    return importlib.import_module(proto_module_path)


def is_uncompressed_image(message: Message) -> bool:
    # Telegram sends photos in the `photo` field (compressed). If user sends as `document` with image mime,
    # it's typically uncompressed (original file). We enforce document with image mime.
    if message.document and message.document.mime_type and message.document.mime_type.startswith('image'):
        return True
    return False


def get_text_from_file(file_path: str) -> str:
    """Прочитати текст з файлу або повернути порожній рядок."""
    try:
        return Path(file_path).read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def cleanup_old_files(max_age_hours: int = 24):
    """Видалити папки користувачів старше max_age_hours днів."""
    try:
        current_time = datetime.now()
        for user_dir in TMP_DIR.iterdir():
            if user_dir.is_dir():
                mod_time = datetime.fromtimestamp(user_dir.stat().st_mtime)
                if current_time - mod_time > timedelta(hours=max_age_hours):
                    shutil.rmtree(user_dir, ignore_errors=True)
                    print(f'Видалено стару папку: {user_dir}')
    except Exception as e:
        print(f'Помилка очищення: {e}')


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text='Prototype 1', callback_data='proto_1'),
            types.InlineKeyboardButton(text='Prototype 2', callback_data='proto_2'),
        ],
        [
            types.InlineKeyboardButton(text='Prototype 3', callback_data='proto_3'),
            types.InlineKeyboardButton(text='Prototype 4', callback_data='proto_4'),
        ]
    ])
    await message.answer('Оберіть прототип:', reply_markup=kb)
    await state.set_state(Form.choosing_proto)


@router.callback_query(lambda c: c.data and c.data.startswith('proto_'), StateFilter(Form.choosing_proto))
async def proto_chosen(cb: CallbackQuery, state: FSMContext):
    proto_id = cb.data.split('_', 1)[1]
    await state.update_data(proto=proto_id)

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Encode', callback_data='action_encode')],
        [types.InlineKeyboardButton(text='Decode', callback_data='action_decode')]
    ])

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

    user_dir = TMP_DIR / str(message.from_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # зберігаємо вхідне зображення
    filename = message.document.file_name or 'input_image'
    in_path = user_dir / filename
    
    # Download file using aiogram 3.x API
    await message.bot.download(file=message.document.file_id, destination=str(in_path))

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
    text_path = user_dir / 'input_text.txt'

    if message.text and not message.document:
        # текст у повідомленні
        text_path.write_text(message.text, encoding='utf-8')
    elif message.document:
        # файл -- зберігаємо
        filename = message.document.file_name or 'text_input.txt'
        text_path = user_dir / filename
        await message.bot.download(file=message.document.file_id, destination=str(text_path))
    else:
        await message.reply('Надішліть текст або текстовий файл (.txt).')
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
    module = import_module_for(proto, 'encoder')
    user_dir = TMP_DIR / str(user_id)
    in_image = data['image_path']
    in_text = data.get('text_path')

    out_image = user_dir / 'out_image.png'

    try:
        # --- Перевірка чи текст вміститься у зображення ---
        from PIL import Image
        import numpy as np
        # Відкриваємо зображення
        img = Image.open(in_image).convert("RGB")
        px = np.array(img, dtype=np.uint8)
        flat_px = px.flatten()
        # Читаємо текст
        text_bytes = Path(in_text).read_bytes()
        length_bytes = len(text_bytes).to_bytes(4, "big")
        full_data = length_bytes + text_bytes
        bits_to_hide = "".join(f"{b:08b}" for b in full_data)
        total_bits_count = len(bits_to_hide)
        if total_bits_count > len(flat_px):
            await bot.send_message(user_id, f'Текст ({len(text_bytes)} байт) не вміститься у це зображення!\nМожна вбудувати максимум {(len(flat_px)-32)//8} байт.')
            await state.clear()
            return

        # викликаємо функцію encode з модулю; різні прототипи мають різні сигнатури
        if PROTOTYPES[proto]['needs_key']:
            key = data.get('key')
            module.encode(in_image, in_text, str(out_image), key)
        else:
            # прототипи без ключа мають сигнатуру (image, text, out)
            module.encode(in_image, in_text, str(out_image))

        # надсилаємо файл як документ, щоб Telegram не стиснув його
        await bot.send_document(user_id, FSInputFile(str(out_image)))
        await bot.send_message(user_id, 'Готово — закодоване зображення надіслано.')
    except Exception as e:
        await bot.send_message(user_id, f'Під час кодування сталася помилка: {e}')
    finally:
        await state.clear()


async def process_decode(user_id: int, state: FSMContext):
    data = await state.get_data()
    proto = data['proto']
    module = import_module_for(proto, 'decoder')
    user_dir = TMP_DIR / str(user_id)
    in_image = data['image_path']
    out_text = user_dir / 'decoded_output.txt'

    try:
        if PROTOTYPES[proto]['needs_key']:
            key = data.get('key')
            module.decode(in_image, str(out_text), key)
        else:
            module.decode(in_image, str(out_text))

        # Якщо файл існує, перевіримо розмір тексту
        if out_text.exists():
            try:
                decoded_text = out_text.read_text(encoding='utf-8', errors='ignore')
                if len(decoded_text) < 200:
                    # малий текст — надішлемо повідомленням
                    await bot.send_message(user_id, f'Декодований текст:\n\n{decoded_text}')
                else:
                    # великий текст — надішлемо файлом
                    await bot.send_document(user_id, FSInputFile(str(out_text)))
                    await bot.send_message(user_id, 'Декодований текст (>200 символів) надіслано як файл.')
            except Exception as read_err:
                await bot.send_message(user_id, f'Помилка читання результату: {read_err}')
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
    cleanup_old_files(max_age_hours=24)  # Видалити файли старше 24 годин

    # Автоматичні повторні спроби старту polling при мережевих або тимчасових помилках.
    # Використовуємо експоненційний backoff з лімітом паузи.
    backoff = 1.0
    max_backoff = 60.0
    attempt = 0
    while True:
        try:
            attempt += 1
            print(f'Polling attempt #{attempt} (backoff={backoff}s)')
            await dp.start_polling(bot)
            # Якщо polling завершився без винятку, вийдемо
            break
        except (KeyboardInterrupt, SystemExit):
            print('Received termination signal, exiting.')
            raise
        except Exception as e:
            # Логування помилки і очікування перед новою спробою
            print(f'Polling failed (attempt {attempt}): {e}')
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
            continue


if __name__ == '__main__':
    asyncio.run(main())
