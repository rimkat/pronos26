# PRD — Pronos 2026 (Coupe du Monde 2026)

## Original problem statement
Application web de pronostics football pour la Coupe du Monde 2026 inspirée L'Équipe. Auth JWT, MongoDB, calendrier 48 équipes / 12 groupes, navigation par date, classement par groupe en direct, calculateur de points (1N2 +1 / diff +1 / score exact +3 bonus).

## Stack
- Backend : FastAPI + Motor (Mongo) + bcrypt + PyJWT
- Frontend : React 19 + Tailwind + shadcn/ui + sonner + lucide
- Auth : JWT Bearer (localStorage)

## Architecture
- backend/server.py : routes API (/api/auth, /api/matches, /api/predictions, /api/admin, /api/leaderboard, /api/dashboard, /api/standings)
- backend/fixtures.py : génération des 72 matchs phase de groupes WC 2026
- frontend/src : AuthContext + ThemeContext + pages (Matches, Login, Register, Dashboard, Leaderboard) + components (NavBar, DateNav, MatchRow, GroupSection, StandingsDrawer)

## Implémenté (Feb 2026)
- Inscription / connexion JWT (email + pseudo + password)
- Hub matchs par date avec navigation horizontale style L'Équipe
- 72 matchs WC 2026 seedés (12 groupes × 3 journées × 2 matchs), 3 affiches du brief forcées (Qatar-Suisse 21h, Brésil-Maroc 0h, Haïti-Écosse 3h)
- Saisie pronostic 2 inputs numériques avec sauvegarde auto (debounce 700ms)
- Drawer "Classement" par groupe avec calcul live (Pts, J, G, N, P, Diff)
- Calculateur de points serveur (1N2 +1, diff +1, score exact +3)
- Endpoint admin protégé pour saisir résultats (recalcule auto les points)
- Tableau de bord utilisateur (points totaux, rang, nb pronos)
- Classement général de tous les pronostiqueurs
- Bascule thème sombre/clair (dark par défaut)

## Backlog
- P1 : Phase à élimination directe (1/16, 1/8, 1/4, 1/2, finale) — pour l'instant uniquement phase de groupes
- P1 : Système de ligues privées entre amis
- P2 : Notifications avant kick-off
- P2 : Stats avancées (% de bons pronos par compétition)
- P2 : Page profil avec avatar
EOF
