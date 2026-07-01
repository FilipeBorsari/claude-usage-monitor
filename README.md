# 📊 Claude Usage Monitor

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/python-3-blue.svg)](https://www.python.org/)
[![GTK 3](https://img.shields.io/badge/GTK-3-orange.svg)](https://www.gtk.org/)
[![Platform: Linux/GNOME](https://img.shields.io/badge/platform-Linux%20%2F%20GNOME-informational.svg)](#-requisitos)
[![Made for Claude Code](https://img.shields.io/badge/made%20for-Claude%20Code-6b4fbb.svg)](https://claude.com/claude-code)

> Um ícone na barra superior do GNOME que mostra, de forma simples e rápida, quanto do seu plano Claude Code já foi consumido — sem precisar abrir o terminal e digitar `/usage`.

<p align="center">
  <sub>🟢 verde = tranquilo &nbsp;·&nbsp; 🟡 amarelo = atenção &nbsp;·&nbsp; 🔴 vermelho = pertinho do limite</sub>
</p>

---

## ✨ Por que isso existe

Eu queria uma extensão simples que me mostrasse, de forma clara e rápida, o meu uso do Claude Code — sem fricção, sem precisar lembrar de rodar um comando (eu sei que é só dar /usage, mas eu queria ver o negócio impresso ali na minha cara o tempo todo).

## 🚀 Funcionalidades

| Recurso | Descrição |
|---|---|
| 🎯 **Gauge colorido** | Ícone na tray com anel de progresso (verde/amarelo/vermelho) e o `%` da sessão atual ao lado |
| 🕔 **Sessão (5h)** | Uso da janela de 5 horas, igual ao `/usage` da CLI oficial |
| 📆 **Semana (7d)** | Uso da janela semanal, com data/hora exata de reset |
| 🧮 **Tokens locais** | Total de tokens consumidos nas últimas 24h e 7 dias, lidos direto dos logs de sessão |
| 🔄 **Auto-refresh** | Atualiza a cada 60s, ou na hora com um clique em "Atualizar agora" |
| 🔐 **Zero configuração** | Reaproveita o token OAuth que o próprio Claude Code já salva localmente |
| 🧩 **Systemd integrado** | Sobe automaticamente no login como serviço de usuário |

## 🛠️ Como funciona

```
┌────────────────────┐      GET /api/oauth/usage       ┌───────────────────────┐
│  ~/.claude/         │ ───────────────────────────────▶│  api.anthropic.com    │
│  .credentials.json  │  (mesmo endpoint do `/usage`)    │  (quota do plano)     │
└────────────────────┘                                   └───────────────────────┘
          │
          │ token OAuth (renovado automaticamente)
          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        claude-usage-monitor (tray icon)                      │
└──────────────────────────────────────────────────────────────────────────────┘
          ▲
          │ soma tokens de uso
          │
┌────────────────────────────┐
│ ~/.claude/projects/**/*.jsonl │  (logs locais de sessão)
└────────────────────────────┘
```

- **Quota do plano**: consulta o mesmo endpoint que o `/usage` da CLI usa (`GET /api/oauth/usage`), autenticado com o token OAuth salvo em `~/.claude/.credentials.json`. O token é renovado automaticamente quando expira, do mesmo jeito que a CLI faz.
- **Tokens locais**: soma o campo `usage` de cada mensagem nos logs JSONL de sessão (`~/.claude/projects/**/*.jsonl`), sem depender de rede.
- **Ícone**: um pequeno gauge desenhado com Cairo, recolorido conforme a severidade retornada pela API.

## 📦 Requisitos

- Linux com GNOME (ou outro ambiente compatível com [AppIndicator](https://github.com/AyatanaIndicators/libayatana-appindicator))
- Python 3
- [Claude Code](https://claude.com/claude-code) já autenticado (`~/.claude/.credentials.json` precisa existir)
- Pacotes de sistema: `gir1.2-ayatanaappindicator3-0.1` e `python3-gi-cairo` (o instalador cuida disso pra você)

## ⚡ Instalação

Instala e sobe como serviço de usuário, com autostart no login:

```bash
./install.sh
```

O script verifica as dependências de sistema, instala o que faltar (pode pedir `sudo`) e habilita o serviço via `systemd --user`. Em poucos segundos o ícone aparece na barra superior.

## 🎛️ Gerenciando o serviço

```bash
systemctl --user status claude-usage-monitor       # status atual
journalctl --user -u claude-usage-monitor -f        # logs em tempo real
systemctl --user restart claude-usage-monitor       # reiniciar
systemctl --user disable --now claude-usage-monitor # desativar e parar
```

## 🧪 Rodando manualmente (sem systemd)

```bash
python3 main.py
```

## 📁 Estrutura do projeto

```
claude-usage-monitor/
├── main.py                        # ponto de entrada
├── install.sh                     # instalador (deps + systemd)
├── systemd-user/
│   └── claude-usage-monitor.service
└── claude_usage_monitor/
    ├── app.py                     # UI: indicator, menu, loop de refresh
    ├── icon.py                    # desenha o gauge (Cairo)
    ├── usage_api.py               # consulta a quota do plano
    ├── credentials.py             # lê/renova o token OAuth
    └── local_stats.py             # soma tokens dos logs locais
```

## 🗺️ Roadmap

- [ ] Notificação quando cruzar o limiar de 90%
- [ ] Suporte a outros indicadores (KStatusNotifierItem/KDE)
- [ ] Empacotamento (`.deb` / Flatpak)

## 🤝 Contribuindo

Issues e PRs são bem-vindos. É um projeto pequeno e pessoal, então mantenha as mudanças simples e alinhadas com o objetivo original: mostrar o uso de forma clara e rápida.

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE).
