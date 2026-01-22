# 🤖 Bot Trading Crypto - Cloud 24/7

Bot automatique qui surveille les marchés crypto 24/7 et t'envoie des alertes Telegram pour les setups de trading valides.

## ✨ Fonctionnalités

- ✅ **Surveillance 24/7** sans ordi allumé
- ✅ **Scan automatique** toutes les 30 minutes
- ✅ **Alertes Telegram** uniquement pour les setups valides
- ✅ **Multi-timeframes** : 1h, 4h, 1d
- ✅ **Confluence d'indicateurs** : RSI, EMA, Bollinger
- ✅ **Filtres stricts** pour éviter les faux signaux
- ✅ **0€/mois** avec Railway (tier gratuit)

## 📱 Étape 1 : Créer ton Bot Telegram

### 1.1 Créer le bot

1. Ouvre Telegram
2. Cherche **@BotFather**
3. Envoie `/newbot`
4. Donne un nom : `Mon Bot Crypto`
5. Donne un username : `ton_nom_crypto_bot`
6. **COPIE LE TOKEN** qu'il te donne (ex: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 1.2 Obtenir ton Chat ID

1. Cherche **@userinfobot** sur Telegram
2. Envoie `/start`
3. **COPIE TON CHAT ID** (ex: `987654321`)

## 🚀 Étape 2 : Déployer sur Railway (GRATUIT)

### 2.1 Créer un compte Railway

1. Va sur [railway.app](https://railway.app)
2. Clique sur **"Start a New Project"**
3. Connecte-toi avec GitHub

### 2.2 Déployer le bot

#### Option A : Depuis GitHub (Recommandé)

1. **Upload le code sur GitHub** :
   ```bash
   # Crée un nouveau repo sur github.com
   # Puis depuis ton terminal :
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/TON_USERNAME/crypto-bot.git
   git push -u origin main
   ```

2. **Sur Railway** :
   - Clique sur "Deploy from GitHub repo"
   - Sélectionne ton repo `crypto-bot`
   - Railway détecte automatiquement Python

#### Option B : Deploy Direct (Plus rapide)

1. **Sur Railway** :
   - Clique sur "Empty Project"
   - Clique sur "+ New" → "Empty Service"
   - Dans Settings → Source, connecte ton GitHub

2. **Upload les fichiers** :
   - Zippe tous les fichiers du dossier `crypto_bot/`
   - Drag & drop le .zip dans Railway

### 2.3 Configurer les variables d'environnement

1. Dans Railway, clique sur ton service
2. Va dans **"Variables"**
3. Ajoute ces 2 variables :

```
TELEGRAM_BOT_TOKEN = ton_token_de_botfather
TELEGRAM_CHAT_ID = ton_chat_id
```

**Exemple** :
```
TELEGRAM_BOT_TOKEN = 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID = 987654321
```

4. Clique sur **"Deploy"**

### 2.4 Vérification

1. Le bot démarre automatiquement
2. Tu reçois un message Telegram : **"🤖 BOT CRYPTO DÉMARRÉ"**
3. Dans les logs Railway, tu vois : **"✅ Bot en mode surveillance 24/7"**

**C'est tout !** Le bot tourne maintenant 24/7 🎉

## 📊 Comment ça marche

### Scan toutes les 30 minutes

Le bot analyse :
- BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, AVAX, MATIC, DOT, UNI, LTC, ATOM, ETC
- Sur 3 timeframes : 1h, 4h, 1d
- Avec RSI, EMA 9/18/200, Bollinger Bands

### Critères de signal LONG 🟢

**Confluence requise** (score ≥ 5/10) :
- ✅ RSI 4h < 30 (oversold) → +3 points
- ✅ Prix < 2% de Bollinger lower → +2 points
- ✅ RSI 1d < 40 → +2 points
- ✅ Volume +20% vs moyenne → +1 point

**Filtres anti-faux signaux** :
- ❌ Skip si chute libre (3 bougies rouges consécutives > -3%)
- ❌ Skip si signal envoyé < 6h

### Critères de signal SHORT 🔴

**Confluence requise** (score ≥ 5/10) :
- ✅ RSI 4h > 70 (overbought) → +3 points
- ✅ Prix < 2% de Bollinger upper → +2 points
- ✅ RSI 1d > 65 → +2 points
- ✅ Volume +20% vs moyenne → +1 point

**Filtres anti-faux signaux** :
- ❌ Skip si rallye violent (3 bougies vertes consécutives > +3%)
- ❌ Skip si signal envoyé < 6h

### Format des alertes

Tu reçois sur Telegram :
```
🟢 LONG SIGNAL 🟢

💎 BTC/USDT
⏰ Timeframe: 4h
📊 Score: 7/10

💰 PRIX
Entry: 90000
Stop: 87300 (-3%)
Target: 93600 (+4.0%)
R/R: 1:1.3

📈 RSI
1h: 35.2
4h: 28.5
1d: 38.9

✅ RAISONS
• RSI 4h=28.5 (oversold)
• Prix à 1.5% de BB_lower
• RSI 1d=38.9 (low)
• Volume +25% vs moyenne

⏰ 2026-01-22 11:30:00

⚠️ FOMC dans 5 jours - Position sizing réduit recommandé
```

## 🛠️ Customisation

### Modifier les coins surveillés

Dans `main.py` ligne 30 :
```python
self.watchlist = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT',
    # Ajoute tes coins ici
]
```

### Modifier la fréquence de scan

Dans `main.py` ligne 172 :
```python
schedule.every(30).minutes.do(self.run_scheduled_scan)
# Change 30 par 15 pour scan toutes les 15 min
```

### Ajuster les seuils RSI

Dans `signal_detector.py` ligne 12 :
```python
self.rsi_oversold = 30  # Change à 25 pour signaux plus stricts
self.rsi_overbought = 70  # Change à 75 pour signaux plus stricts
```

## 📈 Monitoring

### Voir les logs en temps réel

Dans Railway :
1. Clique sur ton service
2. Va dans **"Deployments"**
3. Clique sur le dernier déploiement
4. Les logs s'affichent en temps réel

### Messages typiques dans les logs

```
🔍 SCAN MARCHÉ - 2026-01-22 11:00:00
📊 Analyse BTC/USDT...
📊 Analyse ETH/USDT...
✅ Signal LONG envoyé pour BTC/USDT
📈 RÉSUMÉ DU SCAN
Signaux détectés: 1
  - LONG: 1
  - SHORT: 0
⏰ Prochain scan dans 30 minutes...
```

## 💰 Coûts

**Railway Tier Gratuit** :
- ✅ $5 de crédit gratuit/mois
- ✅ Suffisant pour ce bot (~$3/mois)
- ✅ Pas de carte bancaire requise

Si tu dépasses :
- **Hobby Plan** : $5/mois (illimité)

## 🔧 Maintenance

### Arrêter le bot

Dans Railway → Service → **Settings** → **Sleep Service**

### Redémarrer le bot

Dans Railway → Service → **Deployments** → **Redeploy**

### Mettre à jour le code

1. Modifie le code localement
2. Push sur GitHub :
   ```bash
   git add .
   git commit -m "Update"
   git push
   ```
3. Railway redéploie automatiquement

## 🐛 Troubleshooting

### Pas de message au démarrage

- Vérifie que `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` sont bien configurés
- Vérifie que tu as envoyé `/start` à ton bot sur Telegram

### Erreur "Rate limit exceeded"

- Normal si tu scan trop souvent
- Augmente le délai dans le code (ligne 57 : `time.sleep(0.5)`)

### Bot ne détecte aucun signal

- C'est normal ! Les filtres sont stricts
- En moyenne : 2-5 signaux/jour sur 15 coins
- Si tu veux plus de signaux, baisse les seuils dans `signal_detector.py`

### Bot s'arrête après quelques heures

- Vérifie les logs Railway pour l'erreur
- Possible : problème de réseau avec Binance API
- Le bot redémarre automatiquement sur Railway

## 📞 Support

Si tu as des questions :
1. Vérifie les logs Railway
2. Regarde la section Troubleshooting ci-dessus
3. Les erreurs sont aussi envoyées sur Telegram

## 🎯 Next Steps

Une fois le bot en route, tu peux :
- ✅ Ajouter un calendrier économique (FOMC, CPI...)
- ✅ Créer un dashboard web pour visualiser les signaux
- ✅ Ajouter un système de backtesting
- ✅ Tracker la performance des signaux

---

**Enjoy trading! 🚀📈**
