import logging
from telegram import Update
from telegram.ext import ContextTypes

# --- Admin password (change as needed) ---
ADMIN_PASSWORD = "Prajituri420!"

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

# --- Utility: Check admin authentication in admin handlers ---
async def require_admin_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("is_admin_authenticated"):
        await update.message.reply_text("🔒 Please use /adminlogin to authenticate before using admin commands.")
        return False
    return True