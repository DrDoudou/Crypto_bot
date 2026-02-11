#!/usr/bin/env python3
"""
Bot de trading crypto avec analyse IA Claude
Scan automatique toutes les 30 minutes avec détection LONG et SHORT
"""

import os
import time
import schedule
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
from telegram_notifier_ai import TelegramNotifier
from claude_analyst import ClaudeAnalyst

class ClaudeCryptoBot:
    def __init__(self):
        """Initialise le bot avec Claude AI"""
        
        print("="*60)
        print("🚀 INITIALISATION CLAUDE AI CRYPTO BOT")
        print("="*60)
        
        # Configuration Exchange (on passe à Binance, plus fiable)
        print("📡 Configuration exchange...")
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        print("✅ Exchange: Binance")
        
        # Initialisation Telegram
        print("📱 Configuration Telegram...")
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.notifier = TelegramNotifier(telegram_token, telegram_chat_id)
        
        # Initialisation Claude AI
        print("🧠 Configuration Claude AI...")
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not anthropic_api_key:
            raise ValueError("❌ ANTHROPIC_API_KEY manquante dans les variables d'environnement")
        
        self.analyst = ClaudeAnalyst(anthropic_api_key)
        print("✅ Claude AI connecté")
        
        # Watchlist (réduite pour commencer, ajoute selon budget)
        self.watchlist = [
            'BTC/USDT',
            'ETH/USDT', 
            'SOL/USDT',
            'BNB/USDT',
            'XRP/USDT',
        ]
        
        self.timeframes = ['1h', '4h', '1d']
        self.sent_signals = {}
        
        # Stats quotidiennes
        self.daily_stats = {
            'total_analyses': 0,
            'total_signals': 0,
            'long_signals': 0,
            'short_signals': 0,
            'confidences': [],
            'confluences': [],
            'top_coins': []
        }
        
        print(f"✅ Bot initialisé avec succès!")
        print(f"📊 Surveillance de {len(self.watchlist)} coins")
        print("="*60)

    def calculate_indicators(self, df):
        """Calcule les indicateurs techniques"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA 9, 18, 200
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_18'] = df['close'].ewm(span=18, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Bollinger Bands
        sma = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['bb_upper'] = sma + (std * 2)
        df['bb_middle'] = sma
        df['bb_lower'] = sma - (std * 2)
        
        return df

    def fetch_data(self, symbol, timeframe, limit=500):
        """Récupère les données historiques avec retry"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Calculer les indicateurs
                df = self.calculate_indicators(df)
                
                return df
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Tentative {attempt+1} échouée pour {symbol} {timeframe}, retry...")
                    time.sleep(2)
                else:
                    print(f"  ❌ Erreur {symbol} {timeframe} après {max_retries} tentatives: {str(e)[:100]}")
                    return None
        
        return None

    def get_market_context(self):
        """Récupère le contexte macro du marché (basé sur BTC)"""
        try:
            # Récupérer données BTC 1D
            df_btc = self.fetch_data('BTC/USDT', '1d', limit=30)
            
            if df_btc is None or len(df_btc) < 10:
                return "Contexte marché indisponible"
            
            latest = df_btc.iloc[-1]
            price = latest['close']
            ema_200 = latest['ema_200']
            rsi = latest['rsi']
            
            # Calculer tendance
            pct_from_ema = ((price - ema_200) / ema_200) * 100
            
            if pct_from_ema > 5:
                trend = "BTC en uptrend (bull market)"
            elif pct_from_ema < -5:
                trend = "BTC en downtrend (bear market)"
            else:
                trend = "BTC en range (marché neutre)"
            
            # Momentum
            if rsi > 60:
                momentum = "momentum haussier"
            elif rsi < 40:
                momentum = "momentum baissier"
            else:
                momentum = "momentum neutre"
            
            return f"{trend}, {momentum}. BTC: ${price:,.0f} ({pct_from_ema:+.1f}% EMA200)"
            
        except Exception as e:
            print(f"⚠️ Erreur contexte marché: {e}")
            return "Contexte marché standard"

    def scan_market(self):
        """Analyse tous les coins via Claude AI"""
        print("\n" + "="*60)
        print(f"🔍 SCAN MARCHÉ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Récupérer contexte macro
        market_context = self.get_market_context()
        print(f"🌍 {market_context}")
        print("="*60)
        
        all_signals = []
        analyzed_count = 0
        
        for symbol in self.watchlist:
            try:
                print(f"\n🔍 Analyse {symbol} via Claude AI...")
                data = {}
                
                # Récupérer données multi-timeframe
                for tf in self.timeframes:
                    df = self.fetch_data(symbol, tf)
                    if df is not None and len(df) >= 200:  # Assez de données
                        data[tf] = df
                        print(f"  ✓ {tf}: {len(df)} bougies")
                    time.sleep(0.5)  # Rate limiting
                
                # Analyser avec Claude si données complètes
                if '4h' in data and '1d' in data:
                    analyzed_count += 1
                    self.daily_stats['total_analyses'] += 1
                    
                    print(f"  🧠 Envoi à Claude pour analyse...")
                    
                    signal = self.analyst.analyze_coin(
                        symbol=symbol,
                        data_1h=data.get('1h'),
                        data_4h=data['4h'],
                        data_1d=data['1d'],
                        market_context=market_context
                    )
                    
                    if signal:
                        print(f"  ✅ Signal {signal['signal']} détecté (confidence: {signal['confidence']}/10)")
                        all_signals.append(signal)
                        
                        # Stats
                        self.daily_stats['total_signals'] += 1
                        if signal['signal'] == 'LONG':
                            self.daily_stats['long_signals'] += 1
                        else:
                            self.daily_stats['short_signals'] += 1
                        
                        self.daily_stats['confidences'].append(signal['confidence'])
                        self.daily_stats['confluences'].append(signal.get('confluence_factors', 0))
                        
                        # Envoyer si nouveau signal
                        signal_key = f"{symbol}_{signal['signal']}_{signal['timeframe']}"
                        last_sent = self.sent_signals.get(signal_key, 0)
                        
                        # Envoyer si > 6h depuis dernier signal
                        if time.time() - last_sent > 6 * 3600:
                            self.notifier.send_claude_signal(signal)
                            self.sent_signals[signal_key] = time.time()
                            print(f"  📤 Signal envoyé sur Telegram")
                        else:
                            print(f"  ⏳ Signal déjà envoyé récemment, skip")
                    else:
                        print(f"  💤 Pas de setup valide")
                else:
                    print(f"  ⚠️ Données insuffisantes pour {symbol}")
                    
            except Exception as e:
                print(f"  ❌ Erreur lors de l'analyse de {symbol}: {e}")
                continue
        
        # Résumé
        print(f"\n{'='*60}")
        print(f"📊 RÉSUMÉ DU SCAN")
        print(f"{'='*60}")
        print(f"🔍 Coins analysés: {analyzed_count}")
        print(f"📡 Signaux détectés: {len(all_signals)}")
        
        if all_signals:
            longs = sum(1 for s in all_signals if s['signal'] == 'LONG')
            shorts = sum(1 for s in all_signals if s['signal'] == 'SHORT')
            print(f"  • LONG: {longs}")
            print(f"  • SHORT: {shorts}")
            
            avg_conf = np.mean([s['confidence'] for s in all_signals])
            print(f"🎯 Confidence moyenne: {avg_conf:.1f}/10")
        else:
            print("💤 Aucun setup valide détecté")
            print("✅ Claude reste vigilant - Protection du capital active")
        
        print(f"\n⏰ Prochain scan dans 30 minutes...")

    def run_scheduled_scan(self):
        """Wrapper pour le scan avec error handling"""
        try:
            self.scan_market()
        except Exception as e:
            print(f"❌ Erreur critique lors du scan: {e}")
            try:
                self.notifier.send_error(f"Erreur scan: {str(e)[:100]}")
            except:
                pass
    
    def send_daily_summary(self):
        """Envoie le résumé quotidien"""
        try:
            stats = self.daily_stats.copy()
            
            if stats['confidences']:
                stats['avg_confidence'] = np.mean(stats['confidences'])
            else:
                stats['avg_confidence'] = 0
            
            if stats['confluences']:
                stats['avg_confluence'] = np.mean(stats['confluences'])
            else:
                stats['avg_confluence'] = 0
            
            stats['top_coins'] = self.watchlist[:5]
            
            self.notifier.send_daily_summary(stats)
            
            # Reset stats
            self.daily_stats = {
                'total_analyses': 0,
                'total_signals': 0,
                'long_signals': 0,
                'short_signals': 0,
                'confidences': [],
                'confluences': [],
                'top_coins': []
            }
            
        except Exception as e:
            print(f"❌ Erreur envoi résumé quotidien: {e}")
    
    def start(self):
        """Démarre le bot"""
        print("\n" + "="*60)
        print("🧠 DÉMARRAGE CLAUDE AI CRYPTO BOT")
        print("="*60)
        
        # Premier scan immédiat
        self.run_scheduled_scan()
        
        # Programmer scans toutes les 30 min
        schedule.every(30).minutes.do(self.run_scheduled_scan)
        
        # Programmer résumé quotidien à 20h
        schedule.every().day.at("20:00").do(self.send_daily_summary)
        
        print("\n✅ Bot en mode surveillance 24/7")
        print("🧠 Claude AI analyse les marchés toutes les 30 min")
        print("📱 Vous recevrez des alertes Telegram pour chaque signal")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Point d'entrée principal"""
    
    # Vérifier variables d'environnement
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'ANTHROPIC_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ ERREUR: Variables d'environnement manquantes:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n💡 Configure ces variables avant de démarrer le bot")
        return
    
    # Démarrer le bot
    bot = ClaudeCryptoBot()
    bot.start()

if __name__ == "__main__":
    main()
