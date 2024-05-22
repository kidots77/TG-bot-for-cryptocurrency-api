import os
import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from dotenv import load_dotenv
from api_functions import coin_price, coin_name


load_dotenv()

TG_TOKEN = os.getenv('TOKEN')
COIN_BUTTONS = 
REACH_EDGE_PHRASE = ("Цена за монету {} достигла {} значения {}. Текущее: {}")


bot = Bot(TG_TOKEN)
dp = Dispatcher()

coins_dict = {}
ready_low_edge_coins = []
ready_high_edge_coins = []


class Coin(StatesGroup):
    current_coin = State()
    choice_state = State()
    min_price = State()
    max_price = State()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Функция для команды /start.
    Назначает state для Coin.current_coin
    и отправляет сообщение со списком доступных моент.
    """
    global user
    user = message.from_user.id
    await state.set_state(Coin.current_coin)
    await message.answer(
        f'Здравствуйте, {message.from_user.first_name}. '
        f'Выберите интересующую вас монету.',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=i)] for i in coin_name()],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


@dp.message(Coin.current_coin)
async def send_price(message: Message, state: FSMContext) -> None:
    """
    Вызывается при ответе на команду /start.
    Обновляет state для Coin.choice_state
    и отправляет сообщение с текущей ценой выбранной монеты.
    Уведомляет пользователя, если выбранная монета уже отслеживается.
    В ином случае спрашивает, нужно ли отслеживать выбранную монету.
    """
    await state.update_data(current_coin=message.text)
    data = await state.get_data()
    await state.set_state(Coin.choice_state)
    if data['current_coin'] in coins_dict:
        await message.answer(
            f"Монета {data['current_coin']} уже отслеживается."
        )
    else:
        await message.answer(
            f"{coin_price(data['current_coin'])} USD. Отслеживать эту монету?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='Да')],
                    [KeyboardButton(text='Нет')]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )


@dp.message(Coin.choice_state)
async def ask_min_edge(message: Message, state: FSMContext):
    """
    Вызывается при положительном ответе для отслеживания.
    Обновляет state для Coin.min_price
    и запрашивает минимальный порог для отслеживания.
    """
    await state.update_data(choice_state=message.text)
    data = await state.get_data()
    if data['choice_state'] == 'Да':
        await message.answer(
            'Укажите минимальный порог для отслеживания в USD.'
        )
        await state.set_state(Coin.min_price)


@dp.message(Coin.min_price)
async def ask_max_edge(message: Message, state: FSMContext):
    """
    Обновляет state для Coin.max_price
    и запрашивает максимальный порог для отслеживания.
    """
    await state.update_data(min_price=message.text)
    await state.set_state(Coin.max_price)
    await message.answer('Укажите максимальный порог для отслеживания в USD.')


@dp.message(Coin.max_price)
async def save_data(message: Message, state: FSMContext):
    """
    Сохраняет данные для выбранной монеты и добавляет её в словарь coins_dict.
    Уведомляет пользователя, что монета отслеживается.
    """
    await state.update_data(max_price=message.text)
    data = await state.get_data()
    coins_dict[data['current_coin']] = data
    await message.answer(
        F'Спасибо. Отслеживаю монету {data["current_coin"]} для вас.'
    )
    await state.clear()


async def check_coin_price():
    """
    Функция для мониторинга цены отслеживаемых монет
    и отправления соответствующего сообщения,
    если монета дошла до одного из порогов.
    """
    while True:
        for coin in coins_dict.keys():
            current_coin_price = coin_price(coin)
            if float(coins_dict[coin]['min_price']) >= current_coin_price:
                ready_low_edge_coins.append(coin)
            elif float(coins_dict[coin]['max_price']) <= current_coin_price:
                ready_high_edge_coins.append(coin)

        if ready_low_edge_coins:
            for coin in ready_low_edge_coins:
                await bot.send_message(
                    user,
                    text=REACH_EDGE_PHRASE.format(
                        coins_dict[coin]['current_coin'],
                        'минимального',
                        coins_dict[coin]['min_price'],
                        coin_price(coin)
                    )
                )
                del coins_dict[coin]
                del ready_low_edge_coins[ready_low_edge_coins.index(coin)]

        if ready_high_edge_coins:
            for coin in ready_high_edge_coins:
                await bot.send_message(
                    user,
                    text=REACH_EDGE_PHRASE.format(
                        coins_dict[coin]['current_coin'],
                        'максимального',
                        coins_dict[coin]['max_price'],
                        coin_price(coin)
                    )
                )
                del coins_dict[coin]
                del ready_high_edge_coins[ready_high_edge_coins.index(coin)]
        await asyncio.sleep(5)


async def main():
    asyncio.create_task(check_coin_price())
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
