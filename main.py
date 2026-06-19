import asyncio
import json
import os


from config import TOKEN, ADMIN_ID
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery
class CreateTeam(StatesGroup):
    waiting_name = State()

from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)


# =========================
# CONFIG
# =========================


bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DATA_FILE = "data.json"


def team_kb(tid: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Приєднатися",
                    callback_data=f"join_{tid}"
                )
            ]
        ]
    )


# =========================
# REGISTRATION (FSM)
# =========================

class Registration(StatesGroup):
    first_name = State()
    last_name = State()
    age = State()
    game = State()


games_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="CS2")],
        [KeyboardButton(text="Dota2")],
        [KeyboardButton(text="Valorant")],
        [KeyboardButton(text="Chess")]
    ],
    resize_keyboard=True
)


@dp.message(Registration.game)
async def get_game(message: Message, state: FSMContext):
    data = await state.get_data()

    uid = str(message.from_user.id)
    p = get_user(uid)

    # запис у профіль 1
    p["profiles"]["1"] = {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "age": data["age"],
        "nick": message.from_user.username or ""
    }

    p["games"] = [message.text]

    await state.clear()
    save()

    await message.answer(
        f"✅ Реєстрація завершена!\n\n"
        f"👤 Ім'я: {data['first_name']}\n"
        f"👤 Прізвище: {data['last_name']}\n"
        f"🎂 Вік: {data['age']}\n"
        f"🎮 Гра: {message.text}"
    )


# =========================
# DATABASE
# =========================
players = {}
teams = {}
tournaments = {}
matches = {}
team_counter = 1
class TournamentCreate(StatesGroup):
    waiting_name = State()


# =========================
# SAFE UTIL
# =========================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def get_user(uid: str):
    """
    🔥 ГОЛОВНА ФУНКЦІЯ ЗАХИСТУ
    створює або виправляє користувача
    """

    if uid not in players:
        players[uid] = {
            "elo": 175,
            "wins": 0,
            "loses": 0,
            "matches": 0,
            "team": None,
            "games": [],
            "active_profile": "1",
            "profiles": {
                "1": {"first_name": "", "last_name": "", "age": "", "nick": ""},
                "2": {"first_name": "", "last_name": "", "age": "", "nick": ""}
            }
        }

    p = players[uid]

    # 🔥 MIGRATION SAFETY (ДУЖЕ ВАЖЛИВО)
    p.setdefault("elo", 175)
    p.setdefault("wins", 0)
    p.setdefault("loses", 0)
    p.setdefault("matches", 0)
    p.setdefault("team", None)
    p.setdefault("games", [])

    p.setdefault("active_profile", "1")

    if "profiles" not in p:
        p["profiles"] = {
            "1": {"first_name": "", "last_name": "", "age": "", "nick": ""},
            "2": {"first_name": "", "last_name": "", "age": "", "nick": ""}
        }
    else:
        p["profiles"].setdefault("1", {"first_name": "", "last_name": "", "age": "", "nick": ""})
        p["profiles"].setdefault("2", {"first_name": "", "last_name": "", "age": "", "nick": ""})

    return p


def level(elo: int) -> int:
    return min(20, elo // 175 + 1)


def clean_empty_teams():
    empty = []

    for tid, team in teams.items():
        if not team["players"]:
            empty.append(tid)

    remove_team_from_tournaments(tid)
    del teams[tid]
    save()


def remove_team_from_tournaments(team_id: str):
    for tid in tournaments:
        if team_id in tournaments[tid].get("teams", []):
            tournaments[tid]["teams"].remove(team_id)


# =========================
# SAVE / LOAD
# =========================
def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "players": players,
            "teams": teams,
            "tournaments": tournaments,
            "matches": matches,
            "team_counter": team_counter
        }, f, ensure_ascii=False, indent=2)


def load():
    global players, teams, tournaments, matches, team_counter

    if not os.path.exists(DATA_FILE):
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    players.update(data.get("players", {}))
    teams.update(data.get("teams", {}))
    tournaments.update(data.get("tournaments", {}))
    matches.update(data.get("matches", {}))
    team_counter = data.get("team_counter", 1)


# =========================
# ELO SYSTEM
# =========================
def win_player(p):
    p["elo"] += 20
    p["wins"] += 1
    p["matches"] += 1


def lose_player(p):
    p["elo"] = max(0, p["elo"] - 15)
    p["loses"] += 1
    p["matches"] += 1


def team_win(team_id):
    for uid in teams[team_id]["players"]:
        win_player(players[uid])


def team_lose(team_id):
    for uid in teams[team_id]["players"]:
        lose_player(players[uid])


# =========================
# KEYBOARDS
# =========================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧑 Профіль")],


        [KeyboardButton(text="🛠️ Створити команду")],
        [KeyboardButton(text="👥 Моя команда")],
        [KeyboardButton(text="📋 Список команд")],
        [KeyboardButton(text="🚪 Вийти з команди")],


        [KeyboardButton(text="🏆 Турніри")],
        [KeyboardButton(text="⚔ Створити турнір")],
        [KeyboardButton(text="🗑 Видалити команду")],

        [KeyboardButton(text="🏁 Створити матч")],
        [KeyboardButton(text="⚔ WIN MATCH")],
        [KeyboardButton(text="💀 LOSE MATCH")],

        [KeyboardButton(text="📊 Рейтинг")],
        [KeyboardButton(text="🏅 ELO Рейтинг")]
    ],
    resize_keyboard=True
)


# =========================
# START
# =========================
@dp.message(CommandStart())
async def start(message: Message):
    uid = str(message.from_user.id)
    get_user(uid)
    save()

    await message.answer("🚀 Бот запущено", reply_markup=main_menu)


# =========================
# PROFILE
# =========================
@dp.message(F.text == "🧑 Профіль")
async def profile(message: Message):
    uid = str(message.from_user.id)
    p = get_user(uid)

    pr = p["profiles"][p["active_profile"]]

    wr = round((p["wins"] / p["matches"]) * 100, 1) if p["matches"] else 0

    await message.answer(
        f"👤 Профіль\n"
        f"Ім'я: {pr['first_name']}\n"
        f"Прізвище: {pr['last_name']}\n"
        f"Вік: {pr['age']}\n"
        f"Нік: {pr['nick']}\n"
        f"ELO: {p['elo']}\n"
        f"Lvl: {level(p['elo'])}\n"
        f"Winrate: {wr}%"
    )


# =========================
# TEAM SYSTEM
# =========================

@dp.message(F.text == "🛠️ Створити команду")
async def create_team(message: Message, state: FSMContext):
    await message.answer("✏️ Введи назву команди:")
    await state.set_state(CreateTeam.waiting_name)


@dp.message(CreateTeam.waiting_name)
async def create_team_finish(message: Message, state: FSMContext):
    global team_counter

    uid = str(message.from_user.id)
    player = get_user(uid)

    team_name = message.text.strip()
    tid = str(team_counter)

    teams[tid] = {
        "name": team_name,
        "players": [uid]
    }

    player["team"] = tid

    team_counter += 1
    save()

    await message.answer(f"👥 Команду «{team_name}» створено")
    await state.clear()


# =========================
# 👥 СКЛАД КОМАНДИ
# =========================
@dp.message(F.text == "👥 Моя команда")
async def my_team(message: Message):
    uid = str(message.from_user.id)
    p = get_user(uid)

    if not p["team"]:
        return await message.answer("Немає команди")

    text = "👥 Команда:\n"
    for u in teams[p["team"]]["players"]:
        text += f"- {players[u]['elo']} ELO\n"

    await message.answer(text)


# =========================
# 👥 СПИСОК КОМАНД
# =========================
@dp.message(F.text == "📋 Список команд")
async def list_teams(message: Message):
    if not teams:
        return await message.answer("❌ Команд немає")

    text = "👥 Список команд:\n\n"

    for tid, team in teams.items():
        name = team.get("name", f"Команда {tid}")
        count = len(team["players"])

        kb_buttons = []

        # кнопка приєднання (якщо хочеш залишити)
        kb_buttons.append([
            InlineKeyboardButton(
                text="➕ Приєднатися",
                callback_data=f"team_join_{tid}"
            )
        ])

        # 👇 АДМІН-КНОПКА ВИДАЛЕННЯ КОМАНДИ
        kb_buttons.append([
            InlineKeyboardButton(
                text="🗑 Видалити команду",
                callback_data=f"delete_team_admin_{tid}"
            )
        ])

        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)

        await message.answer(
            f"🆔 ID: {tid}\n"
            f"👥 Назва: {name}\n"
            f"👤 Учасників: {count}",
            reply_markup=kb
        )

    await message.answer(text)


# =========================
# 🚪 ВИХІД З КОМАНДИ
# =========================
@dp.message(F.text == "🚪 Вийти з команди")
async def leave_team(message: Message):
    uid = str(message.from_user.id)
    p = get_user(uid)

    if p["team"] and p["team"] in teams:
        if uid in teams[p["team"]]["players"]:
            teams[p["team"]]["players"].remove(uid)

        p["team"] = None

        save()

    await message.answer("🚪 Вийшов з команди")


# =========================
# 🗑 ВИДАЛЕННЯ КОМАНДИ
# =========================
@dp.message(F.text == "🗑 Видалити команду")
async def delete_team(message: Message):
    uid = str(message.from_user.id)
    tid = players.get(uid, {}).get("team")

    if not tid or tid not in teams:
        return await message.answer("Ти не в команді")

    if not teams[tid]["players"] or teams[tid]["players"][0] != uid:
        return await message.answer("❌ Тільки лідер може видалити команду")

    for user in teams[tid]["players"]:
        players[user]["team"] = None

    del teams[tid]
    save()

    await message.answer("❌ Команду видалено")


# =========================
# ➕ ПРИЄДНАННЯ ДО КОМАНДИ (INLINE)
# =========================
@dp.callback_query(
    F.data.startswith("join_") &
    ~F.data.startswith("join_tournament_")
)
async def join_team(call: CallbackQuery):
    uid = str(call.from_user.id)
    tid = call.data.split("_")[1]

    if tid not in teams:
        return await call.answer("Команду не знайдено", show_alert=True)

    player = get_user(uid)

    # якщо вже в цій команді
    if player["team"] == tid:
        return await call.answer("Ти вже в цій команді")

    # вихід зі старої команди
    old = player["team"]
    if old and old in teams and uid in teams[old]["players"]:
        teams[old]["players"].remove(uid)

    # 🔥 захист від дубля
    if uid not in teams[tid]["players"]:
        teams[tid]["players"].append(uid)

    player["team"] = tid

    save()

    await call.answer("Ти приєднався до команди ✅")
# =========================
# TOURNAMENTS (ADMIN ONLY)
# =========================

# =========================
# 🏆 TOURNAMENT SYSTEM
# =========================

# ---------- CREATE TOURNAMENT ----------
@dp.message(F.text == "⚔ Створити турнір")
async def create_tournament(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Тільки адмін")

    await state.set_state(TournamentCreate.waiting_name)
    await message.answer("🏆 Введіть назву турніру:")


@dp.message(TournamentCreate.waiting_name)
async def tournament_name(message: Message, state: FSMContext):
    global tournaments

    tid = str(len(tournaments) + 1)

    tournaments[tid] = {
        "name": message.text,
        "teams": []
    }

    save()
    await state.clear()

    await message.answer(f"🏆 Турнір '{message.text}' створено")


# ---------- SHOW TOURNAMENTS ----------
@dp.message(F.text == "🏆 Турніри")
async def show_tournaments(message: Message):

    if not tournaments:
        return await message.answer("🏆 Турнірів поки немає")

    for tid, t in tournaments.items():


        for team_id in list(t["teams"]):
            if team_id not in teams:
                t["teams"].remove(team_id)

        buttons = []

        # ➕ JOIN BUTTON
        buttons.append([
            InlineKeyboardButton(
                text="✅ Зареєструватися",
                callback_data=f"join_tournament_{tid}"
            )
        ])

        # 🗑 DELETE BUTTON (ADMIN ONLY)
        if is_admin(message.from_user.id):
            buttons.append([
                InlineKeyboardButton(
                    text="🗑 Видалити турнір",
                    callback_data=f"delete_tournament_{tid}"
                )
            ])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        teams_list = []

        for team_id in t["teams"]:
            if team_id in teams:
                teams_list.append(teams[team_id]["name"])

        if teams_list:
            teams_text = "\n".join([f"• {name}" for name in teams_list])
        else:
            teams_text = "Немає зареєстрованих команд"

        await message.answer(
            f"🏆 Турнір: {t['name']}\n"
            f"👥 Зареєстровано команд: {len(t['teams'])}\n\n"
            f"📋 Команди:\n{teams_text}",
            reply_markup=kb
        )


# ---------- JOIN TOURNAMENT ----------
@dp.callback_query(F.data.startswith("join_tournament_"))
async def join_tournament(callback: CallbackQuery):

    uid = str(callback.from_user.id)
    player = get_user(uid)

    print("UID:", uid)
    print("PLAYER TEAM:", player.get("team"))
    print("ALL TEAMS:", teams)

    if not player["team"]:
        return await callback.answer(
            "Спочатку створіть команду",
            show_alert=True
        )

    tid = callback.data.split("_")[2]

    if tid not in tournaments:
        return await callback.answer(
            "Турнір не знайдено",
            show_alert=True
        )

    team_id = player["team"]

    if team_id not in teams:
        return await callback.answer(
            f"Команду не знайдено. team_id={team_id}",
            show_alert=True
        )

    if team_id in tournaments[tid]["teams"]:
        return await callback.answer(
            "Вже зареєстровано",
            show_alert=True
        )

    tournaments[tid]["teams"].append(team_id)
    save()

    await callback.answer("Команду зареєстровано ✅")


# ---------- DELETE TOURNAMENT ----------
@dp.callback_query(F.data.startswith("delete_tournament_"))
async def delete_tournament(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Тільки адмін", show_alert=True)

    tid = callback.data.split("_")[2]

    if tid not in tournaments:
        return await callback.answer("Турнір не знайдено", show_alert=True)

    del tournaments[tid]
    save()

    await callback.answer("Турнір видалено 🗑")
    await callback.message.edit_text("❌ Турнір видалено")

@dp.callback_query(F.data.startswith("delete_team_admin_"))
async def delete_team_admin(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Тільки адмін", show_alert=True)

    tid = callback.data.split("_")[3]

    if tid not in teams:
        return await callback.answer("Команду не знайдено", show_alert=True)

    # очистити гравців
    for uid in teams[tid]["players"]:
        if uid in players:
            players[uid]["team"] = None

    del teams[tid]
    save()

    await callback.answer("🗑 Команду видалено")
    await callback.message.edit_text("❌ Команду видалено адміном")

# =========================
# MATCH SYSTEM
# =========================
@dp.message(F.text == "⚔ WIN MATCH")
async def win_match(message: Message):
    p = get_user(str(message.from_user.id))

    if not p["team"]:
        return await message.answer("Немає команди")

    team_win(p["team"])
    save()

    await message.answer("✅ Win зараховано")


@dp.message(F.text == "💀 LOSE MATCH")
async def lose_match(message: Message):
    p = get_user(str(message.from_user.id))

    if not p["team"]:
        return await message.answer("Немає команди")

    team_lose(p["team"])
    save()

    await message.answer("❌ Lose зараховано")


# =========================
# RATING
# =========================
@dp.message(F.text == "📊 Рейтинг")
async def rating(message: Message):
    sorted_players = sorted(players.items(), key=lambda x: x[1]["elo"], reverse=True)

    text = "📊 Рейтинг:\n\n"
    for i, (_, p) in enumerate(sorted_players, 1):
        text += f"{i}. {p['elo']} ELO\n"

    await message.answer(text)


@dp.message(F.text == "🏅 ELO Рейтинг")
async def elo_rating(message: Message):
    sorted_players = sorted(players.items(), key=lambda x: x[1]["elo"], reverse=True)

    text = "🏅 ELO:\n\n"
    for i, (_, p) in enumerate(sorted_players, 1):
        text += f"{i}. Lvl {level(p['elo'])} ({p['elo']})\n"

    await message.answer(text)


# =========================
# RUN BOT
# =========================
async def main():
    load()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())