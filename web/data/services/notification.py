
from typing import List
from data import db
from data.models import Notifications

class Notification:

    def get_unread_notifications(recipient_id: int) -> List[Notifications]:
        return Notifications.query.filter_by(recipient_id=recipient_id, is_read=False).order_by(Notifications.created_at.desc()).all()
    
    def get_recent_notifications(recipient_id: int, limit: int = 10) -> List[Notifications]:
        return (
            Notifications.query
            .filter_by(recipient_id=recipient_id)
            .order_by(Notifications.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_notification_by_id(notification_id: int) -> Notifications:
        return Notifications.query.filter_by(id=notification_id).first()

    def get_all_notifications(recipient_id: int) -> List[Notifications]:
        return Notifications.query.filter_by(recipient_id=recipient_id).order_by(Notifications.created_at.desc()).all()
    
    def mark_notification_as_read(notification_id: int) -> None:
        notification = Notifications.query.filter_by(id=notification_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()

    def mark_all_notifications_as_read(recipient_id: int) -> None:
        notifications = Notifications.query.filter_by(recipient_id=recipient_id, is_read=False).all()
        for notification in notifications:
            notification.is_read = True
        db.session.commit()

    def create_notification(recipient_id: int, sender_id: int, message: str) -> Notifications:
        new_notification = Notifications(
            recipient_id=recipient_id,
            sender_id=sender_id,
            message=message,
            is_read=False
        )
        db.session.add(new_notification)
        db.session.commit()

        # TODO: Insert Twilio or email notification logic here

        return new_notification

    def update_notification_message(notification_id: int, new_message: str) -> None:
        notification = Notifications.query.filter_by(id=notification_id).first()
        if notification:
            notification.message = new_message
            db.session.commit()

    def delete_notification(notification_id: int) -> None:
        notification = Notifications.query.filter_by(id=notification_id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()

    def delete_all_notifications(recipient_id: int) -> None:
        notifications = Notifications.query.filter_by(recipient_id=recipient_id).all()
        for notification in notifications:
            db.session.delete(notification)
        db.session.commit()
