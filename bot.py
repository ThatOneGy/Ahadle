import discord
import json
import random
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

with open('lifers.json', 'r') as f:
    lifers = json.load(f)

current_games = {}

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()
    channel_id = message.channel.id

    if content.lower() == '!start':
        if channel_id in current_games:
            await message.channel.send("A game is already running! Use !guess <name> to guess.")
            return

        lifer = random.choice(lifers)
        current_games[channel_id] = {
            'lifer': lifer,
            'wrong_guesses': 0,
            'hint_given': False
        }

        series_count = len(lifer['series'])
        subs = lifer['subs']

        clues = (f"🎲 Guess the Lifer!\n"
                 f"Series count: {series_count}\n"
                 f"Approx subs: {subs}\n"
                 f"Use !guess <name> to guess!")

        await message.channel.send(clues)

    elif content.lower().startswith('!guess'):
        if channel_id not in current_games:
            await message.channel.send("No game running! Type !start to begin.")
            return

        parts = content.split(maxsplit=1)
        if len(parts) < 2:
            await message.channel.send("Please provide a name to guess, e.g. `!guess Grian`")
            return

        guess = parts[1].strip().lower()
        game = current_games[channel_id]
        lifer = game['lifer']
        correct_name = lifer['name'].lower()

        print(f"User guessed: {guess}")
        print(f"Correct lifer: {correct_name}")

        if guess == correct_name:
            await message.channel.send(f"✅ Correct! It was {lifer['name']}! 🎉")
            del current_games[channel_id]
        else:
            game['wrong_guesses'] += 1

            # Try exact match first
            guess_lifer = next((l for l in lifers if l['name'].lower() == guess), None)

            # Fuzzy fallback: check if guess is substring of any lifer name
            if not guess_lifer:
                guess_lifer = next((l for l in lifers if guess in l['name'].lower()), None)

            print(f"Guess lifer found: {guess_lifer['name'] if guess_lifer else None}")

            sub_hint = ""
            series_hint = ""
            if guess_lifer:
                # Subscriber hint
                if guess_lifer['subs'] < lifer['subs']:
                    sub_hint = "Subs ⬆"
                elif guess_lifer['subs'] > lifer['subs']:
                    sub_hint = "Subs ⬇️"
                else:
                    sub_hint = ""

                # Series hint
                guess_series_count = len(guess_lifer['series'])
                correct_series_count = len(lifer['series'])
                if guess_series_count < correct_series_count:
                    series_hint = " They've been in **more** series."
                elif guess_series_count > correct_series_count:
                    series_hint = " They've been in **fewer** series."
                else:
                    series_hint = " They've been in the same number of series."

            await message.channel.send(f"❌ Wrong! {sub_hint}{series_hint} Try again!")

            if game['wrong_guesses'] == 3 and not game['hint_given']:
                hint = lifer['notes'][0] if lifer['notes'] else "No hints available."
                await message.channel.send(f"💡 Hint: {hint}")
                game['hint_given'] = True

client.run(TOKEN)
