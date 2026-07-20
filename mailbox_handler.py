import email
import imaplib
import smtplib
from email.message import EmailMessage
from email.policy import default


def open_imap_connection(config):
    mailbox = imaplib.IMAP4_SSL(
        config.mail_config.email_server,
        config.mail_config.imap_port,
    )
    mailbox.login(
        config.mail_config.email_user,
        config.mail_config.email_password,
    )
    return mailbox


def fetch_email_ids(mailbox, folder):
    status, _ = mailbox.select(folder)
    if status != "OK":
        return [], f"IMAP: failed to select mailbox folder '{folder}'."

    # Use UIDs so IDs stay valid after move/expunge renumbers sequence numbers.
    status, id_data = mailbox.uid("SEARCH", None, "ALL")
    if status != "OK":
        return [], "IMAP: failed to search messages."
    if not id_data or not id_data[0]:
        return [], None

    return id_data[0].split(), None


def fetch_email_by_id(
    mailbox,
    email_id,
):
    try:
        status, msg_data = mailbox.uid("FETCH", email_id.decode("ascii"), "(RFC822)")
        if (
            status != "OK"
            or not msg_data
            or not isinstance(msg_data[0], tuple)
            or len(msg_data[0]) < 2
            or not isinstance(msg_data[0][1], bytes)
        ):
            return None, None, f"IMAP: skipping email id={email_id!r}; fetch returned no message."
        raw_message = msg_data[0][1]
        msg = email.message_from_bytes(raw_message, policy=default)
        return msg, raw_message, None
    except (imaplib.IMAP4.error, ValueError, TypeError, IndexError, UnicodeDecodeError) as exc:
        return None, None, f"IMAP: failed fetching email id={email_id!r}: {exc}"


def _build_forward_message(
    raw_message,
    original_message,
    target_email,
    category,
    mail_config,
):
    forwarded_message = EmailMessage()
    subject = original_message.get("Subject", "(no subject)")
    forwarded_message["From"] = mail_config.email_user
    forwarded_message["To"] = target_email
    forwarded_message["Subject"] = f"FWD [{category.upper()}] {subject}"
    forwarded_message.set_content(
        "Forwarded by errol.\n"
        f"Original category: {category}\n"
        f"Original from: {original_message.get('From', '(unknown)')}\n"
        f"Original subject: {subject}\n"
    )
    forwarded_message.add_attachment(
        raw_message,
        maintype="message",
        subtype="rfc822",
        filename="original.eml",
    )
    return forwarded_message


def forward_email(
    raw_message,
    original_message,
    target_email,
    category,
    config,
):
    if not target_email.strip():
        return f"SMTP: no forward target configured for category '{category}'."

    try:
        forwarded_message = _build_forward_message(
            raw_message=raw_message,
            original_message=original_message,
            target_email=target_email,
            category=category,
            mail_config=config.mail_config,
        )
        with smtplib.SMTP_SSL(config.mail_config.email_server, config.mail_config.smtp_port) as smtp:
            smtp.login(
                config.mail_config.email_user,
                config.mail_config.email_password,
            )
            smtp.send_message(forwarded_message)
    except (smtplib.SMTPException, OSError, ValueError) as exc:
        return f"SMTP: failed forwarding category='{category}' to '{target_email}': {exc}"
    return None


def send_text_email(
    target_email,
    subject,
    body,
    config,
):
    if not target_email or not target_email.strip():
        return "SMTP: no report target configured."

    report_message = EmailMessage()
    report_message["From"] = config.mail_config.email_user
    report_message["To"] = target_email
    report_message["Subject"] = subject
    report_message.set_content(body)

    try:
        with smtplib.SMTP_SSL(config.mail_config.email_server, config.mail_config.smtp_port) as smtp:
            smtp.login(
                config.mail_config.email_user,
                config.mail_config.email_password,
            )
            smtp.send_message(report_message)
    except (smtplib.SMTPException, OSError, ValueError) as exc:
        return f"SMTP: failed sending report to '{target_email}': {exc}"
    return None


def ensure_mailbox_folder(mailbox, folder):
    status, _ = mailbox.create(folder)
    if status in {"OK", "NO"}:
        # "NO" usually means the folder already exists on many IMAP servers.
        return None
    return f"IMAP: failed to ensure mailbox folder '{folder}'."


def move_email_to_folder(
    mailbox,
    email_id,
    target_folder,
):
    try:
        uid = email_id.decode("ascii")
        copy_status, _ = mailbox.uid("COPY", uid, target_folder)
        if copy_status != "OK":
            return f"IMAP: failed to copy email id={email_id!r} to '{target_folder}'."
        store_status, _ = mailbox.uid("STORE", uid, "+FLAGS", "\\Deleted")
        if store_status != "OK":
            return f"IMAP: failed to mark email id={email_id!r} deleted after copy."
        expunge_status, _ = mailbox.expunge()
        if expunge_status != "OK":
            return f"IMAP: failed to expunge email id={email_id!r} after move."
    except (imaplib.IMAP4.error, UnicodeDecodeError) as exc:
        return f"IMAP: failed moving email id={email_id!r} to '{target_folder}': {exc}"
    return None
