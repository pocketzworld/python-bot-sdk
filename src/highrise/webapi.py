from os import environ
from typing import Any, Literal, Type

from aiohttp import ClientSession
from cattrs import Converter
from pendulum import DateTime, parse

from .models_webapi import (
    GetPublicGrabResponse,
    GetPublicGrabsResponse,
    GetPublicItemResponse,
    GetPublicItemsResponse,
    GetPublicPostResponse,
    GetPublicPostsResponse,
    GetPublicRoomResponse,
    GetPublicRoomsResponse,
    GetPublicUserResponse,
    GetPublicUsersResponse,
    ItemCategory,
)

converter = Converter()
converter.register_structure_hook(DateTime, lambda ts, _: parse(ts))

SORT_OPTION = Literal["desc", "asc"]


class WebAPI:
    """A class for interacting with the Highrise Web API.

    This class provides asynchronous methods for fetching data from the Highrise API.
    It supports fetching single and multiple users, rooms, and posts.

    Each method corresponds to a specific endpoint on the Highrise API, and returns a
    structured response based on the response JSON and webapi models.
    """

    url: str = environ.get("HR_WEBAPI_URL", "https://webapi.highrise.game")

    async def get_user(self, user_id: str) -> GetPublicUserResponse:
        """Fetch a single user given its user_id.

        Args:
            user_id: The unique identifier for a user.

        Returns:
            GetPublicUserResponse: The public data of the user.
        """
        endpoint = f"/users/{user_id}"
        return await self.send_request(endpoint, GetPublicUserResponse)

    async def get_users(
        self,
        starts_after: str | None = None,
        ends_before: str | None = None,
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        username: str | None = None,
    ) -> GetPublicUsersResponse:
        """Fetch a list of users, can be filtered, ordered, and paginated.

        Args:
            username: The username of a user.

        Returns:
            GetPublicUsersResponse: A list of public data of users.
        """
        params = {
            "starts_after": starts_after,
            "ends_before": ends_before,
            "sort_order": sort_order,
            "limit": limit,
            "username": username,
        }

        params = {k: v for k, v in params.items() if v is not None}

        endpoint = f"/users?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return await self.send_request(endpoint, GetPublicUsersResponse)

    async def get_room(self, room_id: str) -> GetPublicRoomResponse:
        """Fetch a single room given its room_id.

        Args:
            room_id: The unique identifier for a room.

        Returns:
            GetPublicRoomResponse: The public data of the room.
        """
        endpoint = f"/rooms/{room_id}"
        return await self.send_request(endpoint, GetPublicRoomResponse)

    async def get_rooms(
        self,
        starts_after: str | None = None,
        ends_before: str | None = None,
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        room_name: str | None = None,
        owner_id: str | None = None,
    ) -> GetPublicRoomsResponse:
        """Fetch a list of rooms, can be filtered, ordered, and paginated.

        Args:
            room_name: The name of a room.
            owner_id: The unique identifier of the owner of a room.

        Returns:
            GetPublicRoomsResponse: A list of public data of rooms.
        """
        params = {
            "starts_after": starts_after,
            "ends_before": ends_before,
            "sort_order": sort_order,
            "limit": limit,
            "room_name": room_name,
            "owner_id": owner_id,
        }

        params = {k: v for k, v in params.items() if v is not None}

        endpoint = f"/rooms?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return await self.send_request(endpoint, GetPublicRoomsResponse)

    async def get_post(self, post_id: str) -> GetPublicPostResponse:
        """Fetch a single post given its post_id.

        Args:
            post_id: The unique identifier for a post.

        Returns:
            GetPublicPostResponse: The public data of the post.
        """
        endpoint = f"/posts/{post_id}"
        return await self.send_request(endpoint, GetPublicPostResponse)

    async def get_posts(
        self,
        starts_after: str | None = None,
        ends_before: str | None = None,
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        author_id: str | None = None,
    ) -> GetPublicPostsResponse:
        """Fetch a list of posts, can be filtered, ordered, and paginated.

        Args:
            author_id: The unique identifier of the author of a post.

        Returns:
            GetPublicPostsResponse: A list of public data of posts.
        """
        params = {
            "starts_after": starts_after,
            "ends_before": ends_before,
            "sort_order": sort_order,
            "limit": limit,
            "author_id": author_id,
        }

        params = {k: v for k, v in params.items() if v is not None}

        endpoint = f"/posts?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return await self.send_request(endpoint, GetPublicPostsResponse)

    async def get_item(self, item_id: str) -> GetPublicItemResponse:
        """Fetch a single item given its item_id.

        Args:
            item_id: The unique identifier for a item.

        Returns:
            GetPublicItemResponse: The public data of the item.
        """
        endpoint = f"/items/{item_id}"
        return await self.send_request(endpoint, GetPublicItemResponse)

    async def get_items(
        self,
        starts_after: str | None = None,
        ends_before: str | None = None,
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        rarity: str | None = None,
        item_name: str | None = None,
        category: ItemCategory | None = None,
    ) -> GetPublicItemsResponse:
        """Fetch a list of items, can be filtered, ordered, and paginated.

        Args:
            rarity: The rarities of items to filter for, comma separated (eg: `rare,epic,legendary,none` or `rare`).
            item_name: The name of the item.
            category: The category of the item.

        Returns:
            GetPublicPostsResponse: A list of public data of posts.
        """
        params = {
            "starts_after": starts_after,
            "ends_before": ends_before,
            "sort_order": sort_order,
            "limit": limit,
            "rarity": rarity,
            "item_name": item_name,
            "category": category,
        }

        params = {k: v for k, v in params.items() if v is not None}

        endpoint = f"/items?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return await self.send_request(endpoint, GetPublicItemsResponse)

    async def get_grab(self, grab_id: str) -> GetPublicGrabResponse:
        """Fetch a single grab given its grab_id.

        Args:
            grab_id: The unique identifier for a grab.

        Returns:
            GetPublicGrabResponse: The public data of the grab.
        """
        endpoint = f"/grabs/{grab_id}"
        return await self.send_request(endpoint, GetPublicGrabResponse)

    async def get_grabs(
        self,
        starts_after: str | None = None,
        ends_before: str | None = None,
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        title: str | None = None,
    ) -> GetPublicGrabsResponse:
        """Fetch a list of grabs, can be filtered, ordered, and paginated.

        Args:
            title: The title of the grab.

        Returns:
            GetPublicGrabsResponse: A list of public data of grabs.
        """
        params = {
            "starts_after": starts_after,
            "ends_before": ends_before,
            "sort_order": sort_order,
            "limit": limit,
            "title": title,
        }

        params = {k: v for k, v in params.items() if v is not None}

        endpoint = f"/grabs?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return await self.send_request(endpoint, GetPublicGrabsResponse)

    async def send_request(self, endpoint: str, cl: Type[Any]) -> Any:
        """
        Sends a request to the given endpoint and returns a structured response from webapi models.

        Raises:
            ResponseError: If the response status is not 200.
        """
        async with ClientSession() as session:
            async with session.get(f"{self.url}{endpoint}") as response:
                from . import ResponseError

                if response.status == 200:
                    data = await response.json()
                    return converter.structure(data, cl)
                else:
                    raise ResponseError((await response.read()).decode())
