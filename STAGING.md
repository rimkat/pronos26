# Environnement de staging

Objectif : avoir une copie de l'app (frontend + backend + base) séparée de
la prod, pour tester avant de pousser sur `main`.

## 1. Branche Git

Toute nouvelle fonctionnalité se développe sur une branche, se fusionne
dans `staging` pour test, puis dans `main` pour la prod.

```bash
git checkout -b staging
git push -u origin staging
```

Workflow :
```
feature/xxx  --> merge --> staging (auto-déployé en staging) --> test --> merge --> main (prod)
```

## 2. Base de données (MongoDB Atlas)

Pas besoin d'un nouveau cluster : on réutilise le même cluster Atlas mais
avec un nom de base différent, complètement isolé de la prod.

- Prod  : `DB_NAME=pronos26`
- Staging : `DB_NAME=pronos26_staging`

La base est créée automatiquement au premier écrit, rien à faire côté Atlas.

## 3. Backend (Render)

Créer un **second Web Service** sur Render :

1. Render Dashboard > New > Web Service > sélectionner le repo `pronos26`.
2. Branch : `staging` (au lieu de `main`).
3. Root directory : `backend`.
4. Build command : `./build.sh`
5. Start command : (la même que la prod, ex. `uvicorn server:app --host 0.0.0.0 --port $PORT`)
6. Nom du service : `pronos26-api-staging`.
7. Onglet Environment > coller les variables de
   `backend/.env.staging.example` (générer de **nouveaux** `JWT_SECRET`
   et `ADMIN_TOKEN`, différents de la prod).

Render redéploiera automatiquement ce service à chaque push sur `staging`.

## 4. Frontend (Vercel)

Pas besoin d'un nouveau projet : Vercel déploie déjà automatiquement
chaque branche sur une URL "Preview" stable :
`https://pronos26-git-staging-<ton-compte>.vercel.app`

Il faut juste lui donner la bonne URL d'API :

1. Vercel Dashboard > projet `pronos26` > Settings > Environment Variables.
2. Ajouter `VITE_API_URL` = `https://pronos26-api-staging.onrender.com`
   et cocher uniquement l'environnement **Preview** (pas Production).
3. Pousser sur `staging` → Vercel build automatiquement avec cette valeur.

## 5. CORS

Sur le service Render staging, mettre :
```
CORS_ORIGINS=https://pronos26-git-staging-<ton-compte>.vercel.app
```
(remplacer `<ton-compte>` par ton compte/équipe Vercel - visible dans l'URL
du déploiement preview).

## 6. Sécurité - à corriger

`backend/.env` est actuellement **versionné dans git** (avec les vrais
secrets de prod : mot de passe Mongo, JWT_SECRET, clé Zafronix). À faire
séparément :
- ajouter `backend/.env` au `.gitignore`
- le retirer du suivi : `git rm --cached backend/.env`
- régénérer les secrets exposés (mot de passe Mongo Atlas, JWT_SECRET,
  ADMIN_TOKEN) puisqu'ils sont visibles dans l'historique du repo.

## Résumé des URLs

| | Prod | Staging |
|---|---|---|
| Frontend | https://pronos26.vercel.app (ou domaine custom) | https://pronos26-git-staging-<compte>.vercel.app |
| Backend | https://pronos26.onrender.com | https://pronos26-api-staging.onrender.com |
| DB | `pronos26` | `pronos26_staging` |
| Branche | `main` | `staging` |
