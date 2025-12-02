# 📱 Telegram Bot Setup

## 🚀 Quick Setup

### 1. Create a Bot on Telegram

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the instructions
3. Choose a name for your bot (e.g., "papersthisweek Bot")
4. Choose a username (must end with `bot`, e.g., `papersthisweek_bot`)
5. **Copy the token** that BotFather returns (something like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

**Option A - Simple Method:**
1. Send a message to your bot (any message)
2. Open in your browser:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   (Replace `<YOUR_TOKEN>` with the token you received)
3. Look for `"chat":{"id":123456789}` – that number is your `chat_id`

**Option B - Use @userinfobot:**
1. Search for `@userinfobot` on Telegram
2. Send `/start`
3. It will show your ID (negative for groups, positive for personal)

**Option C - Use @getidsbot:**
1. Search for `@getidsbot` on Telegram
2. Add it to a group or send `/start` directly
3. It will show the `chat_id`

### 3. Configure `.env`

Create or edit the `.env` file in the project root:

```env
# Bot token (from @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Your chat_id (number obtained above)
TELEGRAM_CHAT_ID=123456789
```

### 4. Install dependencies

```bash
pip install requests
```

(`requests` is already in `requirements.txt`)

### 5. Test

```bash
python telegram_sender.py
```

Or just run the agent:

```bash
python main.py
```

The ranking will be sent automatically to your Telegram! 🎉

---

## 📋 Full `.env` Example

```env
# Telegram (required for sending results)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# LLM (default: local)
LLM_PROVIDER=deepseek-local
DEEPSEEK_MODEL=deepseek-r1:7b

# Embeddings (default: local)
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=nomic-embed-text
```

---

## 🎯 Telegram Advantages

✅ **Very simple** – no browser required
✅ **More reliable** – official Telegram API
✅ **Markdown support** – nice formatted messages
✅ **Server-friendly** – runs in the background
✅ **No quota limits** – free and unlimited for normal use
✅ **Groups and channels** – can send to groups as well

---

## 🔧 Sending to Groups or Channels

### For Groups:
1. Add your bot to the group
2. Give it permission to send messages
3. Use the group `chat_id` (usually negative, e.g. `-1001234567890`)

### For Channels:
1. Create a channel
2. Add your bot as an administrator
3. Use the channel `chat_id` (format: `-1001234567890` or `@channel_name`)

**Get group/channel `chat_id`:**
- Add `@getidsbot` to the group/channel
- It will post the ID

---

## 🐛 Troubleshooting

### "TELEGRAM_BOT_TOKEN is not set"
- Check that you copied the token correctly from @BotFather
- Make sure it is in the `.env` file in the project root
- The token format should be: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### "Chat not found" or "Unauthorized"
- Check that `TELEGRAM_CHAT_ID` is correct
- Make sure you have sent at least one message to the bot
- For groups, ensure the bot was added to the group

### "Bad Request: can't parse entities"
- This usually happens due to invalid Markdown formatting
- The code already handles most cases, but if it persists, check the ranking text

### "requests not installed"
```bash
pip install requests
```

---

## 📚 Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [@BotFather](https://t.me/BotFather) – Create and manage bots
- [@getidsbot](https://t.me/getidsbot) – Discover chat IDs

---

## 💡 Tips

1. **Multiple recipients**: You can create a list of `chat_id`s and send to all of them
2. **Scheduling**: Use `cron` (Linux/Mac) or Task Scheduler (Windows) to run automatically
3. **Formatting**: Telegram supports Markdown, so rankings look nice
4. **Privacy**: Your data goes only to Telegram, which is usually more private than web-based hacks

---

## 🔒 Security

- **Never share your bot token** publicly
- Add `.env` to `.gitignore` if you use Git
- The token gives full control over your bot
- If it is exposed, revoke it in @BotFather and create a new one
