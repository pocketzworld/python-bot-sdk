from __future__ import annotations

from typing import Optional, Sequence

from attrs import define
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
    colors: OutfitItemColors | None


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
    badge: int
    joined_at: DateTime
    last_online_in: int | None
    num_followers: int
    num_following: int
    num_friends: int
    active_room: Optional[ActiveRoomInfo]
    country_code: str
    crew: Optional[Crew]
    voice_enabled: bool


@define
class UserBasic:
    user_id: str
    joined_at: str
    username: str
    last_connect_at: str
    last_activity_at: str
    created_at: str
    banned_until: str
    banned: bool


@define
class Room:
    room_id: str
    disp_name: str
    created_at: str
    num_connected: str
    moderator_ids: list[str]
    designer_ids: list[str]
    crew_id: str
    description: str
    locale: str
    access_policy: str
    category: str
    bots: str
    indicators: str
    thumbnail_url: str
    banner_url: str
    owner_id: str
    is_home_room: str


@define
class RoomBasic:
    room_id: str
    disp_name: str
    description: str
    category: str
    locale: str
    is_home_room: str
    owner_id: str
    designer_ids: list[str]
    moderator_ids: list[str]
    created_at: str
    access_policy: str


@define
class Comment:
    id: str
    content: str
    postId: str
    authorId: str
    authorName: str
    numLikes: int


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
    author_id: str
    body: PostBody | None
    caption: str
    comments: list[Comment]
    created_at: str
    featured_user_ids: str
    file_key: str
    num_comments: int
    num_likes: int
    num_reposts: int
    type: str
    visibility: str


@define
class PostBasic:
    post_id: str
    author_id: str
    body: PostBody | None
    caption: str
    created_at: str
    featured_user_ids: str
    file_key: str
    num_comments: int
    num_likes: int
    num_reposts: int
    type: str
    visibility: str
