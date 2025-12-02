"""
Módulo para enviar resultados do agente via Telegram.
Usa Telegram Bot API (oficial e confiável).
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

def send_telegram_message(chat_id: str, message: str) -> bool:
    """
    Send a message via Telegram using Bot API.
    
    Args:
        chat_id: ID of the chat (can be your user ID or ID of a group)
        message: Message to be sent
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        import requests
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not configured in .env")
            print("💡 Create a bot with @BotFather on Telegram and get the token")
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"  # Supports markdown formatting
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print(f"✅ Message sent to Telegram (chat_id: {chat_id})")
                return True
            else:
                print(f"❌ Telegram API Error: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except ImportError:
        print("❌ requests not installed. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

def send_ranking_to_telegram(chat_id: str, ranking_text: str, tema: str = "Tech News") -> bool:
    """
    Format and send the ranking of tech news via Telegram.
    
    Args:
        chat_id: ID of the Telegram chat
        ranking_text: Generated ranking text
        tema: Analyzed tech news theme
    
    Returns:
        True if sent successfully
    """
    # Format the message for Telegram with Markdown
    message = f"""🚀 *papersthisweek - {tema}*

{ranking_text}

---
Generated automatically via **papersthisweek** by [@bon4to](https://github.com/bon4to)"""
    
    return send_telegram_message(chat_id, message)

def get_telegram_chat_id() -> Optional[str]:
    """
    Try to get the chat_id of the user automatically.
    Return None if not possible.
    """
    try:
        import requests
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return None
        
        # Get the latest updates
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("result"):
                # Get the chat_id of the last received message
                updates = data["result"]
                if updates:
                    last_update = updates[-1]
                    if "message" in last_update:
                        return str(last_update["message"]["chat"]["id"])
        
        return None
    except Exception:
        return None

if __name__ == "__main__":
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if chat_id:
        send_telegram_message(
            chat_id,
            "🧪 *Test of Telegram bot - papersthisweek*\n\nWorking! ✅"
        )
    else:
        print("Configure TELEGRAM_CHAT_ID in .env to test")
        print("\n💡 To discover your chat_id:")
        print("   1. Send a message to your bot")
        print("   2. Access: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates")
        print("   3. Search for 'chat':{'id': ...}")

