import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

class Player:
    def __init__(self, member):
        self.member = member
        self.position = 0
        self.coins = 0
        self.treasure = 0
        self.skip = False
        self.retired = False

board = [
    "スタート",
    "コイン+100",
    "1マス戻る",
    "次回休み",
    "コイン+30",
    "宝箱！",
    "コイン-50",
    "お宝の気配（何もなし）",
    "2マス進む",
    "宝箱！",
    "コイン+150",
    "ランダムで誰かと位置交換",
    "1マス戻る",
    "コイン+70",
    "フィーバー！コインx2",
    "ゴール！"
]
GOAL = len(board) - 1

game_data = {}

class JoinView(discord.ui.View):
    def __init__(self, host):
        super().__init__(timeout=60)
        self.host = host
        self.player_ids = set()
        self.players = []
        self.started = False

    @discord.ui.button(label="参加！", style=discord.ButtonStyle.primary)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.player_ids:
            await interaction.response.send_message("すでに参加しています！", ephemeral=True)
            return
        self.player_ids.add(interaction.user.id)
        self.players.append(Player(interaction.user))
        await interaction.response.send_message(f"{interaction.user.mention}が参加しました。", ephemeral=True)

    @discord.ui.button(label="開始！", style=discord.ButtonStyle.success)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("主催者だけが開始できます。", ephemeral=True)
            return
        if len(self.players) < 2:
            await interaction.response.send_message("2人以上必要です。", ephemeral=True)
            return
        self.started = True
        self.stop()
        await interaction.response.send_message("ゲーム開始！", ephemeral=False)

@bot.tree.command(name="startgame", description="すごろくゲームを開始")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def startgame(interaction: discord.Interaction):
    if game_data.get('playing', False):
        await interaction.response.send_message("既にゲーム中です！", ephemeral=True)
        return
   view = JoinView(interaction.user)
    msg = await interaction.response.send_message("すごろく参加者募集中！ ボタンで参加→開始", view=view, ephemeral=False)
    await view.wait()  # ボタン待機（1分または開始時点でstop）
    if not view.started:
        await interaction.followup.send("締切になりました。開始されませんでした。")
        return
    # playersリストを決定し、ゲーム開始!
    game_data["playing"] = True
    game_data["players"] = view.players
    game_data["turn"] = 0

    await next_turn(interaction.channel)

async def board_status():
    lines = []
    for p in game_data.get("players", []):
        if not p.retired:
            lines.append(f"{p.member.display_name}: マス{p.position}, コイン{p.coins}, 宝箱{p.treasure}")
    return "■進行状況\n" + "\n".join(lines)

async def next_turn(channel):
    # アクティブ参加者
    active_players = [p for p in game_data["players"] if not p.retired]
    if not active_players:
        await channel.send("全員脱落でゲーム終了！")
        game_data.clear()
        return
    turn = game_data["turn"] % len(active_players)
    cur_player = active_players[turn]
    if cur_player.skip:
        await channel.send(f"{cur_player.member.mention}は今回は休みです！")
        cur_player.skip = False
        game_data["turn"] += 1
        await next_turn(channel)
        return

    class TurnView(discord.ui.View):
        @discord.ui.button(label="サイコロを振る", style=discord.ButtonStyle.primary)
        async def roll_btn(self, interaction: discord.Interaction, b):
            if interaction.user != cur_player.member:
                await interaction.response.send_message("あなたの番ではありません。", ephemeral=True)
                return
            await interaction.response.defer(thinking=True)
            dice = random.randint(1, 6)
            await interaction.followup.send(f"{cur_player.member.mention}のサイコロ：{dice}")
            await sugoroku_action(channel, cur_player, dice)
            self.stop()
        @discord.ui.button(label="脱落", style=discord.ButtonStyle.danger)
        async def retire_btn(self, interaction: discord.Interaction, b):
            if interaction.user != cur_player.member:
                await interaction.response.send_message("あなたの番ではありません。", ephemeral=True)
                return
            cur_player.retired = True
            await interaction.response.send_message(f"{cur_player.member.mention}が脱落しました。")
            self.stop()
            # turnを進めて次へ
            game_data["turn"] += 1
            await next_turn(channel)

    await channel.send(f"----------------\n{cur_player.member.mention}の番!\n{await board_status()}", view=TurnView())

async def sugoroku_action(channel, player, dice):
    player.position += dice
    if player.position >= GOAL:
        await channel.send(f"🏁 {player.member.mention}がゴール！クリア！\n結果:\n{await board_status()}")
        game_data.clear()
        return
   effect = board[player.position]
    effmsg = ""
    if effect == "コイン+100":
        player.coins += 100; effmsg = "+100コイン！"
    elif effect == "コイン+30":
        player.coins += 30; effmsg = "+30コイン！"
    elif effect == "コイン-50":
        player.coins -= 50; effmsg = "-50コイン…"
    elif effect == "1マス戻る":
        player.position = max(0, player.position - 1); effmsg = "1マス戻る！"
    elif effect == "2マス進む":
        player.position = min(GOAL - 1, player.position + 2); effmsg = "さらに2マス進む！"
    elif effect == "宝箱！":
        player.treasure += 1; player.coins += random.randint(30, 200); effmsg = "宝箱ゲット！"
    elif effect == "フィーバー！コインx2":
        player.coins *= 2; effmsg = "コイン2倍！"
    elif effect == "次回休み":
        player.skip = True; effmsg = "次回お休み！"
    elif effect == "ランダムで誰かと位置交換":
        others = [p for p in game_data["players"] if p != player and not p.retired]
        if others:
            target = random.choice(others)
            player.position, target.position = target.position, player.position
            effmsg = f"{target.member.display_name}と位置を交換！"
    elif effect == "お宝の気配（何もなし）":
        effmsg = "…何もなし！"

    await channel.send(f"{player.member.mention}は{player.position}マス目 ({effect}) に到着!\n{effmsg}\n「/retire」でも途中脱落可能！")
    game_data["turn"] += 1
    await next_turn(channel)

@bot.tree.command(name="retire", description="ゲームから脱落します")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def retire(interaction: discord.Interaction):
    if not game_data.get("playing"):
        await interaction.response.send_message("開催中のゲームがありません。", ephemeral=True)
        return
    found = False
    for player in game_data["players"]:
        if player.member == interaction.user:
            if player.retired:
                await interaction.response.send_message("すでに脱落済みです。", ephemeral=True)
                return
            player.retired = True
            found = True
            await interaction.response.send_message(f"{interaction.user.mention}が脱落しました。")
    if not found:
        await interaction.response.send_message("ゲーム参加者ではありません。", ephemeral=True)

@bot.event
async def on_ready():
    print("Ready!")
    # GUILD_ID部分を正しく設定して下さい
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

bot.run(TOKEN)
