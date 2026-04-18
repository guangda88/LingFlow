# Managed Agents Architecture Summary


Architecture Overview:
1.  **Brain (Core Logic)**: The LLM itself. Stateless.
2.  **Hands (Tools)**: Code execution, APIs. Stateful.
3.  **Conversation (Memory/Events)**: The log of all tool calls and responses.

Key Principles:
- **Decoupling**: Brain never touches the hardware directly.
- **Virtualization**: Tools are abstracted interfaces.
- **Event-Driven**: Everything is a log entry.
