"""
Example Plugin: Productivity Macros
Demonstrates macro automation for common tasks
"""

from src.core.plugin_api import PluginBase, PluginMetadata
from src.modules.input.macros import MacroActionType


class ProductivityMacrosPlugin(PluginBase):
    """
    Example plugin with productivity macros

    Features:
    - Text expansion macros
    - Application launching macros
    - Common workflow automation
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="productivity_macros",
            version="1.0.0",
            author="Linux Copilot",
            description="Productivity automation macros",
            dependencies=[]
        )

    async def initialize(self, core_api) -> bool:
        """Initialize the plugin"""
        try:
            self.core_api = core_api
            self.macro_engine = core_api.get_module('macros')
            self.keyboard = core_api.get_module('keyboard')

            if not self.macro_engine or not self.keyboard:
                self.logger.error("Required modules not available")
                return False

            # Subscribe to events
            core_api.subscribe_event("expand_text", self._expand_text)
            core_api.subscribe_event("run_workflow", self._run_workflow)

            # Define text expansion shortcuts
            self.expansions = {
                "@@email": "user@example.com",
                "@@date": self._get_current_date,
                "@@sig": "Best regards,\nYour Name"
            }

            self.logger.info("Productivity Macros Plugin initialized")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    async def shutdown(self):
        """Shutdown the plugin"""
        self.logger.info("Productivity Macros Plugin shutting down")

    def _get_current_date(self):
        """Get current date as string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    async def _expand_text(self, event):
        """Expand text shortcut"""
        try:
            shortcut = event.data.get('shortcut')
            if not shortcut:
                return

            if shortcut in self.expansions:
                expansion = self.expansions[shortcut]

                # If expansion is callable, call it
                if callable(expansion):
                    expansion = expansion()

                # Type the expansion
                await self.keyboard.type_text(expansion)
                self.logger.info(f"Expanded '{shortcut}' to '{expansion[:50]}...'")
            else:
                self.logger.warning(f"Unknown shortcut: {shortcut}")

        except Exception as e:
            self.logger.error(f"Error expanding text: {e}")

    async def _run_workflow(self, event):
        """Run a predefined workflow"""
        try:
            workflow_name = event.data.get('workflow')
            if not workflow_name:
                return

            if workflow_name == "open_dev_env":
                await self._open_dev_environment()
            elif workflow_name == "save_all":
                await self._save_all_documents()
            else:
                self.logger.warning(f"Unknown workflow: {workflow_name}")

        except Exception as e:
            self.logger.error(f"Error running workflow: {e}")

    async def _open_dev_environment(self):
        """Open development environment (example workflow)"""
        # This is a simplified example
        # In practice, this would open terminal, IDE, browser, etc.
        await self.keyboard.send_combination(['super', 't'])  # Open terminal
        self.logger.info("Opened development environment")

    async def _save_all_documents(self):
        """Save all open documents (example workflow)"""
        # Send Ctrl+S to save
        await self.keyboard.send_combination(['ctrl', 's'])
        self.logger.info("Saved all documents")
