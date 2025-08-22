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

effect_master = [
    "スタート！",
    "コイン+200",
    "落とし穴！1マス戻る",
    "推しのライブに当選！コイン+150",
    "宝箱発見！コイン+ランダム",
    "バズった！全員コイン+50",
    "バイト代日 コイン+120",
    "フォロワー1万人突破！コイン+300",
    "猫に癒やされ1回休み",
    "推しが卒業…コイン-100",
    "新作ガチャ爆死…コイン-80",
    "合格発表！2マス進む",
    "SNSで炎上…次回休み",
    "手作りおにぎり大成功！コイン+30",
    "推しカフェ巡り コイン-50",
    "ゾンビ映画主演！コイン+60",
    "推しにファンサもらう！コイン+70",
    "サウナで整う コイン+20",
    "アカウント凍結…コイン-120",
    "恋愛ドラマに出演2マス進む",
    "大雨で寝坊！1回休み",
    "支払い忘れ…コイン-60",
    "鬼滅の刃全巻読破コイン+50",
    "課金爆死コイン-120",
    "オールでカラオケコイン-40",
    "筋トレ継続 コイン+40",
    "推しのアクリルスタンド破損コイン-30",
    "ドリンク1杯無料クーポン！コイン+10",
    "宝くじ1等！コイン+500",
    "すべって転倒、1マス戻る",
    "転職成功 コイン+200",
    "ダブルピースで写真映え！コイン+20",
    "迷子…2マス戻る",
    "友人と大喧嘩コイン-100",
    "猫カフェでリラックス コイン+30",
    "推しの結婚発表 コイン-200",
    "体育祭リレー優勝！コイン+70",
    "ワクチン副反応…次回休み",
    "深夜アニメで夜更かしコイン-30",
    "目覚まし聞き逃し1回休み",
    "大掃除でお宝発見！コイン+70",
    "間違い電話で恥ずかしい思いコイン-20",
    "マクドナルドのポテトL当選 コイン+20",
    "お年玉をもらう コイン+80",
    "推し似のイケメン・美女と遭遇2マス進む",
    "転校生と意気投合 コイン+30",
    "ファミチキ争奪ジャンケンコイン+50",
    "LINE誤爆コイン-20",
    "大雨でスマホ壊滅 コイン-150",
    "好きな人に告白される！2マス進む",
    "スポーツ大会最下位…1マス戻る",
    "Amazonギフト当選 コイン+60",
    "推しがTwitterでリプ返 コイン+40",
    "一目惚れで運命感じる！コイン+20",
    "定期券紛失…コイン-70",
    "宿題忘れて先生に叱られるコイン-30",
    "推しと同じクラスになる！コイン+80",
    "席替えで神席！1マス進む",
    "深夜テンションで爆買いコイン-100",
    "推しキャラの誕生日イベント参加コイン+40",
    "SNSハッキング被害コイン-100",
    "LINEがバグりまくる1回休み",
    "牛丼並盛無料券 コイン+10",
    "推しの新商品に出費コイン-60",
    "友達の誕生日パーティコイン-50",
    "突然のプレゼント コイン+90",
    "サプライズ逆ドッキリコイン+30",
    "猫の動画で癒やし コイン+10",
    "推しのサイン入りグッズGET！コイン+120",
    "仕事で大ミス…コイン-80",
    "バイト先で神対応し褒められる！コイン+50",
    "夜食カップラーメンで胃もたれコイン-20",
    "宝箱：レアアイテムGET！",
    "ゲーム実況で人気者！コイン+70",
    "寝坊して朝ごはん抜きコイン-10",
    "迷惑メール大量受信コイン-20",
    "バレンタインチョコの山 コイン+30",
    "推しカプ大逆転！コイン+50",
    "特売セールに並ぶコイン-20",
    "冷凍ピザにソースかけ忘れコイン-5",
    "アンチからの粘着コイン-30",
    "YouTubeショートでバズるコイン+90",
    "さっぽろ雪まつり見物1マス進む",
    "好きなラーメン屋閉店コイン-60",
    "路上ライブ大成功コイン+40",
    "英会話レッスン1回無料コイン+20",
    "推しと同じ星座でテンションUP！1マス進む",
    "寝違えて首が痛い…1回休み",
    "100万回の「いいね」コイン+100",
    "月見バーガー発売で大興奮コイン+30",
    "インスタのリール動画大成功！コイン+40",
    "推しアプリ新作リリース コイン+50",
    "バスに乗り遅れ1マス戻る",
    "母親の手料理！コイン+40",
    "フリマアプリで不用品売却コイン+60",
    "プリンを冷蔵庫で発見コイン+10",
    "推しのLINE着せ替え配信コイン+30",
    "友人との友情復活コイン+20",
    "MV動画が世界で話題コイン+120",
    "ラジオで名前を読まれるコイン+80",
    "超人気イベント当選！2マス進む",
    "有給消化大成功コイン+40",
    "レジェンド級神引き！コイン+200",
    "永久無料パスポート当選コイン+300",
    "ゴール！！！"
]
def create_board():
    # 50個ランダム選出（重複なし）
    chosen_events = random.sample(effect_master, 50)
    # 盤面リスト: 0=スタート, 1~50=イベント, 51=ゴール
    return ["スタート"] + chosen_events + ["ゴール!!!"]

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
