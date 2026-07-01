#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Verificando dependências do sistema..."
if ! python3 -c "import gi; gi.require_version('AyatanaAppIndicator3', '0.1'); from gi.repository import AyatanaAppIndicator3" >/dev/null 2>&1; then
    echo "Instalando gir1.2-ayatanaappindicator3-0.1 (requer sudo)..."
    sudo apt-get update
    sudo apt-get install -y gir1.2-ayatanaappindicator3-0.1
fi

if ! python3 -c "import cairo" >/dev/null 2>&1; then
    echo "Instalando python3-gi-cairo (requer sudo)..."
    sudo apt-get install -y python3-gi-cairo
fi

mkdir -p ~/.config/systemd/user
cp "$SCRIPT_DIR/systemd-user/claude-usage-monitor.service" ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now claude-usage-monitor.service

echo ""
echo "Instalado. O ícone deve aparecer na barra superior em poucos segundos."
echo "Ver logs:    journalctl --user -u claude-usage-monitor -f"
echo "Reiniciar:   systemctl --user restart claude-usage-monitor"
echo "Desativar:   systemctl --user disable --now claude-usage-monitor"
