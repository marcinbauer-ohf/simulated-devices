"""Todo platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated todo lists."""
    async_add_entities(
        SimulatedTodoListEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedTodoListEntity(SimulatedEntity, TodoListEntity):
    """Simulated maintenance list, stored in the coordinator state."""

    _attr_icon = "mdi:clipboard-check-outline"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "tasks", "Tasks")

    def _raw_items(self) -> list[dict]:
        return list(self.coordinator.data.get("todo_items", []))

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=item["uid"],
                summary=item["summary"],
                status=TodoItemStatus(item.get("status", "needs_action")),
            )
            for item in self._raw_items()
        ]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        items = self._raw_items()
        # ponytail: max-uid+1, fine for a simulator; use uuid4 if items ever sync.
        next_uid = str(max((int(i["uid"]) for i in items), default=0) + 1)
        items.append(
            {
                "uid": next_uid,
                "summary": item.summary or "",
                "status": (item.status or TodoItemStatus.NEEDS_ACTION).value,
            }
        )
        self.coordinator.set_state(todo_items=items)

    async def async_update_todo_item(self, item: TodoItem) -> None:
        items = self._raw_items()
        for existing in items:
            if existing["uid"] == item.uid:
                if item.summary is not None:
                    existing["summary"] = item.summary
                if item.status is not None:
                    existing["status"] = item.status.value
        self.coordinator.set_state(todo_items=items)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        remaining = [i for i in self._raw_items() if i["uid"] not in uids]
        self.coordinator.set_state(todo_items=remaining)
