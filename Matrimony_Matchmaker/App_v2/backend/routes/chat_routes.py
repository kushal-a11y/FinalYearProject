from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from sqlalchemy import or_, and_, func

from db import db
from models.user_profile import UserProfile
from models.chat_message import ChatMessage

chat_bp = Blueprint('chat', __name__)


def _serialize_user(u):
    return {
        "user_id": u.user_id,
        "name": u.name or (u.email.split('@')[0] if u.email else f"User {u.user_id}"),
        "image_url": u.image_url,
        "verified": bool(u.pan_verified),
    }


@chat_bp.route('/chat/<int:user_id>')
def chat_page(user_id):
    """Render the full chat UI for the logged-in user."""
    user = UserProfile.query.get(user_id)
    if not user:
        return "User not found", 404
    peer_id = request.args.get('with', type=int)
    return render_template('chat.html', user=user, peer_id=peer_id)


@chat_bp.route('/chat/api/conversations/<int:user_id>', methods=['GET'])
def conversations(user_id):
    """List everyone this user has exchanged messages with, plus last message."""
    msgs = (
        ChatMessage.query
        .filter(or_(ChatMessage.sender_id == user_id,
                    ChatMessage.receiver_id == user_id))
        .order_by(ChatMessage.timestamp.desc())
        .all()
    )

    seen = {}
    for m in msgs:
        other_id = m.receiver_id if m.sender_id == user_id else m.sender_id
        if other_id not in seen:
            seen[other_id] = {
                "last_message": m.content,
                "last_time": m.timestamp.isoformat() if m.timestamp else None,
                "unread": 0,
            }
        if m.receiver_id == user_id and not m.is_read:
            seen[other_id]["unread"] += 1

    result = []
    for other_id, meta in seen.items():
        peer = UserProfile.query.get(other_id)
        if not peer:
            continue
        entry = _serialize_user(peer)
        entry.update(meta)
        result.append(entry)

    result.sort(key=lambda e: e["last_time"] or "", reverse=True)
    return jsonify({"conversations": result}), 200


@chat_bp.route('/chat/api/messages/<int:user_id>/<int:peer_id>', methods=['GET'])
def get_messages(user_id, peer_id):
    """Return the full thread between user_id and peer_id and mark incoming read."""
    after_id = request.args.get('after', type=int)  # for lightweight polling

    q = ChatMessage.query.filter(
        or_(
            and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == peer_id),
            and_(ChatMessage.sender_id == peer_id, ChatMessage.receiver_id == user_id),
        )
    )
    if after_id:
        q = q.filter(ChatMessage.id > after_id)

    messages = q.order_by(ChatMessage.timestamp.asc()).all()

    # Mark peer -> user messages as read
    unread = [m for m in messages if m.receiver_id == user_id and not m.is_read]
    if unread:
        for m in unread:
            m.is_read = True
        db.session.commit()

    peer = UserProfile.query.get(peer_id)
    return jsonify({
        "messages": [m.to_dict() for m in messages],
        "peer": _serialize_user(peer) if peer else None,
    }), 200


@chat_bp.route('/chat/api/send', methods=['POST'])
def send_message():
    data = request.get_json() or {}
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = (data.get('content') or '').strip()

    if not sender_id or not receiver_id:
        return jsonify({"error": "sender_id and receiver_id are required"}), 400
    if sender_id == receiver_id:
        return jsonify({"error": "You cannot message yourself"}), 400
    if not content:
        return jsonify({"error": "Message cannot be empty"}), 400
    if len(content) > 2000:
        return jsonify({"error": "Message is too long"}), 400

    if not UserProfile.query.get(sender_id) or not UserProfile.query.get(receiver_id):
        return jsonify({"error": "User not found"}), 404

    msg = ChatMessage(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        timestamp=datetime.utcnow(),
        is_read=False,
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"message": msg.to_dict()}), 201


@chat_bp.route('/chat/api/unread/<int:user_id>', methods=['GET'])
def unread_count(user_id):
    count = (
        db.session.query(func.count(ChatMessage.id))
        .filter(ChatMessage.receiver_id == user_id, ChatMessage.is_read == False)  # noqa: E712
        .scalar()
    )
    return jsonify({"unread": int(count or 0)}), 200


@chat_bp.route('/chat/api/start', methods=['POST'])
def start_conversation():
    """Validate that a conversation can be opened with a given peer."""
    data = request.get_json() or {}
    peer_id = data.get('peer_id')
    peer = UserProfile.query.get(peer_id) if peer_id else None
    if not peer:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"peer": _serialize_user(peer)}), 200
