"""SMTP 이메일 알림 유틸리티."""
import smtplib
from email.mime.text import MIMEText
from datetime import datetime


def send_email(smtp_cfg, subject, body):
    """이메일 한 통 전송."""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_cfg["user"]
    msg["To"] = smtp_cfg["to"]

    try:
        with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"]) as server:
            server.starttls()
            server.login(smtp_cfg["user"], smtp_cfg["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"  ⚠ 이메일 전송 실패: {e}")
        return False


def notify_error(smtp_cfg, task_name, error_msg):
    """오류 발생 알림."""
    if not smtp_cfg:
        return
    subject = f"[수집 오류] {task_name}"
    body = (
        f"작업: {task_name}\n"
        f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"오류: {error_msg}\n"
    )
    send_email(smtp_cfg, subject, body)


def notify_progress(smtp_cfg, task_name, current, total, extra=""):
    """진행률 리포트 전송."""
    if not smtp_cfg:
        return
    pct = current / total * 100 if total else 0
    subject = f"[진행 {pct:.0f}%] {task_name}"
    body = (
        f"작업: {task_name}\n"
        f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"진행: {current}/{total} ({pct:.1f}%)\n"
    )
    if extra:
        body += f"\n{extra}\n"
    send_email(smtp_cfg, subject, body)
