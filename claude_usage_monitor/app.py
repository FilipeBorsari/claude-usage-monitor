import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import Gtk, GLib, AyatanaAppIndicator3 as AppIndicator3

from datetime import datetime, timezone

from . import usage_api, local_stats, icon

APP_ID = "claude-usage-monitor"
REFRESH_SECONDS = 60


def _format_resets_at(iso_ts):
    if not iso_ts:
        return "?"
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except ValueError:
        return "?"
    local_dt = dt.astimezone()
    now = datetime.now(timezone.utc).astimezone()
    delta = local_dt - now
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    if delta.total_seconds() <= 0:
        return "agora"
    if hours > 0:
        return f"em {hours}h{minutes:02d}m ({local_dt.strftime('%H:%M')})"
    return f"em {minutes}m ({local_dt.strftime('%H:%M')})"


def _format_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


class QuotaRow(Gtk.Box):
    def __init__(self, title):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.set_border_width(6)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.title_label = Gtk.Label(label=title, xalign=0)
        self.pct_label = Gtk.Label(label="--%", xalign=1)
        header.pack_start(self.title_label, True, True, 0)
        header.pack_end(self.pct_label, False, False, 0)
        self.pack_start(header, False, False, 0)

        self.bar = Gtk.ProgressBar()
        self.bar.set_show_text(False)
        self.pack_start(self.bar, False, False, 0)

        self.reset_label = Gtk.Label(label="", xalign=0)
        self.reset_label.get_style_context().add_class("dim-label")
        self.pack_start(self.reset_label, False, False, 0)

    def update(self, percent, resets_at):
        if percent is None:
            self.pct_label.set_text("?")
            self.bar.set_fraction(0)
            self.reset_label.set_text("sem dados")
            return
        self.pct_label.set_text(f"{percent:.0f}%")
        self.bar.set_fraction(max(0.0, min(1.0, percent / 100.0)))
        self.reset_label.set_text(f"reinicia {_format_resets_at(resets_at)}")


class StatsRow(Gtk.Box):
    def __init__(self, title):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_border_width(6)
        self.title_label = Gtk.Label(label=title, xalign=0)
        self.value_label = Gtk.Label(label="--", xalign=1)
        self.pack_start(self.title_label, True, True, 0)
        self.pack_end(self.value_label, False, False, 0)

    def update(self, text):
        self.value_label.set_text(text)


class UsageMonitorApp:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            APP_ID,
            "utilities-system-monitor-symbolic",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Claude Usage")

        self.menu = Gtk.Menu()
        self._build_menu()
        self.indicator.set_menu(self.menu)

        self.refresh()
        GLib.timeout_add_seconds(REFRESH_SECONDS, self._on_timer)

    def _build_menu(self):
        self.status_item = Gtk.MenuItem(label="Claude — atualizando...")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)
        self.menu.append(Gtk.SeparatorMenuItem())

        self.session_row = QuotaRow("Sessão (5h)")
        session_item = Gtk.MenuItem()
        session_item.add(self.session_row)
        session_item.set_sensitive(False)
        self.menu.append(session_item)

        self.week_row = QuotaRow("Semana (7d)")
        week_item = Gtk.MenuItem()
        week_item.add(self.week_row)
        week_item.set_sensitive(False)
        self.menu.append(week_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        self.local_24h_row = StatsRow("Tokens (24h)")
        local_24h_item = Gtk.MenuItem()
        local_24h_item.add(self.local_24h_row)
        local_24h_item.set_sensitive(False)
        self.menu.append(local_24h_item)

        self.local_7d_row = StatsRow("Tokens (7 dias)")
        local_7d_item = Gtk.MenuItem()
        local_7d_item.add(self.local_7d_row)
        local_7d_item.set_sensitive(False)
        self.menu.append(local_7d_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        refresh_item = Gtk.MenuItem(label="Atualizar agora")
        refresh_item.connect("activate", self._on_refresh_clicked)
        self.menu.append(refresh_item)

        quit_item = Gtk.MenuItem(label="Sair")
        quit_item.connect("activate", self._on_quit)
        self.menu.append(quit_item)

        self.menu.show_all()

    def _on_timer(self):
        self.refresh()
        return True

    def _on_refresh_clicked(self, _widget):
        self.refresh()

    def _on_quit(self, _widget):
        Gtk.main_quit()

    def refresh(self):
        try:
            data = usage_api.fetch_usage()
            summary = usage_api.summarize(data)
            error = None
        except Exception as e:
            summary = None
            error = str(e)

        stats = local_stats.compute()

        if summary is not None:
            session = summary["session"]
            week = summary["week"]
            self.session_row.update(session["percent"], session["resets_at"])
            self.week_row.update(week["percent"], week["resets_at"])

            worst_percent = max(
                p for p in (session["percent"], week["percent"]) if p is not None
            ) if (session["percent"] is not None or week["percent"] is not None) else None
            worst_severity = session["severity"] if (session["percent"] or 0) >= (week["percent"] or 0) else week["severity"]

            self.status_item.set_label(
                f"Sessão {session['percent']:.0f}% · Semana {week['percent']:.0f}%"
                if session["percent"] is not None and week["percent"] is not None
                else "Claude — dados parciais"
            )
            self.indicator.set_icon_full(icon.render(worst_percent, worst_severity), "Claude usage")
            self.indicator.set_label(
                f"{session['percent']:.0f}%" if session["percent"] is not None else "?", ""
            )
        else:
            self.status_item.set_label(f"Erro: {error}")
            self.indicator.set_icon_full(icon.render(None, "error"), "Claude usage")
            self.indicator.set_label("!", "")

        self.local_24h_row.update(f"{_format_tokens(stats['24h']['total'])} · {stats['24h']['messages']} msgs")
        self.local_7d_row.update(f"{_format_tokens(stats['7d']['total'])} · {stats['7d']['messages']} msgs")

    def run(self):
        Gtk.main()


def main():
    app = UsageMonitorApp()
    app.run()


if __name__ == "__main__":
    main()
