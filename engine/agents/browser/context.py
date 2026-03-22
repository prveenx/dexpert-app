from dataclasses import dataclass, field
from typing import Optional, Any, Callable, Awaitable

from playwright.async_api import Page, BrowserContext

from .browser.config.config import BrowserAgentSettings
from .browser.perception.perception import PerceptionPipeline
from .browser.controller.interaction import InteractionController
from .browser.controller.navigation import NavigationController
from .browser.tools.registry import BrowserToolRegistry
from .browser.perception.captcha_handler.solve import CaptchaHandler
from .browser.core.memory import BrowserMemory
from .browser.manager import BrowserManager
from core.scratchpad import Scratchpad
from llm.client import LLMClient

@dataclass
class BrowserAgentContext:
    page: Page
    browser_context: BrowserContext
    settings: BrowserAgentSettings
    prompts: Any  

    manager: BrowserManager
    navigator: NavigationController
    interactor: InteractionController
    perception: PerceptionPipeline
    tool_registry: BrowserToolRegistry

    scratchpad: Scratchpad
    memory: BrowserMemory
    captcha_handler: CaptchaHandler

    llm: LLMClient
    vision_llm: LLMClient
    
    # 🚀 Inject TUI emitter so tools can stream live progress
    emit_func: Callable[[str, str], Awaitable[None]]

    @classmethod
    def build(
        cls,
        page: Page,
        browser_context: BrowserContext,
        settings: BrowserAgentSettings,
        prompts: Any,
        manager: BrowserManager,
        llm: LLMClient,
        emit_func: Callable[[str, str], Awaitable[None]], # 🚀
        vision_llm: Optional[LLMClient] = None,
    ) -> "BrowserAgentContext":
        
        vision_llm = vision_llm or llm
        perception = PerceptionPipeline(settings)
        navigator = NavigationController(browser_context)
        interactor = InteractionController(navigator, settings)
        scratchpad = Scratchpad()
        memory = BrowserMemory()
        captcha_handler = CaptchaHandler(settings, perception, vision_llm, prompts)

        tool_registry = BrowserToolRegistry(
            navigator=navigator,
            interactor=interactor,
            perception=perception,
            scratchpad=scratchpad,
            manager=manager,
            emit_func=emit_func, # 🚀
            llm=llm,
            vision_llm=vision_llm,
            prompts=prompts
        )

        return cls(
            page=page,
            browser_context=browser_context,
            settings=settings,
            prompts=prompts,
            manager=manager,
            navigator=navigator,
            interactor=interactor,
            perception=perception,
            tool_registry=tool_registry,
            scratchpad=scratchpad,
            memory=memory,
            captcha_handler=captcha_handler,
            llm=llm,
            vision_llm=vision_llm,
            emit_func=emit_func, # 🚀
        )