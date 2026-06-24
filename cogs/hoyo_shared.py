import discord
from discord.ui import View, Select
import re

# Import Enums from hakushin if available, else define them?
# The bot seems to require hakushin, so we keep using it for Enums to minimize breakage.
try:
    from hakushin import Game, Language
except ImportError:
    # Fallback if library missing (though unlikely given setup)
    from enum import Enum
    class Game(Enum):
        GI = "genchin" # library actually uses 'genshin' as value? 
        # Actually let's assume library is present as per imports in upcoming.py
        # But if we want to decouple, we can define our own.
        # Let's import for now.
        pass

# Constants from upcoming.py
GAME_COLORS = {
    Game.GI: 0x00D7FA, # Cyan-ish
    Game.HSR: 0xFFD700, # Gold
    Game.ZZZ: 0xFFA500  # Orange
}

GAME_URLS = {
    Game.GI: "gi",
    Game.HSR: "hsr",
    Game.ZZZ: "zzz"
}

# ZZZ 스킬 아이콘 태그 -> 이모지
ICONMAP_EMOJI = {
    'Icon_Normal': '⚔️', 'Icon_Special': '🔷', 'Icon_SpecialReady': '🔷',
    'Icon_Evade': '💨', 'Icon_QTE': '⚡', 'Icon_UltimateReady': '💥',
    'Icon_Ultimate': '💥', 'Icon_Switch': '🔄', 'Icon_Assist': '🤝',
    'Icon_Dodge': '💨', 'Icon_Chain': '⛓️',
}


def _fmt_param(value, decimals: int, percent: bool) -> str:
    """파라미터 값을 포맷. percent=True 면 ×100 후 % 표기."""
    if isinstance(value, str):
        return value + ("%" if percent else "")
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if percent:
        v *= 100
    if decimals <= 0:
        s = f"{int(round(v))}"
    else:
        s = f"{v:.{decimals}f}".rstrip('0').rstrip('.')
        if not s or s == '-0':
            s = '0'
    return s + ("%" if percent else "")


def clean_description(text: str, params=None) -> str:
    """스킬/무기/돌파 설명 정리.

    - HSR 스타일 `#N[fmt]%` 와 GI 스타일 `{paramN:FMT}` 플레이스홀더를 params 로 치환
      (`%`/`P` 포맷은 항상 ×100). params 없거나 범위 밖이면 깔끔히 제거.
    - `{LINK#...}{/LINK}`, `<color>`/`<unbreak>`/`<IconMap>` 등 태그 제거.
    """
    if not text:
        return ""

    # IconMap -> 이모지
    text = re.sub(r'<IconMap:([^>]+)>', lambda m: ICONMAP_EMOJI.get(m.group(1), ''), text)

    if params:
        # HSR: #N[i] / #N[f1] / #N[i]%
        def _hsr(m):
            idx = int(m.group(1)) - 1
            fmt = m.group(2).lower()
            pct = m.group(3) == '%'
            if 0 <= idx < len(params):
                dec = 0 if fmt.startswith('i') else (int(fmt[1:]) if len(fmt) > 1 and fmt[1:].isdigit() else 1)
                return _fmt_param(params[idx], dec, pct)
            return ''
        text = re.sub(r'#(\d+)\[([a-zA-Z]\d?)\](%?)', _hsr, text)

        # GI: {paramN:F1P} / {paramN:F1} / {paramN:P} / {paramN:I}
        def _gi(m):
            idx = int(m.group(1)) - 1
            fmt = m.group(2)
            if 0 <= idx < len(params):
                pct = 'P' in fmt.upper()
                dm = re.search(r'[Ff](\d)', fmt)
                dec = int(dm.group(1)) if dm else (0 if fmt.upper().startswith('I') else 1)
                return _fmt_param(params[idx], dec, pct)
            return ''
        text = re.sub(r'\{param(\d+):([A-Za-z0-9]+)\}', _gi, text)

    # LINK 태그 제거 (내부 텍스트는 유지)
    text = re.sub(r'\{LINK#[^}]*\}', '', text)
    text = text.replace('{/LINK}', '')
    # < > 태그 제거 (color, unbreak 등)
    text = re.sub(r'<[^>]+>', '', text)
    # 미치환 잔여 플레이스홀더 제거
    text = re.sub(r'#\d+\[[^\]]*\]%?', '', text)
    text = re.sub(r'\{param\d+:[^}]*\}', '', text)
    text = re.sub(r'\{/?[A-Za-z][^}]*\}', '', text)

    # 줄바꿈/공백 정리
    text = text.replace('\\n', '\n')
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

class HoyoSelectView(View):
    def __init__(self, cog, results, default_game, default_game_name, type_str):
        super().__init__(timeout=60)
        self.cog = cog
        self.type_str = type_str
        self.message = None
        self.results_map = {}  # Store results for lookup
        
        options = []
        for res in results:
            # Handle both dict and object (SimpleNamespace)
            if isinstance(res, dict):
                name = res.get('name')
                rid = res.get('id')
                game_val = res.get('game').value if res.get('game') else default_game.value
                gname = res.get('game_name') or default_game_name
            else:
                name = getattr(res, 'name', '?')
                rid = getattr(res, 'id', '?')
                # Objects from 'new items' usually don't have game info, use default
                game_val = getattr(res, 'game', default_game).value
                gname = getattr(res, 'game_name', default_game_name)

            option_key = f"{game_val}_{rid}"
            self.results_map[option_key] = {'name': name, 'id': rid, 'game_val': game_val, 'game_name': gname}
            
            options.append(discord.SelectOption(
                label=f"{gname} - {name}",
                value=option_key,
                description=f"{gname}에서 결과 확인"
            ))
            
        select = Select(placeholder="게임을 선택해주세요", options=options[:25])
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        select = self.children[0]
        val = select.values[0]
        
        # Get stored result data
        result_data = self.results_map.get(val, {})
        game_val = result_data.get('game_val', '')
        item_id = result_data.get('id', '')
        item_name = result_data.get('name', '')
        game_name = result_data.get('game_name', '')
        
        # Find Game enum by value
        selected_game = None
        for g in Game:
            if str(g.value) == game_val:
                selected_game = g
                break
        
        if not game_name:
            game_name = "원신" if selected_game == Game.GI else "스타레일" if selected_game == Game.HSR else "젠레스 존 제로"
        
        # Call appropriate show method based on type_str
        if self.type_str == 'character':
            await self.cog._show_character_detail_by_id(interaction, item_id, selected_game, game_name)
        elif self.type_str == 'weapon':
            await self.cog._show_weapon_detail_by_id(interaction, item_id, selected_game, game_name)
        elif self.type_str == 'artifact':
             if hasattr(self.cog, '_show_artifact_detail_by_id'):
                 await self.cog._show_artifact_detail_by_id(interaction, item_id, selected_game, game_name, item_name)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except:
                pass


class GameSelectView(discord.ui.View):
    """View for selecting which game to view upcoming content for."""
    def __init__(self, cog, content_type: str, timeout=60):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.content_type = content_type  # 'character', 'weapon', 'artifact'
        self.message = None
        
        # Add buttons for each game
        games = [
            (Game.GI, "원신", discord.ButtonStyle.primary),
            (Game.HSR, "스타레일", discord.ButtonStyle.secondary),
            (Game.ZZZ, "젠레스 존 제로", discord.ButtonStyle.danger) 
        ]
        
        for game, name, style in games:
            button = discord.ui.Button(label=name, style=style)
            button.callback = self.make_callback(game, name)
            self.add_item(button)
    
    def make_callback(self, game, game_name: str):
        async def callback(interaction: discord.Interaction):
            try:
                await interaction.response.defer()
                for child in self.children:
                    child.disabled = True
                if self.message:
                    await self.message.edit(view=self)
                
                if self.content_type == 'character':
                    if hasattr(self.cog, '_show_new_characters'):
                        await self.cog._show_new_characters(interaction, game, game_name)
                elif self.content_type == 'weapon':
                    if hasattr(self.cog, '_show_new_weapons'):
                        await self.cog._show_new_weapons(interaction, game, game_name)
                elif self.content_type == 'artifact':
                    if hasattr(self.cog, '_show_new_artifacts'):
                        await self.cog._show_new_artifacts(interaction, game, game_name)
                        
            except Exception as e:
                print(f"[GameSelectView] Callback error: {e}")
        return callback
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass
