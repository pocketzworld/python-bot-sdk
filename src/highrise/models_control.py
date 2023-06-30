from attrs import define
from cattrs.preconf.json import make_converter

from ._unions import configure_tagged_union
from .models import KeepaliveRequest

converter = make_converter()


@define
class ControlSessionMetadata:
    connection_id: str
    instance_ids: list[str]


@define
class InstanceStartedEvent:
    """A room instance has been spawned."""

    instance_id: str


@define
class InstanceStoppedEvent:
    """A room instance has been stopped."""

    instance_id: str


ControlEvent = InstanceStartedEvent | InstanceStoppedEvent | KeepaliveRequest.Response

configure_tagged_union(ControlEvent, converter)
