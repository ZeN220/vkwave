import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from vkwave.bots.core.dispatching.events.base import BaseEvent
from vkwave.bots.core.dispatching.filters import BaseFilter
from vkwave.bots.core.dispatching.filters.manage import FilterManager
from vkwave.bots.core.dispatching.handler.base import FILTERS_NOT_PASSED

from ..handler.callback import BaseCallback
from .registrar import HandlerRegistrar

HANDLER_NOT_FOUND = object()
logger = logging.getLogger(__name__)


class BaseRouter(ABC):
    @abstractmethod
    async def is_suitable(self, event: BaseEvent) -> bool:
        """Execute router's filters"""

    @abstractmethod
    async def process_event(self, event: BaseEvent) -> Any:
        """Process event. If suitable handler wasn't found then return HANDLER_NOT_FOUND"""

    @property
    @abstractmethod
    def registrar(self) -> HandlerRegistrar:
        ...


class DefaultRouter(BaseRouter):
    def __init__(self, filters: Optional[List[BaseFilter]] = None):
        self.filter_manager = FilterManager()
        filters = filters or []
        for filter in filters:
            self.filter_manager.add_filter(filter)

        self._registrar = HandlerRegistrar()

    @property
    def registrar(self) -> HandlerRegistrar:
        return self._registrar

    async def process_event(self, event: BaseEvent) -> Any:
        for handler in self._registrar.handlers:
            h_res = await handler.process_event(event)
            if h_res is FILTERS_NOT_PASSED:
                continue
            return h_res
        return HANDLER_NOT_FOUND

    async def is_suitable(self, event: BaseEvent) -> bool:
        return await self.filter_manager.execute_filters(event)

    def register_handler(
        self, *filters: Union[BaseFilter, Any], callback: Union[BaseCallback, Any]
    ):
        """
        Register handler with one method

        >>> router.register_handler(EventTypeFilter("message_new"), TextFilter("123"), callback=callback)
        """
        self._registrar.register(
            self._registrar.new().with_filters(*filters).handle(callback).ready()
        )
