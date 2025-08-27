import time
import random
import sqlite3
from typing import List, Callable, Optional, Any, NoReturn
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class EventArgs:
    """イベント引数の基底クラス"""
    pass


@dataclass
class RecipeEventArgs(EventArgs):
    """レシピイベントの引数クラス"""
    recipe: Optional['RecipeSO']
    success: bool
    message: str


class DeliveryError(Exception):
    """配達関連の例外基底クラス"""
    pass


class InvalidRecipeError(DeliveryError):
    """無効なレシピエラー"""
    pass


class Event:
    """C#のeventに相当するクラス"""
    
    def __init__(self):
        self._handlers: List[Callable] = []
    
    def add_handler(self, handler: Callable):
        """イベントハンドラーを追加"""
        if handler not in self._handlers:
            self._handlers.append(handler)
    
    def remove_handler(self, handler: Callable):
        """イベントハンドラーを削除"""
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def invoke(self, sender, args: EventArgs = None):
        """イベントを発火"""
        for handler in self._handlers:
            handler(sender, args or EventArgs())


@dataclass(frozen=True)
class KitchenObjectSO:
    """キッチンオブジェクトのデータクラス"""
    name: str
    object_id: int


@dataclass
class RecipeSO:
    """レシピのデータクラス"""
    name: str
    kitchen_object_so_list: List[KitchenObjectSO] = field(default_factory=list)


@dataclass
class RecipeListSO:
    """レシピリストのデータクラス"""
    recipe_so_list: List[RecipeSO] = field(default_factory=list)


class PlateKitchenObject:
    """皿のキッチンオブジェクト"""
    
    def __init__(self):
        self._kitchen_object_so_list: List[KitchenObjectSO] = []
    
    def add_kitchen_object(self, kitchen_object: KitchenObjectSO):
        """キッチンオブジェクトを追加"""
        self._kitchen_object_so_list.append(kitchen_object)
    
    def get_kitchen_object_so_list(self) -> List[KitchenObjectSO]:
        """キッチンオブジェクトリストを取得"""
        return self._kitchen_object_so_list.copy()


class RecipeSpawner:
    """レシピ生成を担当するクラス"""
    def __init__(self, recipe_list: RecipeListSO, max_waiting: int = 4,
                 spawn_interval: float = 4.0):
        self.recipe_list = recipe_list
        self.max_waiting = max_waiting
        self.spawn_interval = spawn_interval
        self.timer = 0.0
        
    def update(self, delta_time: float) -> Optional[RecipeSO]:
        """
        タイマーを更新し、必要に応じて新しいレシピを生成する
        
        Args:
            delta_time: 経過時間
            
        Returns:
            Optional[RecipeSO]: 新しいレシピ、または None
        """
        self.timer -= delta_time
        if self.timer <= 0:
            self.timer = self.spawn_interval
            return random.choice(self.recipe_list.recipe_so_list)
        return None


class KitchenGameManager:
    """キッチンゲームマネージャー（Singleton）"""
    
    _instance: Optional['KitchenGameManager'] = None
    
    def __init__(self):
        self._is_game_playing = False
    
    @classmethod
    def get_instance(cls) -> 'KitchenGameManager':
        """Singletonインスタンスを取得"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def is_game_playing(self) -> bool:
        """ゲームが進行中かどうか"""
        return self._is_game_playing
    
    def start_game(self):
        """ゲーム開始"""
        self._is_game_playing = True
    
    def stop_game(self):
        """ゲーム停止"""
        self._is_game_playing = False


class DeliveryManager:
    """配達管理クラス（Python版）"""
    
    _instance: Optional['DeliveryManager'] = None
    
    def __init__(self, recipe_list_so: RecipeListSO):
        # イベント定義
        self.on_recipe_spawned = Event()
        self.on_recipe_result = Event()  # success/failedを統合
        
        # 状態管理の分離
        self._recipe_spawner = RecipeSpawner(recipe_list_so)
        self._recipe_list_so = recipe_list_so
        self._waiting_recipe_so_list: List[RecipeSO] = []
        self._successful_recipes_amount = 0
        self._last_update_time = time.time()

    @classmethod
    def initialize(cls, recipe_list_so: RecipeListSO) -> 'DeliveryManager':
        """明示的な初期化メソッド"""
        if cls._instance is not None:
            raise RuntimeError("DeliveryManagerは既に初期化されています")
        cls._instance = cls(recipe_list_so)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'DeliveryManager':
        """インスタンス取得（初期化済みの場合のみ）"""
        if cls._instance is None:
            raise RuntimeError("DeliveryManagerが初期化されていません。initialize()を呼び出してください。")
        return cls._instance
        
    def get_recipe_by_name(self, recipe_name: str) -> Any:
        """レシピ名から安全にレシピを取得する"""
        query = "SELECT * FROM recipes WHERE name = ?"
        with sqlite3.connect('recipes.db') as conn:
            cursor = conn.cursor()
            return cursor.execute(query, (recipe_name,)).fetchone()
    
    def update(self):
        """フレーム更新処理（UnityのUpdate相当）"""
        current_time = time.time()
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time
        
        kitchen_game_manager = KitchenGameManager.get_instance()
        if kitchen_game_manager.is_game_playing():
            # RecipeSpawnerを使用してレシピを生成
            new_recipe = self._recipe_spawner.update(delta_time)
            if new_recipe and len(self._waiting_recipe_so_list) < self._recipe_spawner.max_waiting:
                self._waiting_recipe_so_list.append(new_recipe)
                self.on_recipe_spawned.invoke(self, RecipeEventArgs(
                    recipe=new_recipe,
                    success=True,
                    message="新しいレシピが生成されました"
                ))
    
    def deliver_recipe(self, plate_kitchen_object: PlateKitchenObject) -> None:
        """
        レシピの材料と皿の材料が一致しているかどうかを確認する
        
        Args:
            plate_kitchen_object: 配達する皿オブジェクト
            
        Raises:
            InvalidRecipeError: 無効な皿や材料の場合
        """
        try:
            if not isinstance(plate_kitchen_object, PlateKitchenObject):
                raise InvalidRecipeError("無効な皿オブジェクトです")
            
            plate_ingredients = plate_kitchen_object.get_kitchen_object_so_list()
            if not plate_ingredients:
                raise InvalidRecipeError("皿が空です")
            
            plate_counter = Counter(plate_ingredients)
            
            for i, waiting_recipe_so in enumerate(self._waiting_recipe_so_list):
                recipe_counter = Counter(waiting_recipe_so.kitchen_object_so_list)
                if plate_counter == recipe_counter:
                    self._successful_recipes_amount += 1
                    self._waiting_recipe_so_list.pop(i)
                    
                    self.on_recipe_result.invoke(self, RecipeEventArgs(
                        recipe=waiting_recipe_so,
                        success=True,
                        message="レシピ配達成功！"
                    ))
                    return
            
            # 一致するレシピが見つからなかった場合
            self.on_recipe_result.invoke(self, RecipeEventArgs(
                recipe=None,
                success=False,
                message="一致するレシピが見つかりませんでした"
            ))
            
        except InvalidRecipeError as e:
            self.on_recipe_result.invoke(self, RecipeEventArgs(
                recipe=None,
                success=False,
                message=str(e)
            ))
    
    def get_waiting_recipe_so_list(self) -> List[RecipeSO]:
        """待機中のレシピリストを取得"""
        return self._waiting_recipe_so_list.copy()
    
    def get_successful_recipes_amount(self) -> int:
        """成功したレシピ数を取得"""
        return self._successful_recipes_amount


# 使用例
if __name__ == "__main__":
    # サンプルデータ作成
    tomato = KitchenObjectSO("Tomato", 1)
    lettuce = KitchenObjectSO("Lettuce", 2)
    bread = KitchenObjectSO("Bread", 3)
    
    # サンプルレシピ
    sandwich_recipe = RecipeSO("Sandwich", [bread, lettuce, tomato])
    salad_recipe = RecipeSO("Salad", [lettuce, tomato])
    
    recipe_list = RecipeListSO([sandwich_recipe, salad_recipe])
    
    # ゲームマネージャーとデリバリーマネージャーを初期化
    game_manager = KitchenGameManager.get_instance()
    game_manager.start_game()
    
    delivery_manager = DeliveryManager.get_instance(recipe_list)
    
    # イベントハンドラーの設定
    def on_recipe_spawned(sender, args: RecipeEventArgs):
        print(f"新しいレシピが生成されました！: {args.message}")
    
    def on_recipe_result(sender, args: RecipeEventArgs):
        print(f"レシピ結果: {args.message}")
    
    delivery_manager.on_recipe_spawned.add_handler(on_recipe_spawned)
    delivery_manager.on_recipe_result.add_handler(on_recipe_result)
    
    # サンプル実行
    print("ゲーム開始...")
    
    # 5秒間更新処理を実行
    start_time = time.time()
    while time.time() - start_time < 5:
        delivery_manager.update()
        time.sleep(0.1)  # 100ms間隔で更新
    
    print(f"待機中のレシピ数: {len(delivery_manager.get_waiting_recipe_so_list())}")
    
    # サンプル配達テスト
    plate = PlateKitchenObject()
    plate.add_kitchen_object(bread)
    plate.add_kitchen_object(lettuce)
    plate.add_kitchen_object(tomato)
    
    print("サンドイッチを配達...")
    delivery_manager.deliver_recipe(plate)
    
    print(f"成功したレシピ数: {delivery_manager.get_successful_recipes_amount()}")