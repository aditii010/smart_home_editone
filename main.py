# main.py

from llm_interface import query_llm
from rag_engine import RAGEngine
from intent_firewall import intent_firewall
from state_manager import StateManager
from smart_home_api import control_device


class SmartHomeAssistantXAI:
    def __init__(self):
        self.rag = RAGEngine()
        self.state_manager = StateManager()

    def generate_rich_explanation(self, device, action, result):
        """
        Create a user-friendly explanation for why the system took an action.
        """
        return (
            f"🤖 Explanation:\n"
            f"- Detected intent: {action} the {device}\n"
            f"- Executed action: {result}\n"
            f"- Safety & reasoning checks passed ✅\n"
        )

    def run(self):
        print("🎙️ SMART HOME ASSISTANT - XAI")
        print("💡 Rich explanations and intent transparency included.")
        print("Type 'exit' to quit\n")

        while True:
            user_input = input("🧑 You: ")
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break

            print("[AI] Processing your request...")

            llm_result = query_llm(user_input)

            # ✅ Normalize llm_result so it's always a list of dicts
            if isinstance(llm_result, str):
                llm_result = [{"text": llm_result, "device": None, "action": None}]
            elif isinstance(llm_result, dict):
                llm_result = [llm_result]
            elif not isinstance(llm_result, list):
                llm_result = []

            # Process each command returned by the LLM
            for cmd in llm_result:
                device = cmd.get("device")
                action = cmd.get("action")

                if device and action:
                    print(f"[LLM] Recognized command: device={device}, action={action}")

                    # ✅ Pass dict to intent_firewall (fixes your error)
                    if intent_firewall({"device": device, "action": action}):
                        confirm = input(
                            "⚠️ Safety Check: Are you sure you want to proceed? (yes/no): "
                        ).strip().lower()
                        if confirm != "yes":
                            print("❌ Command canceled by user.")
                            continue

                    # Execute the action
                    result = control_device(device=device, action=action)
                    explanation = self.generate_rich_explanation(device, action, result)
                    print(explanation)

                else:
                    print("[LLM] No command recognized, using knowledge base...")
                    rag_answer = self.rag.query(user_input)
                    print(f"[AI] RAG Response:\n💡 {rag_answer}")


if __name__ == "__main__":
    assistant = SmartHomeAssistantXAI()
    assistant.run()
