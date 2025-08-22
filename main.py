import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

class Player:
    def __init__(self, member):
        self.member = member
        self.position = 0
        self.coins = 0
        self.treasure = 0
        self.skip = False
        self.retired = False

# ボード内容
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

game_data = {
    "playing": False,
    "players": [],
    "turn": 0,
    "current_msg": None,
}

### スラッシュコマンド「/startgame」
@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="startgame", description="すごろくゲームを開始します")
async def startgame(interaction: discord.Interaction):
    if game_data["playing"]:
        await interaction.response.send_message("既にゲーム中です！", ephemeral=True)
        return

    game_data["playing"] = True
    game_data["players"] = []
    game_data["turn"] = 0

    # 参加ボタンを表示
    class JoinView(discord.ui.View):
        @discord.ui.button(label="参加！", style=discord.ButtonStyle.primary)
        async def join(self, btn, inter):
            if any(p.member == inter.user for p in game_data["players"]):
                await inter.response.send_message("既に参加しています！", ephemeral=True)
                return
            player = Player(inter.user)
            game_data["players"].append(player)
            await inter.response.send_message(f"{inter.user.mention}さん参加！", ephemeral=True)

        @discord.ui.button(label="開始！", style=discord.ButtonStyle.success)
        async def start_btn(self, btn, inter):
            if len(game_data["players"]) < 2:
                await inter.response.send_message("2人以上必要です！", ephemeral=True)
                return
            await inter.response.defer()
            await inter.followup.send("ゲーム開始！")
            await next_turn(inter.channel)

    await interaction.response.send_message("すごろく参加者を募集します。最大1分。\nボタンで参加してください。", view=JoinView())


async def board_status():
    lines = []
    for player in game_data["players"]:
        if player.retired: continue
        stat = f"{player.member.display_name}: マス{player.position}（コイン{player.coins}、宝箱{player.treasure}）"
        lines.append(stat)
    return "■現状\n" + "\n".join(lines)


async def next_turn(channel):
    # 脱落者を除外
    active_players = [p for p in game_data["players"] if not p.retired]
    if len(active_players)==0:
        await channel.send("全員脱落でゲーム終了！")
        game_data["playing"]=False
        return
    cur_player = active_players[game_data["turn"] % len(active_players)]
    if cur_player.skip:
        await channel.send(f"{cur_player.member.mention}は今回お休み。")
        cur_player.skip = False
        game_data["turn"] += 1
        await next_turn(channel)
        return

    # サイコロ＆脱落ボタン
    class RollView(discord.ui.View):
        @discord.ui.button(label="サイコロを振る", style=discord.ButtonStyle.primary)
        async def roll_btn(self, btn, inter):
            if inter.user != cur_player.member:
                await inter.response.send_message("あなたの番ではありません。", ephemeral=True)
                return
            dice = random.randint(1, 6)
            await inter.response.send_message(f"{cur_player.member.mention}のサイコロ: {dice}！")
            await sugoroku_action(channel, cur_player, dice)
            self.stop()
        @discord.ui.button(label="脱落(リタイア)", style=discord.ButtonStyle.danger)
        async def retire_btn(self, btn, inter):
            if inter.user != cur_player.member:
                await inter.response.send_message("あなたの番ではありません。", ephemeral=True)
                return
            cur_player.retired = True
            await channel.send(f"{cur_player.member.mention}が脱落しました。")
            self.stop()
            game_data["turn"] += 1
            await next_turn(channel)

    msg = await channel.send(f"---\n{cur_player.member.mention}の番です。\n"+await board_status(),
                             view=RollView())
    game_data["current_msg"] = msg

async def sugoroku_action(channel, player, dice):
    # 移動
    player.position += dice
    if player.position >= GOAL:
        await channel.send(f"🏁 {player.member.mention}がゴール！おめでとう！\n最終結果：\n"+await board_status())
        game_data["playing"] = False
        return
    effect = board[player.position]
    effmsg = ""
    if effect == "コイン+100":
        player.coins += 100; effmsg = "+100コインゲット！"
    elif effect == "コイン+30":
        player.coins += 30; effmsg = "+30コインゲット！"
    elif effect == "コイン-50":
        player.coins -= 50; effmsg = "-50コイン…"
    elif effect == "1マス戻る":
        player.position = max(0, player.position-1); effmsg = "1マス戻る！"
    elif effect == "2マス進む":
        player.position = min(GOAL-1, player.position+2); effmsg = "さらに2マス進む！"
    elif effect == "宝箱！":
        player.treasure += 1; player.coins += random.randint(30,200); effmsg = "宝箱ゲット！何かいいことがある…"
    elif effect == "フィーバー！コインx2":
        player.coins *= 2; effmsg = "コインが2倍に！"
    elif effect == "次回休み":
        player.skip = True; effmsg = "次回おやすみ。"
    elif effect == "ランダムで誰かと位置交換":
        targets = [p for p in game_data["players"] if p != player and not p.retired]
        if targets:
            target = random.choice(targets)
            player.position, target.position = target.position, player.position
            effmsg = f"{target.member.display_name}と位置を入れ替え！"
    elif effect == "お宝の気配（何もなし）":
        effmsg = "…何もなし！"

    await channel.send(f"{player.member.mention}は{player.position}マス目({effect})に到着！\n{effmsg}\n"+await board_status())
    game_data["turn"] += 1
    await next_turn(channel)

### 脱落コマンド
@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="retire", description="ゲームからリタイアします")
async def retire(interaction: discord.Interaction):
    for player in game_data["players"]:
        if player.member == interaction.user and not player.retired:
            player.retired = True
            await interaction.response.send_message(f"{interaction.user.mention}が脱落しました。")
            return
    await interaction.response.send_message("参加していない/既に脱落済みです。", ephemeral=True)

### 宝探しチャレンジ（別ミニゲーム例）
@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="treasure", description="宝探しゲーム！")
async def treasure(interaction: discord.Interaction):
    text_channels = [ch for ch in interaction.guild.text_channels if ch.permissions_for(interaction.guild.me).send_messages]
    treasure_channel = random.choice(text_channels)
    hint_msg = f"宝物（コイン{random.randint(10,100)}）をどこかのチャンネルに隠しました。チャンネル名の最初の文字は「{treasure_channel.name[0]}」！\nどのチャンネルでしょう？"
    await interaction.response.send_message(hint_msg, ephemeral=True)
    await treasure_channel.send("🏆このチャンネルに最初に「/found」と書き込んだ人が宝ゲット！")

@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="found", description="宝探し発見！")
async def found(interaction: discord.Interaction):
    # 本来は状態を記憶して当たり判定・重複防止処理も
    await interaction.response.send_message("宝を見つけました！（今回は記念品のみです）", ephemeral=True)

### 起動
@bot.event
async def on_ready():
    print("ボット起動")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print("Slashコマンド同期失敗", e)

bot.run(TOKEN)
