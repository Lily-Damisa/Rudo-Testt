"""
supabase_db.py — Supabase database layer for Rudo chatbot.
Replaces all Redis/Upstash operations with Supabase (PostgreSQL).
"""

import os
import json
import logging
from datetime import datetime
from supabase import create_client, Client

# ── Initialise Supabase client ────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Successfully connected to Supabase")
    except Exception as e:
        logging.error(f"Failed to connect to Supabase: {e}")
        supabase = None
else:
    logging.warning("SUPABASE_URL or SUPABASE_KEY not set. Supabase functionality disabled.")


# ── USER STATE ────────────────────────────────────────────────────────────────

def save_user_state(sender: str, state: dict):
    """Save or update a user's conversation state in Supabase."""
    if not supabase:
        return
    try:
        supabase.table("user_states").upsert({
            "sender":     sender,
            "state":      json.dumps(state),
            "updated_at": datetime.utcnow().isoformat()
        }, on_conflict="sender").execute()
        logging.debug(f"Saved state for {sender}")
    except Exception as e:
        logging.error(f"Error saving user state for {sender}: {e}")


def load_user_state(sender: str):
    """Load a user's conversation state from Supabase. Returns dict or None."""
    if not supabase:
        return None
    try:
        result = supabase.table("user_states").select("state").eq("sender", sender).execute()
        if result.data:
            return json.loads(result.data[0]["state"])
    except Exception as e:
        logging.error(f"Error loading user state for {sender}: {e}")
    return None


# ── CONVERSATION HISTORY ──────────────────────────────────────────────────────

def get_conversation(sender: str):
    """Get the last 100 messages for a user from Supabase."""
    if not supabase:
        return []
    try:
        result = (
            supabase.table("conversations")
            .select("role, message, created_at")
            .eq("sender", sender)
            .order("created_at", desc=False)
            .limit(100)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error getting conversation for {sender}: {e}")
        return []


def save_message(sender: str, role: str, message: str):
    """Save a single message to the conversations table."""
    if not supabase:
        return
    try:
        supabase.table("conversations").insert({
            "sender":     sender,
            "role":       role,
            "message":    str(message),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        logging.debug(f"Saved {role} message for {sender}")
    except Exception as e:
        logging.error(f"Error saving message for {sender}: {e}")


# ── ORDERS ────────────────────────────────────────────────────────────────────

def save_order(sender: str, user_id: str, product: str, price: str, quantity: int, address: str):
    """Save a single order to the orders table."""
    if not supabase:
        return
    try:
        supabase.table("orders").insert({
            "sender":     sender,
            "user_id":    user_id,
            "product":    product,
            "price":      price,
            "quantity":   quantity,
            "address":    address,
            "status":     "pending",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        logging.info(f"Order saved for {sender}: {product} x{quantity}")
    except Exception as e:
        logging.error(f"Error saving order for {sender}: {e}")


def get_all_orders():
    """Fetch all orders for the dashboard."""
    if not supabase:
        return []
    try:
        result = (
            supabase.table("orders")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error fetching orders: {e}")
        return []


def get_all_users():
    """Fetch all user states for the dashboard."""
    if not supabase:
        return []
    try:
        result = (
            supabase.table("user_states")
            .select("sender, state, updated_at")
            .order("updated_at", desc=True)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return []


def get_all_conversations():
    """Fetch all conversations for the dashboard."""
    if not supabase:
        return []
    try:
        result = (
            supabase.table("conversations")
            .select("*")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logging.error(f"Error fetching conversations: {e}")
        return []