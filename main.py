#!/usr/bin/env python3
"""
Bot de trading crypto - Cloud 24/7
Scan automatique toutes les 30 minutes
Alertes Telegram pour les setups valides
"""

import os
import time
import schedule
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
from telegram_notifier import TelegramNotifier
from signal_detector import SignalDetector

class CryptoTradingBot:
    def __init__(self):
        """Initialise le bot avec support Proxy SOCKS5"""
        # Récupération des identifiants depuis les variables Railway
        vpn_user = os.getenv('VPN_USER')
        vpn_pass = os.getenv('VPN_PASS')
        
        # URL du proxy SOCKS5 NordVPN (Suisse)
        # Note : On utilise le port 1080 pour le SOCKS5
        proxy_url = f'socks5://{vpn_user}:{vpn_pass}@ch339.nordvpn.com:1080'
        
        self.exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
            'proxies': {
                'http': proxy_url,
                'https': proxy_url,
            }
        })
        # Telegram notifier
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        self.notifier = TelegramNotifier(telegram_token, telegram_chat_id)
        self.signal_detector = SignalDetector()
        
        # Coins à surveiller
        self.watchlist = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
            'ADA/USDT', 'DOGE/USDT', 'LINK/USDT', 'AVAX/USDT', 'MATIC/USDT',
            'DOT/USDT', 'UNI/USDT', 'LTC/USDT', 'ATOM/USDT', 'ETC/USDT'
        ]
        
        # Timeframes
        self.timeframes = ['1h', '4h', '1d']
        
        # Tracker des signaux déjà envoyés (éviter spam)
        self.sent_signals = {}
        
        print("🚀 Bot initialisé avec succès!")
        print(f"📊 Surveillance de {len(self.watchlist)} coins")
        print(f"⏰ Scan toutes les 30 minutes")
        
    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        """Récupère les données OHLCV"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"❌ Erreur {symbol} {timeframe}: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calcule les indicateurs techniques"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_18'] = df['close'].ewm(span=18, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Bollinger Bands
        sma = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['bb_upper'] = sma + (std * 2)
        df['bb_middle'] = sma
        df['bb_lower'] = sma - (std * 2)
        
        # Distance aux bandes
        df['dist_bb_lower'] = ((df['close'] - df['bb_lower']) / df['close'] * 100)
        df['dist_bb_upper'] = ((df['bb_upper'] - df['close']) / df['close'] * 100)
        
        return df
    
    def get_multi_timeframe_data(self, symbol):
        """Récupère les données sur plusieurs timeframes"""
        data = {}
        
        for tf in self.timeframes:
            df = self.fetch_ohlcv(symbol, tf)
            if df is not None and len(df) >= 200:  # Assez de données pour EMA 200
                df = self.calculate_indicators(df)
                data[tf] = df
            time.sleep(0.3)  # Rate limiting
        
        return data
    
    def scan_market(self):
        """Scan complet du marché"""
        print(f"\n{'='*60}")
        print(f"🔍 SCAN MARCHÉ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        all_signals = []
        
        for symbol in self.watchlist:
            try:
                print(f"\n📊 Analyse {symbol}...")
                
                # Récupérer données multi-timeframe
                data = self.get_multi_timeframe_data(symbol)
                
                if not data or '4h' not in data:
                    print(f"⚠️  Données insuffisantes pour {symbol}")
                    continue
                
                # Détecter les signaux
                signals = self.signal_detector.detect_signals(symbol, data)
                
                if signals:
                    all_signals.extend(signals)
                    
                    # Vérifier si signal déjà envoyé récemment (< 6h)
                    for signal in signals:
                        signal_key = f"{symbol}_{signal['type']}_{signal['timeframe']}"
                        last_sent = self.sent_signals.get(signal_key, 0)
                        
                        # Envoyer seulement si > 6h depuis dernier signal
                        if time.time() - last_sent > 6 * 3600:
                            self.notifier.send_signal(signal)
                            self.sent_signals[signal_key] = time.time()
                            print(f"✅ Signal {signal['type']} envoyé pour {symbol}")
                        else:
                            print(f"⏭️  Signal déjà envoyé récemment pour {symbol}")
                
            except Exception as e:
                print(f"❌ Erreur lors de l'analyse de {symbol}: {e}")
                continue
        
        # Résumé
        print(f"\n{'='*60}")
        print(f"📈 RÉSUMÉ DU SCAN")
        print(f"{'='*60}")
        print(f"Signaux détectés: {len(all_signals)}")
        
        if all_signals:
            longs = sum(1 for s in all_signals if s['type'] == 'LONG')
            shorts = sum(1 for s in all_signals if s['type'] == 'SHORT')
            print(f"  - LONG: {longs}")
            print(f"  - SHORT: {shorts}")
        else:
            print("Aucun signal fort détecté")
        
        print(f"\n⏰ Prochain scan dans 30 minutes...")
        
        return all_signals
    
    def run_scheduled_scan(self):
        """Exécute un scan programmé"""
        try:
            self.scan_market()
        except Exception as e:
            print(f"❌ Erreur lors du scan: {e}")
            # Envoyer notification d'erreur
            try:
                self.notifier.send_error(str(e))
            except:
                pass
    
    def start(self):
        """Démarre le bot en mode continu"""
        print("\n" + "="*60)
        print("🤖 DÉMARRAGE DU BOT CRYPTO")
        print("="*60)
        
        # Premier scan immédiat
        self.run_scheduled_scan()
        
        # Programmer les scans toutes les 30 minutes
        schedule.every(30).minutes.do(self.run_scheduled_scan)
        
        # Boucle infinie
        print("\n✅ Bot en mode surveillance 24/7")
        print("🔔 Vous recevrez des alertes Telegram pour chaque signal")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check toutes les minutes

def main():
    """Point d'entrée principal"""
    # Vérifier les variables d'environnement
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("❌ ERREUR: Variable TELEGRAM_BOT_TOKEN manquante")
        print("💡 Configure-la dans Railway/Render")
        return
    
    if not os.getenv('TELEGRAM_CHAT_ID'):
        print("❌ ERREUR: Variable TELEGRAM_CHAT_ID manquante")
        print("💡 Configure-la dans Railway/Render")
        return
    
    # Créer et démarrer le bot
    bot = CryptoTradingBot()
    bot.start()

if __name__ == "__main__":
    main()
