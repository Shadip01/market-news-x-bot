from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
import html
import smtplib


@dataclass(frozen=True)
class EmailSection:
    headline: str
    summary_lines: tuple[str, ...]
    link: str
    source: str


class EmailPublisher:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_use_tls: bool,
        smtp_username: str,
        smtp_password: str,
        email_from: str,
        email_to: tuple[str, ...],
        dry_run: bool,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_use_tls = smtp_use_tls
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.email_from = email_from
        self.email_to = email_to
        self.dry_run = dry_run

    def send_digest(self, sections: list[EmailSection]) -> None:
        if not sections:
            return

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        subject = f"Market News Digest ({len(sections)} updates) - {now_utc}"
        text_body = self._build_text_body(sections)
        html_body = self._build_html_body(sections)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.email_from
        msg["To"] = ", ".join(self.email_to)
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        if self.dry_run:
            print("[DRY RUN] Would send email digest:")
            print(f"To: {msg['To']}")
            print(f"Subject: {subject}")
            print(text_body)
            return

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
            if self.smtp_use_tls:
                server.starttls()
            if self.smtp_username:
                server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
        print(f"Sent email digest to {', '.join(self.email_to)}")

    @staticmethod
    def _build_text_body(sections: list[EmailSection]) -> str:
        lines = ["Latest Market News", ""]
        for idx, section in enumerate(sections, start=1):
            lines.append(f"{idx}. {section.headline}")
            for line in section.summary_lines:
                lines.append(f"   - {line}")
            lines.append(f"   Source: {section.source}")
            lines.append(f"   Link: {section.link}")
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def _build_html_body(sections: list[EmailSection]) -> str:
        blocks: list[str] = ["<h2>Latest Market News</h2>"]
        for section in sections:
            summary_list = "".join(
                f"<li>{html.escape(line)}</li>" for line in section.summary_lines
            )
            safe_headline = html.escape(section.headline)
            safe_source = html.escape(section.source)
            safe_link = html.escape(section.link, quote=True)
            blocks.append(
                """
                <div style=\"margin-bottom:18px;\">
                  <h3 style=\"margin:0 0 8px 0;\">{headline}</h3>
                  <ul style=\"margin:0 0 8px 16px; padding:0;\">{summary_list}</ul>
                  <p style=\"margin:0;\"><strong>Source:</strong> {source}</p>
                  <p style=\"margin:0;\"><a href=\"{link}\">Read full article</a></p>
                </div>
                """.format(
                    headline=safe_headline,
                    summary_list=summary_list,
                    source=safe_source,
                    link=safe_link,
                )
            )
        return "\n".join(blocks)
