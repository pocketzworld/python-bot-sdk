from __future__ import annotations

from enum import Enum, unique
from typing import Optional, Sequence

from attrs import Factory, define
from pendulum import DateTime


@define
class GetPublicUserResponse:
    user: User


@define
class GetPublicUsersResponse:
    users: list[UserBasic]
    total: int
    first_id: str
    last_id: str


@define
class GetPublicRoomResponse:
    room: Room


@define
class GetPublicRoomsResponse:
    rooms: list[RoomBasic]
    total: int
    first_id: str
    last_id: str


@define
class GetPublicPostResponse:
    post: Post


@define
class GetPublicPostsResponse:
    posts: list[PostBasic]
    total: int
    first_id: str
    last_id: str


@define
class GetPublicItemResponse:
    item: Item
    related_items: RelatedItems | None
    storefront_listings: StorefrontListings | None


@define
class GetPublicItemsResponse:
    items: list[ItemBasic]
    total: int
    first_id: str
    last_id: str


@define
class GetPublicGrabResponse:
    grab: Grab


@define
class GetPublicGrabsResponse:
    grabs: list[Grab]
    total: int
    first_id: str
    last_id: str


@unique
class ItemCategory(str, Enum):
    BAG = "bag"
    BLUSH = "blush"
    BODY = "body"
    DRESS = "dress"
    EARRINGS = "earrings"
    EMOTE = "emote"
    EYE = "eye"
    EYEBROW = "eyebrow"
    FACE_HAIR = "face_hair"
    FISHING_ROD = "fishing_rod"
    FRECKLE = "freckle"
    GLASSES = "glasses"
    GLOVES = "gloves"
    HAIR_BACK = "hair_back"
    HAIR_FRONT = "hair_front"
    HANDBAG = "handbag"
    HAT = "hat"
    JACKET = "jacket"
    LASHES = "lashes"
    MOLE = "mole"
    MOUTH = "mouth"
    NECKLACE = "necklace"
    NOSE = "nose"
    PANTS = "pants"
    SHIRT = "shirt"
    SHOES = "shoes"
    SHORTS = "shorts"
    SKIRT = "skirt"
    WATCH = "watch"
    FULLSUIT = "fullsuit"
    SOCK = "sock"
    TATTOO = "tattoo"
    ROD = "rod"
    AURA = "aura"


@unique
class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    NONE = "none_"


@unique
class LegacyRewardCategory(str, Enum):
    POPS = "pops"
    GEMS = "gems"
    OUTFIT = "outfit"
    GACHA_TOKENS = "gacha_tokens"
    FURNITURE = "furniture"
    COLLECTIBLE = "collectible"
    LUCKY_TOKENS = "lucky_tokens"
    EVENT_TICKETS = "event_tickets"
    EMOTE = "emote"
    GIFT_BOX = "gift_box"
    ENERGY = "energy"
    VIP_DAYS = "vip_days"
    CHIPS = "chips"
    PROMO_TOKENS = "promo_tokens"
    SKYPASS_STARS = "skypass_stars"
    ROOM_BOOST_TOKENS = "room_boost_tokens"
    ROOM_VOICE_TOKENS = "room_voice_tokens"
    POCKET_COINS = "pocket_coins"
    CASH = "cash"
    CUSTOM_CURRENCY = "custom_currency"
    PET = "pet"


@unique
class NFIStrategy(str, Enum):
    SEQUENTIAL = "sequential"
    TOTAL_DEFINED = "total_defined"
    POOL = "pool"


@define
class OutfitItemColors:
    dependent_colors: Sequence[str] = tuple()
    palettes: Sequence[list] = tuple()
    linked_colors: str = ""


@define
class OutfitItem:
    item_id: str
    name: str
    rarity: str
    active_palette: int
    parts: list[tuple[str, str]]
    colors: OutfitItemColors | None = None


@define
class ActiveRoomInfo:
    id: str
    display_name: str
    code_name: Optional[str]


@define
class Crew:
    id: str
    name: str


@define
class User:
    user_id: str
    username: str
    outfit: list[OutfitItem]
    bio: str
    joined_at: DateTime
    last_online_in: DateTime | None
    num_followers: int
    num_following: int
    num_friends: int
    active_room: Optional[ActiveRoomInfo]
    country_code: str
    crew: Optional[Crew]
    voice_enabled: bool
    discord_id: str | None = None


@define
class UserBasic:
    user_id: str
    username: str | None = None
    created_at: str | None = None
    joined_at: str | None = None
    last_connect_at: str | None = None
    last_activity_at: str | None = None
    banned_until: str | None = None
    banned: bool = False


@define
class Room:
    room_id: str
    disp_name: str
    created_at: str
    access_policy: str
    category: str
    owner_id: str
    locale: list[str] = []
    is_home_room: bool | None = None
    num_connected: int = 0
    moderator_ids: list[str] = []
    designer_ids: list[str] = []
    description: str | None = None
    crew_id: str | None = None
    bots: str | None = None
    indicators: str | None = None
    thumbnail_url: str | None = None
    banner_url: str | None = None


@define
class RoomBasic:
    room_id: str
    disp_name: str
    description: str
    category: str
    owner_id: str
    created_at: str
    access_policy: str
    locale: list[str] = []
    is_home_room: bool | None = None
    designer_ids: list[str] = []
    moderator_ids: list[str] = []


@define
class Comment:
    id: str
    content: str
    post_id: str
    author_id: str
    author_name: str
    num_likes: int


@define
class PostItem:
    item_id: str
    active_palette: int = 0
    account_bound: bool = False


@define
class PostInventory:
    items: list[PostItem]


@define
class PostBody:
    text: str
    inventory: PostInventory


@define
class Post:
    post_id: str
    author_id: str | None = None
    created_at: str | None = None
    file_key: str | None = None
    type: str | None = None
    visibility: str = "private"
    num_comments: int = 0
    num_likes: int = 0
    num_reposts: int = 0
    body: PostBody | None = None
    caption: str | None = None
    featured_user_ids: list[str] = []
    comments: list[Comment] = []


@define
class PostBasic:
    post_id: str
    author_id: str | None = None
    created_at: str | None = None
    file_key: str | None = None
    type: str | None = None
    visibility: str = "private"
    num_comments: int = 0
    num_likes: int = 0
    num_reposts: int = 0
    body: PostBody | None = None
    caption: str | None = None
    featured_user_ids: list[str] = []


@define
class SkinPart:
    bone: str
    slot: str
    image_file: str
    attachment_name: str | None = None
    has_remote_render_layer: bool | None = None


@define
class Item:
    item_id: str
    item_name: str
    acquisition_cost: int | None = None
    acquisition_amount: int | None = None
    acquisition_currency: str | None = None
    category: ItemCategory | None = None
    color_linked_categories: list[str] = []
    color_palettes: list[str] = []
    created_at: DateTime | None = None
    description_key: str | None = None
    gems_sale_price: int | None = None
    inspired_by: list[str] = []
    is_purchasable: bool = False
    is_tradable: bool = False
    image_url: str | None = None
    icon_url: str | None = None
    link_ids: list[str] = []
    m_dependent_colors: list[tuple[ItemCategory, int, int]] = []
    m_front_skin_part_list: list[SkinPart] = []
    m_back_skin_part_list: list[SkinPart] = []
    m_hidden_skin_parts: set[str] = Factory(set)
    pops_sale_price: int | None = None
    rarity: Rarity = Rarity.NONE
    release_date: DateTime | None = None


@define
class ItemBasic:
    item_id: str
    item_name: str
    category: ItemCategory | None = None
    color_linked_categories: list[str] | None = []
    color_palettes: list[str] | None = []
    created_at: DateTime | None = None
    description_key: str | None = None
    gems_sale_price: int | None = None
    inspired_by: list[str] = []
    is_purchasable: bool = False
    is_tradable: bool = False
    image_url: str | None = None
    icon_url: str | None = None
    link_ids: list[str] = []
    m_dependent_colors: list[tuple[ItemCategory, int, int]] | None = []
    m_front_skin_part_list: list[SkinPart] = []
    m_back_skin_part_list: list[SkinPart] = []
    m_hidden_skin_parts: set[str] = Factory(set)
    pops_sale_price: int | None = None
    rarity: Rarity = Rarity.NONE
    release_date: DateTime | None = None


@define
class Affiliation:
    id: str
    title: str
    type: str
    event_type: str | None = None


@define
class RelatedItem:
    item_id: str
    disp_name: str
    rarity: Rarity = Rarity.NONE


@define
class RelatedItems:
    affiliations: list[Affiliation] = []
    items: list[RelatedItem] = []


@define
class Seller:
    user_id: str
    username: str
    outfit: list[OutfitItem] = []
    last_connected_at: DateTime | None = None


@define
class StorefrontListings:
    sellers: list[Seller] = []
    pages: int = 0
    total: int = 0


@define
class NFIItemMetadata:
    item_number: int
    stack_id: str


@define
class NFITemplateMetadata:
    strategy: NFIStrategy
    total_amount: int | None = None


@define
class ItemMetadata:
    nfi_metadata: NFIItemMetadata | None = None
    nfi_template_metadata: NFITemplateMetadata | None = None


@define
class Reward:
    category: LegacyRewardCategory
    amount: int
    reward_id: str = ""
    item_id: str | None = None
    account_bound: bool = False
    metadata: ItemMetadata | None = None


@define
class LimitedKompuReward:
    expires_at: DateTime | None = None
    rewards: list[Reward] = []


@define
class ProgressReward:
    rewards_at: int
    rewards: list[Reward] = []


@define
class Grab:
    grab_id: str
    title: str
    description: str
    background_color: tuple[int, int, int]
    banner_img_url: str
    starts_at: DateTime | None = None
    expires_at: DateTime | None = None
    rewards: list[Reward] = []
    primary_img_url: str | None = None
    secondary_img_url: str | None = None
    costs: list[Reward] = []
    kompu_rewards: list[Reward] = []
    is_tradable: bool = True
    limited_time_kompu: LimitedKompuReward | None = None
    progress_reward: ProgressReward | None = None
