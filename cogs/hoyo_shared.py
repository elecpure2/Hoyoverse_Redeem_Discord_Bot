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

def clean_description(text: str, params=None) -> str:
    if not text:
        return ""
    
    # 0. ZZZ IconMap tags -> emoji mapping
    icon_map = {
        'Icon_Normal': '⚔️',
        'Icon_Special': '🔷',
        'Icon_SpecialReady': '🔷',
        'Icon_Evade': '💨',
        'Icon_QTE': '⚡',
        'Icon_UltimateReady': '💥',
        'Icon_Switch': '🔄',
    }
    for icon_key, emoji in icon_map.items():
        text = text.replace(f'<IconMap:{icon_key}>', emoji)
    
    # 1. HTML/color tags removal using regex
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. Param replacement if provided
    if params:
        def replace_param(match):
            idx = int(match.group(1)) - 1
            algo = match.group(2) # i, f1, P, etc
            percent = match.group(3) # % or empty

            if 0 <= idx < len(params):
                val = params[idx]
                
                # Handle non-numeric params (strings from ZZZ API)
                if isinstance(val, str):
                    return val + percent
                
                # HSR/ZZZ convention: if tag has %, multiply by 100
                # But only if value looks like a ratio (< 1)
                if percent == '%' and isinstance(val, (int, float)):
                    if val < 1:
                        val *= 100
                    
                # Formatting
                if algo == 'i':
                    return f"{int(round(val))}" + percent
                elif algo == 'f1':
                    return f"{val:.1f}" + percent
                elif algo == 'P':
                    # ZZZ uses P for percentage values (already multiplied)
                    return f"{val:.1f}" + percent
                else:
                    if isinstance(val, float):
                        return f"{val:.1f}" + percent
                    return f"{val}" + percent
            return match.group(0)

        # Regex to match #1[i], #1[i]%, #1[P]% etc
        text = re.sub(r'#(\d+)\[([a-zA-Z0-9]+)\](%?)', replace_param, text)
    
    # Strip {LINK...} parsing
    text = re.sub(r'\{LINK#.+?\}(.+?)\{/LINK\}', r'\1', text)
    
    # 3. Newline fixes (HSR literal \n)
    text = text.replace(r'\n', '\n')
    
    # 4. Clean up multiple spaces/newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
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
