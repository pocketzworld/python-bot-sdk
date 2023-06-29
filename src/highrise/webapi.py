from os import environ
from typing import Any, Literal, Type

from aiohttp import ClientSession
from cattrs import Converter
from pendulum import DateTime, parse

from .models_webapi import (
    GetPublicPostResponse,
    GetPublicPostsResponse,
    GetPublicRoomResponse,
    GetPublicRoomsResponse,
    GetPublicUserResponse,
    GetPublicUsersResponse,
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
            user_id (str): The unique identifier for a user.

        Returns:
            GetPublicUserResponse: The public data of the user.
        """
        endpoint = f"/users/{user_id}"
        return await self.send_request(endpoint, GetPublicUserResponse)

    async def get_users(
        self,
        starts_after: str = "",
        ends_before: str = "",
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        username: str = "",
    ) -> GetPublicUsersResponse:
        """Fetch a list of users, can be filtered, ordered, and paginated.

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
            room_id (str): The unique identifier for a room.

        Returns:
            GetPublicRoomResponse: The public data of the room.
        """
        endpoint = f"/rooms/{room_id}"
        return await self.send_request(endpoint, GetPublicRoomResponse)

    async def get_rooms(
        self,
        starts_after: str = "",
        ends_before: str = "",
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        room_name: str = "",
        owner_id: str = "",
    ) -> GetPublicRoomsResponse:
        """Fetch a list of rooms, can be filtered, ordered, and paginated.

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

        endpoint = f"/users?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return await self.send_request(endpoint, GetPublicRoomsResponse)

    async def get_post(self, post_id: str) -> GetPublicPostResponse:
        """Fetch a single post given its post_id.

        Args:
            post_id (str): The unique identifier for a post.

        Returns:
            GetPublicPostResponse: The public data of the post.
        """
        endpoint = f"/posts/{post_id}"
        return await self.send_request(endpoint, GetPublicPostResponse)

    async def get_posts(
        self,
        starts_after: str = "",
        ends_before: str = "",
        sort_order: SORT_OPTION = "desc",
        limit: int = 20,
        author_id: str = "",
    ) -> GetPublicPostsResponse:
        """Fetch a list of posts, can be filtered, ordered, and paginated.

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

        endpoint = f"/users?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return await self.send_request(endpoint, GetPublicPostsResponse)

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
