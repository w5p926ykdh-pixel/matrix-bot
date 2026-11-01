
import asyncio
import getpass
import json
import math
import os
import random
import string
import time
import uuid
from datetime import datetime, timezone

from nio import AsyncClient, RoomMessageText

HOMESERVER = "https://matrix.org"
USER_ID = "@zacino:matrix.org"

SCORES_FILE = "scores.json"
START_TIME_MS = 0

scores = {}
guess_games = {}


def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_scores():
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)


async def reply(client, room_id, message):
    await client.room_send(
        room_id=room_id,
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": str(message)
        }
    )


COMMANDS = {
    "!help", "!ping", "!coin", "!dice", "!roll", "!flip",
    "!random", "!choose", "!8ball", "!rate", "!ship",
    "!joke", "!fact", "!trivia", "!rps", "!number",
    "!password", "!uuid", "!guess", "!reverse", "!upper",
    "!lower", "!mock", "!clap", "!spoiler", "!count",
    "!vowels", "!length", "!repeat", "!emojify", "!sqrt",
    "!percent", "!table", "!binary", "!unbinary", "!hex",
    "!unhex", "!compliment", "!insult", "!leaderboard",
    "!points", "!uptime"
}

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "Why did the computer go to the doctor? It had a virus.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "Why was the JavaScript developer sad? They didn't know how to null their feelings."
]

FACTS = [
    "Octopuses have three hearts.",
    "A day on Venus is longer than its year.",
    "Honey can remain edible for a very long time when stored properly.",
    "Bananas are berries, botanically speaking.",
    "Sharks existed before trees.",
    "The Moon is slowly moving away from Earth."
]

TRIVIA = [
    ("What is the capital of France?", ["paris"]),
    ("How many sides does a hexagon have?", ["6", "six"]),
    ("What planet is known as the Red Planet?", ["mars"]),
    ("What is 9 × 8?", ["72", "seventy two", "seventy-two"]),
    ("What is the largest ocean on Earth?", ["pacific", "pacific ocean"]),
    ("Which language is commonly used with matrix-nio?", ["python"])
]

COMPLIMENTS = [
    "You're more capable than you think.",
    "Your curiosity is a strength.",
    "You have good potential.",
    "Keep learning and improving."
]

INSULTS = [
    "Your Wi-Fi has more intelligence than your router.",
    "You're running on Internet Explorer energy.",
    "Your brain is buffering."
]


async def on_message(room, event):
    global START_TIME_MS

    if event.sender == USER_ID:
        return

    if event.server_timestamp < START_TIME_MS:
        return

    body = event.body.strip()
    if not body.startswith("!"):
        return

    parts = body.split()
    command = parts[0].lower()
    args = parts[1:]
    room_id = room.room_id
    sender = event.sender

    # Ignore unknown commands: they do not earn points.
    if command not in COMMANDS:
        return

    # One point for every recognized command.
    scores[sender] = scores.get(sender, 0) + 1
    save_scores()

    try:
        if command == "!help":
            await reply(client, room_id,
                "Commands:\n" + " ".join(sorted(COMMANDS)) +
                "\nEvery recognized command earns 1 point.")

        elif command == "!ping":
            await reply(client, room_id, "Pong!")

        elif command == "!points":
            await reply(client, room_id,
                f"{sender} has {scores.get(sender, 0)} points.")

        elif command == "!leaderboard":
            ranking = sorted(
                scores.items(),
                key=lambda item: item[1],
                reverse=True
            )[:10]

            lines = ["🏆 Leaderboard:"]
            for i, (user, points) in enumerate(ranking, 1):
                lines.append(f"{i}. {user}: {points} points")

            await reply(client, room_id, "\n".join(lines))

        elif command == "!uptime":
            seconds = max(0, int(time.time() - START_TIME_MS / 1000))
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            await reply(client, room_id,
                f"Running for {hours}h {minutes}m {seconds}s.")

        elif command == "!coin":
            await reply(client, room_id, random.choice(["Heads!", "Tails!"]))

        elif command == "!flip":
            await reply(client, room_id, random.choice(["Heads!", "Tails!"]))

        elif command == "!dice":
            await reply(client, room_id, f"You rolled {random.randint(1, 6)}.")

        elif command == "!roll":
            sides = int(args[0]) if args else 6
            if not 2 <= sides <= 1000000:
                raise ValueError("Choose between 2 and 1,000,000 sides.")
            await reply(client, room_id, f"You rolled {random.randint(1, sides)}.")

        elif command == "!random":
            if len(args) < 2:
                await reply(client, room_id, "Usage: !random MIN MAX")
            else:
                low, high = int(args[0]), int(args[1])
                if low > high:
                    low, high = high, low
                await reply(client, room_id, str(random.randint(low, high)))

        elif command == "!choose":
            if not args:
                await reply(client, room_id, "Usage: !choose option1, option2, option3")
            else:
                options = [x.strip() for x in " ".join(args).split(",") if x.strip()]
                if len(options) < 2:
                    await reply(client, room_id, "Give me at least two comma-separated options.")
                else:
                    await reply(client, room_id, f"I choose: {random.choice(options)}")

        elif command == "!8ball":
            await reply(client, room_id, random.choice([
                "Definitely.", "Probably.", "Ask again later.",
                "Not looking good.", "Absolutely not.", "It is uncertain."
            ]))

        elif command == "!rate":
            subject = " ".join(args) or sender
            await reply(client, room_id,
                f"I rate {subject} {random.randint(0, 100)}/100.")

        elif command == "!ship":
            if len(args) < 2:
                await reply(client, room_id, "Usage: !ship NAME1 NAME2")
            else:
                await reply(client, room_id,
                    f"{args[0]} + {args[1]} = {random.randint(0, 100)}% compatibility.")

        elif command == "!joke":
            await reply(client, room_id, random.choice(JOKES))

        elif command == "!fact":
            await reply(client, room_id, random.choice(FACTS))

        elif command == "!trivia":
            question, answers = random.choice(TRIVIA)
            await reply(client, room_id,
                f"Trivia: {question}\nAnswer: {answers[0]}")

        elif command == "!rps":
            if not args or args[0].lower() not in ["rock", "paper", "scissors"]:
                await reply(client, room_id, "Usage: !rps rock, !rps paper, or !rps scissors")
            else:
                user_choice = args[0].lower()
                bot_choice = random.choice(["rock", "paper", "scissors"])
                if user_choice == bot_choice:
                    result = "It's a tie!"
                elif (user_choice, bot_choice) in [
                    ("rock", "scissors"),
                    ("paper", "rock"),
                    ("scissors", "paper")
                ]:
                    result = "You win!"
                else:
                    result = "I win!"
                await reply(client, room_id,
                    f"You chose {user_choice}; I chose {bot_choice}. {result}")

        elif command == "!number":
            await reply(client, room_id, f"Random number: {random.randint(1, 100)}")

        elif command == "!password":
            length = int(args[0]) if args else 16
            if not 4 <= length <= 128:
                raise ValueError("Password length must be between 4 and 128.")
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = "".join(random.choice(alphabet) for _ in range(length))
            await reply(client, room_id, f"Generated password: {password}")

        elif command == "!uuid":
            await reply(client, room_id, str(uuid.uuid4()))

        elif command == "!guess":
            key = f"{room_id}:{sender}"
            if not args:
                guess_games[key] = random.randint(1, 20)
                await reply(client, room_id, "I'm thinking of a number from 1 to 20. Use !guess NUMBER.")
            else:
                if key not in guess_games:
                    await reply(client, room_id, "Start a game first with !guess.")
                else:
                    guess = int(args[0])
                    target = guess_games[key]
                    if guess == target:
                        del guess_games[key]
                        await reply(client, room_id, "Correct! You got it.")
                    elif guess < target:
                        await reply(client, room_id, "Too low!")
                    else:
                        await reply(client, room_id, "Too high!")

        elif command == "!reverse":
            await reply(client, room_id, " ".join(args)[::-1])

        elif command == "!upper":
            await reply(client, room_id, " ".join(args).upper())

        elif command == "!lower":
            await reply(client, room_id, " ".join(args).lower())

        elif command == "!mock":
            text = " ".join(args)
            await reply(client, room_id,
                "".join(c.upper() if i % 2 else c.lower()
                        for i, c in enumerate(text)))

        elif command == "!clap":
            await reply(client, room_id, " 👏 ".join(args))

        elif command == "!spoiler":
            await reply(client, room_id, f"||{' '.join(args)}||")

        elif command == "!count":
            await reply(client, room_id, f"Word count: {len(' '.join(args).split())}")

        elif command == "!vowels":
            text = " ".join(args)
            await reply(client, room_id,
                f"Vowels: {sum(c.lower() in 'aeiou' for c in text)}")

        elif command == "!length":
            await reply(client, room_id, f"Length: {len(' '.join(args))} characters.")

        elif command == "!repeat":
            if not args:
                await reply(client, room_id, "Usage: !repeat TEXT")
            else:
                await reply(client, room_id, " ".join(args))

        elif command == "!emojify":
            replacements = {
                "happy": "happy 😊",
                "sad": "sad 😢",
                "love": "love ❤️",
                "fire": "fire 🔥",
                "cool": "cool 😎",
                "cat": "cat 🐱",
                "dog": "dog 🐶"
            }
            text = " ".join(args)
            for word, replacement in replacements.items():
                text = text.replace(word, replacement)
                text = text.replace(word.capitalize(), replacement)
            await reply(client, room_id, text)

        elif command == "!sqrt":
            if not args:
                await reply(client, room_id, "Usage: !sqrt NUMBER")
            else:
                value = float(args[0])
                if value < 0:
                    raise ValueError("Number must be non-negative.")
                await reply(client, room_id, str(math.sqrt(value)))

        elif command == "!percent":
            if len(args) < 2:
                await reply(client, room_id, "Usage: !percent VALUE TOTAL")
            else:
                value, total = float(args[0]), float(args[1])
                if total == 0:
                    raise ValueError("Total cannot be zero.")
                await reply(client, room_id, f"{value / total * 100:.2f}%")

        elif command == "!table":
            if not args:
                await reply(client, room_id, "Usage: !table NUMBER")
            else:
                n = int(args[0])
                if not 1 <= n <= 10000:
                    raise ValueError("Choose a number from 1 to 10,000.")
                await reply(client, room_id,
                    "\n".join(f"{n} × {i} = {n * i}" for i in range(1, 11)))

        elif command == "!binary":
            await reply(client, room_id,
                " ".join(format(ord(c), "08b") for c in " ".join(args)))

        elif command == "!unbinary":
            bits = "".join(args).replace(" ", "")
            if not bits or any(c not in "01" for c in bits) or len(bits) % 8:
                raise ValueError("Provide binary in groups of 8 bits.")
            decoded = bytes(
                int(bits[i:i + 8], 2)
                for i in range(0, len(bits), 8)
            ).decode("utf-8")
            await reply(client, room_id, decoded)

        elif command == "!hex":
            await reply(client, room_id, " ".join(args).encode().hex())

        elif command == "!unhex":
            await reply(client, room_id,
                bytes.fromhex(" ".join(args)).decode("utf-8"))

        elif command == "!compliment":
            await reply(client, room_id, random.choice(COMPLIMENTS))

        elif command == "!insult":
            await reply(client, room_id, random.choice(INSULTS))

    except (ValueError, OverflowError, UnicodeDecodeError) as e:
        await reply(client, room_id, f"Error: {e}")
    except Exception as e:
        print(f"Command error ({command}): {e}")


async def main():
    global client, START_TIME_MS, scores

    scores = load_scores()

    client = AsyncClient(HOMESERVER, USER_ID)
    password = os.environ.get("MATRIX_PASSWORD")

    if not password:
        raise RuntimeError("MATRIX_PASSWORD secret is missing")

    response = await client.login(password)
    if not hasattr(response, "access_token"):
        print(f"Login failed: {response}")
        await client.close()
        return

    print("Logged in successfully.")
    client.add_event_callback(on_message, RoomMessageText)

    await client.sync(timeout=30000)
    START_TIME_MS = int(time.time() * 1000)

    print("Bot is running.")
    try:
        await client.sync_forever(timeout=30000)
    finally:
        save_scores()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
