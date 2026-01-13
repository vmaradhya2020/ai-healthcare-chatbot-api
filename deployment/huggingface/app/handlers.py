import re
from datetime import datetime, timedelta
from typing import Tuple, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app import models
from app.rag import query as rag_query
from app.intent import Intents
from app.config import settings

# ============================
# Generic NL parsing utilities
# ============================

TRACKING_RE = re.compile(r"\b[A-Z]{2,5}-?\d{3,}-?\d*\b", re.IGNORECASE)
DATE_ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
NUM_RE = re.compile(r"\b(\d+)\b")


def _now() -> datetime:
    return datetime.utcnow()


def _parse_limit(msg: str, default: int = 5, hard_max: int = 50) -> int:
    # Look for phrases like "last 5", "top 10", or any number in question
    num = None
    for m in NUM_RE.finditer(msg):
        try:
            val = int(m.group(1))
            if 1 <= val <= hard_max:
                num = val
                break
        except Exception:
            continue
    return num if num else default


def _extract_tracking(msg: str) -> Optional[str]:
    m = TRACKING_RE.search(msg)
    return m.group(0) if m else None


def _extract_status(msg: str, allowed: List[str]) -> Optional[str]:
    for st in allowed:
        if st in msg:
            return st
    return None


def _parse_date_range(msg: str) -> Optional[Tuple[datetime, datetime]]:
    msg = msg.lower()
    now = _now()
    start = end = None

    if "last week" in msg:
        start = now - timedelta(days=7)
        end = now
    elif "last month" in msg:
        start = now - timedelta(days=30)
        end = now
    elif "today" in msg:
        start = datetime(now.year, now.month, now.day)
        end = now
    elif "yesterday" in msg:
        yd = now - timedelta(days=1)
        start = datetime(yd.year, yd.month, yd.day)
        end = datetime(now.year, now.month, now.day)
    else:
        # between YYYY-MM-DD and YYYY-MM-DD
        if "between" in msg and "and" in msg:
            dates = DATE_ISO_RE.findall(msg)
            if len(dates) >= 2:
                try:
                    y1, m1, d1 = map(int, dates[0])
                    y2, m2, d2 = map(int, dates[1])
                    start = datetime(y1, m1, d1)
                    end = datetime(y2, m2, d2) + timedelta(days=1)
                except Exception:
                    start = end = None

    if start and end and start < end:
        return start, end
    return None


# =================================
# Orders domain: ask-anything engine
# =================================

_ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered"]


def handle_order_status(db: Session, client_id: int, message_text: str) -> Tuple[str, str]:
    msg = message_text.lower()

    # Defaults
    limit = _parse_limit(msg, default=5)
    status = _extract_status(msg, _ORDER_STATUSES)
    trk = _extract_tracking(msg)
    dr = _parse_date_range(msg)

    base = db.query(models.Order).filter(models.Order.client_id == client_id)

    # Tracking number explicitly asked → status for that order
    if trk:
        q = base.filter(models.Order.tracking_number == trk).order_by(models.Order.order_date.desc())
        order = q.first()
        if order:
            eta = order.expected_delivery_date.strftime("%Y-%m-%d") if order.expected_delivery_date else "unknown"
            return (f"Tracking {order.tracking_number}: status is '{order.status}'. Expected delivery: {eta}.", "sql")
        return (f"No order found for tracking number {trk}.", "sql")

    # Apply optional filters
    if status:
        base = base.filter(models.Order.status == status)
    if dr:
        start, end = dr
        base = base.filter(and_(models.Order.order_date >= start, models.Order.order_date < end))

    # Metric inference
    wants_count = any(w in msg for w in ["how many", "count", "number of"])
    wants_latest = any(w in msg for w in ["latest", "recent", "last order"]) and not wants_count
    wants_list = any(w in msg for w in ["list", "show"]) and not wants_count

    if wants_count:
        cnt = base.with_entities(func.count(models.Order.id)).scalar() or 0
        detail = f" with status '{status}'" if status else ""
        if dr:
            detail += " in the requested date range"
        return (f"You have {cnt} orders{detail}.", "sql")

    if wants_latest:
        order = base.order_by(models.Order.order_date.desc()).first()
        if not order:
            return ("No orders found for your criteria.", "sql")
        eta = order.expected_delivery_date.strftime("%Y-%m-%d") if order.expected_delivery_date else "unknown"
        return (
            f"Latest order: status '{order.status}', tracking {order.tracking_number or 'N/A'}, expected delivery {eta}.",
            "sql",
        )

    if wants_list:
        rows = base.order_by(models.Order.order_date.desc()).limit(limit).all()
        if not rows:
            return ("No orders found for your criteria.", "sql")
        lines = []
        for o in rows:
            eta = o.expected_delivery_date.strftime("%Y-%m-%d") if o.expected_delivery_date else "unknown"
            lines.append(
                f"- {o.order_date.strftime('%Y-%m-%d')} | status {o.status} | tracking {o.tracking_number or 'N/A'} | ETA {eta}"
            )
        return ("Here are the recent orders:\n" + "\n".join(lines), "sql")

    # Default overview: count + latest
    cnt = base.with_entities(func.count(models.Order.id)).scalar() or 0
    latest = base.order_by(models.Order.order_date.desc()).first()
    if latest:
        eta = latest.expected_delivery_date.strftime("%Y-%m-%d") if latest.expected_delivery_date else "unknown"
        extra = f" with status '{status}'" if status else ""
        if dr:
            extra += " in the requested date range"
        return (
            f"You have {cnt} orders{extra}. Latest is '{latest.status}', tracking {latest.tracking_number or 'N/A'}, ETA {eta}.",
            "sql",
        )
    return ("No orders found for your criteria.", "sql")


# ==================================
# Invoices domain: ask-anything engine
# ==================================

_INVOICE_STATUSES = ["pending", "paid", "overdue"]


def handle_payment_invoice(db: Session, client_id: int, message_text: str) -> Tuple[str, str]:
    msg = message_text.lower()

    limit = _parse_limit(msg, default=5)
    status = _extract_status(msg, _INVOICE_STATUSES)
    dr = _parse_date_range(msg)

    base = db.query(models.Invoice).filter(models.Invoice.client_id == client_id)

    if status:
        base = base.filter(models.Invoice.status == status)
    if dr:
        start, end = dr
        base = base.filter(and_(models.Invoice.invoice_date >= start, models.Invoice.invoice_date < end))

    wants_count = any(w in msg for w in ["how many", "count", "number of"])
    wants_sum = any(w in msg for w in ["sum", "total", "amount due", "total due", "outstanding"]) and (status in (None, "pending", "overdue"))
    wants_latest = any(w in msg for w in ["latest", "recent", "last invoice"]) and not (wants_count or wants_sum)
    wants_list = any(w in msg for w in ["list", "show"]) and not (wants_count or wants_sum)

    if wants_count:
        cnt = base.with_entities(func.count(models.Invoice.id)).scalar() or 0
        detail = f" with status '{status}'" if status else ""
        if dr:
            detail += " in the requested date range"
        return (f"You have {cnt} invoices{detail}.", "sql")

    if wants_sum:
        # Sum only over pending/overdue by default if not specified
        sum_base = base
        if status is None:
            sum_base = base.filter(models.Invoice.status.in_(["pending", "overdue"]))
        total_due = sum_base.with_entities(func.coalesce(func.sum(models.Invoice.amount), 0)).scalar() or 0
        return (f"Total outstanding amount is {total_due}.", "sql")

    if wants_latest:
        inv = base.order_by(models.Invoice.invoice_date.desc()).first()
        if not inv:
            return ("No invoices found for your criteria.", "sql")
        return (
            f"Latest invoice dated {inv.invoice_date.strftime('%Y-%m-%d')} has status '{inv.status}' and amount {inv.amount} {getattr(inv, 'currency', 'USD')}.",
            "sql",
        )

    if wants_list:
        rows = base.order_by(models.Invoice.invoice_date.desc()).limit(limit).all()
        if not rows:
            return ("No invoices found for your criteria.", "sql")
        lines = [
            f"- {i.invoice_date.strftime('%Y-%m-%d')} | {i.status} | {i.amount} {getattr(i, 'currency', 'USD')}"
            for i in rows
        ]
        return ("Here are the recent invoices:\n" + "\n".join(lines), "sql")

    # Default overview: pending count + total due + latest
    pending_cnt = (
        db.query(func.count(models.Invoice.id))
        .filter(models.Invoice.client_id == client_id, models.Invoice.status == "pending")
        .scalar()
        or 0
    )
    total_due = (
        db.query(func.coalesce(func.sum(models.Invoice.amount), 0))
        .filter(models.Invoice.client_id == client_id, models.Invoice.status.in_(["pending", "overdue"]))
        .scalar()
        or 0
    )
    latest = base.order_by(models.Invoice.invoice_date.desc()).first()
    if latest:
        return (
            f"Pending invoices: {pending_cnt}. Total outstanding: {total_due}. Latest invoice is '{latest.status}' on {latest.invoice_date.strftime('%Y-%m-%d')} for {latest.amount} {getattr(latest, 'currency', 'USD')}.",
            "sql",
        )
    return (f"Pending invoices: {pending_cnt}. Total outstanding: {total_due}.", "sql")


# ========================================
# Warranty/AMC domain: ask-anything engine
# ========================================

_WARRANTY_METRICS = ["count", "list", "latest"]


def handle_warranty_amc(db: Session, client_id: int, message_text: str) -> Tuple[str, str]:
    msg = message_text.lower()

    # Check if it's a general question that should use RAG
    if any(phrase in msg for phrase in ["what is", "explain", "tell me about", "period", "how long"]):
        try:
            res = rag_query(message_text, k=5, collection=settings.CHROMA_COLLECTION)
            docs = res.get("documents", [])
            if docs:
                snippet = "\n\n".join(d for d in docs[:2])
                return (f"From documentation: {snippet}", "rag")
            else:
                return ("No relevant documents found for your query.", "rag")
        except Exception as e:
            print(f"RAG error: {e}")
            # Fall back to SQL

    limit = _parse_limit(msg, default=5)
    wants_count = any(w in msg for w in ["how many", "count", "number of"])
    wants_list = any(w in msg for w in ["list", "show"]) and not wants_count
    wants_latest = any(w in msg for w in ["latest", "recent", "last"]) and not (wants_count or wants_list)

    # Active warranties
    war_q = (
        db.query(models.Warranty)
        .join(models.Equipment, models.Warranty.equipment_id == models.Equipment.id)
        .filter(models.Equipment.client_id == client_id)
    )

    # AMC contracts
    amc_q = (
        db.query(models.AMCContract)
        .join(models.Equipment, models.AMCContract.equipment_id == models.Equipment.id)
        .filter(models.Equipment.client_id == client_id)
    )

    if wants_count:
        active_w = war_q.filter(models.Warranty.status == "active").with_entities(func.count(models.Warranty.id)).scalar() or 0
        active_a = amc_q.filter(models.AMCContract.status == "active").with_entities(func.count(models.AMCContract.id)).scalar() or 0
        return (f"Active warranties: {active_w}. Active AMC contracts: {active_a}.", "sql")

    if wants_list:
        wars = war_q.order_by(models.Warranty.end_date.asc()).limit(limit).all()
        if not wars:
            return ("No warranties found.", "sql")
        lines = [
            f"- Equip {w.equipment_id} | {w.status} | {w.start_date.strftime('%Y-%m-%d')} to {w.end_date.strftime('%Y-%m-%d')}"
            for w in wars
        ]
        return ("Warranties:\n" + "\n".join(lines), "sql")

    if wants_latest:
        w = war_q.order_by(models.Warranty.end_date.desc()).first()
        if not w:
            return ("No warranties found.", "sql")
        return (
            f"Most recent warranty spans {w.start_date.strftime('%Y-%m-%d')} to {w.end_date.strftime('%Y-%m-%d')} with status '{w.status}'.",
            "sql",
        )

    # Overview
    active_w = war_q.filter(models.Warranty.status == "active").with_entities(func.count(models.Warranty.id)).scalar() or 0
    active_a = amc_q.filter(models.AMCContract.status == "active").with_entities(func.count(models.AMCContract.id)).scalar() or 0
    return (f"Active warranties: {active_w}. Active AMC contracts: {active_a}.", "sql")


# ======================================
# Maintenance domain: ask-anything engine
# ======================================


def handle_scheduling(db: Session, client_id: int, message_text: str) -> Tuple[str, str]:
    msg = message_text.lower()

    limit = _parse_limit(msg, default=5)
    wants_count = any(w in msg for w in ["how many", "count", "number of"]) and "maintenance" in msg
    wants_list = any(w in msg for w in ["list", "show", "upcoming"]) and not wants_count
    wants_latest = any(w in msg for w in ["latest", "recent", "last"]) and not (wants_count or wants_list)

    base = (
        db.query(models.ScheduledMaintenance)
        .join(models.Equipment, models.ScheduledMaintenance.equipment_id == models.Equipment.id)
        .filter(models.Equipment.client_id == client_id)
    )

    if wants_count:
        cnt = base.with_entities(func.count(models.ScheduledMaintenance.id)).scalar() or 0
        return (f"You have {cnt} scheduled maintenance entries.", "sql")

    if wants_list:
        rows = base.order_by(models.ScheduledMaintenance.scheduled_date.asc()).limit(limit).all()
        if not rows:
            return ("No scheduled maintenance found.", "sql")
        lines = []
        for m in rows:
            ds = m.scheduled_date.strftime('%Y-%m-%d') if m.scheduled_date else 'unknown'
            lines.append(f"- Equipment {m.equipment_id} | {m.status} | {ds}")
        return ("Upcoming maintenance:\n" + "\n".join(lines), "sql")

    if wants_latest:
        m = base.order_by(models.ScheduledMaintenance.scheduled_date.desc()).first()
        if not m:
            return ("No scheduled maintenance found.", "sql")
        ds = m.scheduled_date.strftime('%Y-%m-%d') if m.scheduled_date else 'unknown'
        return (f"Most recent maintenance entry: equipment {m.equipment_id}, status {m.status}, on {ds}.", "sql")

    # Overview
    cnt = base.with_entities(func.count(models.ScheduledMaintenance.id)).scalar() or 0
    return (f"You have {cnt} scheduled maintenance entries.", "sql")


# ======================
# Tickets/complaints NL
# ======================


def handle_complaint(db: Session, user_id: int, client_id: int, message_text: str) -> Tuple[str, str]:
    msg = message_text.lower().strip()

    wants_create = any(w in msg for w in ["create", "log", "register"]) or "complaint" in msg
    wants_count = any(w in msg for w in ["how many", "count", "number of"]) and ("ticket" in msg or "complaint" in msg)
    wants_list = any(w in msg for w in ["list", "show"]) and ("ticket" in msg or "complaint" in msg)

    base = db.query(models.Ticket).filter(models.Ticket.client_id == client_id)

    if wants_count:
        open_cnt = base.filter(models.Ticket.status.in_(["open", "in_progress"]))\
            .with_entities(func.count(models.Ticket.id)).scalar() or 0
        return (f"You have {open_cnt} open or in-progress tickets.", "sql")

    if wants_list:
        limit = _parse_limit(msg, default=5)
        rows = base.order_by(models.Ticket.created_at.desc()).limit(limit).all()
        if not rows:
            return ("No tickets found.", "sql")
        lines = [
            f"- #{t.id} | {t.status} | {t.subject[:50]}"
            for t in rows
        ]
        return ("Recent tickets:\n" + "\n".join(lines), "sql")

    if wants_create:
        text = message_text.strip()
        if len(text) < 15:
            return ("To register a complaint, please provide a short subject and brief description in one message.", "none")
        subject = (text[:80] + "...") if len(text) > 80 else text
        ticket = models.Ticket(
            client_id=client_id,
            user_id=user_id,
            subject=subject,
            description=text,
            status="open",
            priority="medium",
            created_at=datetime.utcnow(),
        )
        db.add(ticket)
        db.commit()
        return (f"Complaint registered with ticket id {ticket.id}.", "sql")

    # Overview
    open_cnt = base.filter(models.Ticket.status.in_(["open", "in_progress"]))\
        .with_entities(func.count(models.Ticket.id)).scalar() or 0
    return (f"You have {open_cnt} open or in-progress tickets.", "sql")


# ===============================
# Default / RAG placeholder logic
# ===============================

def handle_default(db: Session, client_id: int, message_text: str) -> Tuple[str, str]:
    # Use RAG for non-SQL intents: attempt retrieval and compose a grounded answer.
    res = rag_query(message_text, k=5, collection=settings.CHROMA_COLLECTION)
    docs = res.get("documents", [])
    metas = res.get("metadatas", [])

    if not docs:
        return (
            "I couldn't find relevant documents yet. Please add docs and run the ingestion script.",
            "none",
        )

    # Compose a concise grounded answer
    preview = "\n".join([f"- {m.get('source','doc')} (chunk {m.get('chunk')})" for m in metas[:3]])
    snippet = "\n\n".join(d[:300] for d in docs[:2])
    answer = (
        "Here's what I found in the documentation (summarized):\n\n"
        f"{snippet}\n\nSources:\n{preview}"
    )
    return (answer, "rag")
