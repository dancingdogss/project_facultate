import logging
from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps

ADMIN_IDS = [5501799605]  # Your admin user IDs
ADMIN_PASSWORD = "Prajituri420!"  # Change as needed

# --- Set up admin action logger ---
admin_logger = logging.getLogger("admin_actions")
admin_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("admin_actions.log", encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(user_id)s - %(command)s')
file_handler.setFormatter(formatter)
if not admin_logger.hasHandlers():
    admin_logger.addHandler(file_handler)

def log_admin_action(user_id, command):
    admin_logger.info("", extra={"user_id": user_id, "command": command})

# --- Admin login flow ---
async def adminlogin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔒 Enter admin password:")
    context.user_data["awaiting_admin_password"] = True

async def admin_password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_admin_password"):
        return
    if update.message.text == ADMIN_PASSWORD:
        context.user_data["is_admin_authenticated"] = True
        context.user_data.pop("awaiting_admin_password", None)
        await update.message.reply_text("✅ Admin login successful. You can now use admin commands.")
        log_admin_action(update.effective_user.id, "Admin login successful")
    else:
        await update.message.reply_text("❌ Incorrect password. Try again or /cancel.")
        log_admin_action(update.effective_user.id, "Failed admin login attempt")

# --- Decorator: Require admin authentication for admin commands ---
def require_admin_auth(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id in ADMIN_IDS or context.user_data.get("is_admin_authenticated"):
            return await func(update, context, *args, **kwargs)
        else:
            # Gracefully handle both messages and callback queries
            context.user_data["awaiting_admin_password"] = True
            cq = getattr(update, "callback_query", None)
            if cq is not None:
                try:
                    await cq.answer("Please authenticate: use /adminlogin", show_alert=True)
                except Exception:
                    pass
                try:
                    await cq.message.reply_text("🔒 Please use /adminlogin and enter the admin password to access this command.")
                except Exception:
                    pass
            else:
                msg = getattr(update, "message", None) or getattr(update, "effective_message", None)
                if msg is not None:
                    await msg.reply_text("🔒 Please use /adminlogin and enter the admin password to access this command.")
            return
    return wrapper