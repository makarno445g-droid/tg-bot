LEVELS = {
    1: 175, 2: 350, 3: 525, 4: 700, 5: 875,
    6: 1050, 7: 1225, 8: 1400, 9: 1575, 10: 1750,
    11: 1925, 12: 2100, 13: 2275, 14: 2450, 15: 2625,
    16: 2800, 17: 2975, 18: 3150, 19: 3325, 20: 3500
}

WIN = {
    1: 65, 2: 62, 3: 59, 4: 56, 5: 53,
    6: 50, 7: 47, 8: 44, 9: 41, 10: 38,
    11: 35, 12: 33, 13: 31, 14: 29, 15: 27,
    16: 25, 17: 23, 18: 21, 19: 19, 20: 17
}

LOSE = {
    1: 10, 2: 10, 3: 13, 4: 16, 5: 19,
    6: 22, 7: 25, 8: 28, 9: 31, 10: 34,
    11: 37, 12: 40, 13: 43, 14: 46, 15: 49,
    16: 52, 17: 55, 18: 58, 19: 61, 20: 65
}


def get_level(elo):
    lvl = 1
    for k, v in LEVELS.items():
        if elo >= v:
            lvl = k
    return lvl


def win(player):
    player["elo"] += WIN[get_level(player["elo"])]


def lose(player):
    player["elo"] -= LOSE[get_level(player["elo"])]
    if player["elo"] < 0:
        player["elo"] = 0


def team_win(team_players, players):
    for uid in team_players:
        win(players[uid])


def team_lose(team_players, players):
    for uid in team_players:
        lose(players[uid])


def get_rating(players):
    result = []

    for uid, p in players.items():
        result.append({
            "nickname": p["nickname"],
            "elo": p["elo"],
            "level": get_level(p["elo"])
        })

    return sorted(result, key=lambda x: x["elo"], reverse=True)