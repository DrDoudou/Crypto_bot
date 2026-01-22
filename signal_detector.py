"""
Module de détection de signaux trading
Filtres stricts pour éviter les faux signaux
"""

import pandas as pd
import numpy as np
from datetime import datetime

class SignalDetector:
    def __init__(self):
        """Initialise le détecteur"""
        # Seuils stricts
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.bb_threshold = 2.0  # % de distance aux bandes
        
    def detect_signals(self, symbol, data):
        """
        Détecte les signaux de trading avec confluence multi-indicateurs
        
        Args:
            symbol: Symbole du coin (ex: BTC/USDT)
            data: Dict avec données par timeframe {'1h': df, '4h': df, '1d': df}
        
        Returns:
            Liste de signaux détectés
        """
        signals = []
        
        # Utiliser 4h comme référence principale
        if '4h' not in data:
            return signals
        
        df_4h = data['4h']
        latest_4h = df_4h.iloc[-1]
        
        # Vérifier données 1h et 1d
        df_1h = data.get('1h')
        df_1d = data.get('1d')
        
        latest_1h = df_1h.iloc[-1] if df_1h is not None else None
        latest_1d = df_1d.iloc[-1] if df_1d is not None else None
        
        # === DÉTECTION LONG ===
        long_signal = self._check_long_setup(
            symbol, latest_4h, latest_1h, latest_1d, df_4h
        )
        if long_signal:
            signals.append(long_signal)
        
        # === DÉTECTION SHORT ===
        short_signal = self._check_short_setup(
            symbol, latest_4h, latest_1h, latest_1d, df_4h
        )
        if short_signal:
            signals.append(short_signal)
        
        return signals
    
    def _check_long_setup(self, symbol, latest_4h, latest_1h, latest_1d, df_4h):
        """
        Vérifie si conditions LONG sont remplies
        Nécessite CONFLUENCE de plusieurs indicateurs
        """
        score = 0
        reasons = []
        
        # Critère 1: RSI 4h oversold (STRICT)
        rsi_4h = latest_4h['rsi']
        if rsi_4h < self.rsi_oversold:
            score += 3
            reasons.append(f"RSI 4h={rsi_4h:.1f} (oversold)")
        elif rsi_4h < 40:
            score += 1
            reasons.append(f"RSI 4h={rsi_4h:.1f} (low)")
        else:
            # Pas assez oversold, pas de signal
            return None
        
        # Critère 2: Prix proche Bollinger lower
        dist_bb_lower = latest_4h['dist_bb_lower']
        if dist_bb_lower < self.bb_threshold:
            score += 2
            reasons.append(f"Prix à {dist_bb_lower:.1f}% de BB_lower")
        
        # Critère 3: Confirmation RSI 1d
        if latest_1d is not None:
            rsi_1d = latest_1d['rsi']
            if rsi_1d < 40:
                score += 2
                reasons.append(f"RSI 1d={rsi_1d:.1f} (low)")
        
        # Critère 4: Volume en augmentation
        if len(df_4h) >= 2:
            vol_current = latest_4h['volume']
            vol_avg = df_4h['volume'].tail(10).mean()
            if vol_current > vol_avg * 1.2:
                score += 1
                reasons.append("Volume +20% vs moyenne")
        
        # Critère 5: Pas de chute libre (vérifier momentum)
        if len(df_4h) >= 3:
            last_3_closes = df_4h['close'].tail(3).values
            # Si les 3 dernières bougies sont en baisse forte, skip
            if all(last_3_closes[i] < last_3_closes[i-1] * 0.97 for i in range(1, 3)):
                return None  # Chute trop forte, pas de signal
        
        # Score minimum requis: 5
        if score < 5:
            return None
        
        # Calculer prix d'entrée, stop et target
        entry_price = latest_4h['close']
        stop_loss = entry_price * 0.97  # -3%
        bb_middle = latest_4h['bb_middle']
        
        # Target: BB middle ou +5%, le plus proche
        target_bb = bb_middle
        target_5pct = entry_price * 1.05
        take_profit = min(target_bb, target_5pct)
        
        risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)
        
        return {
            'type': 'LONG',
            'symbol': symbol,
            'timeframe': '4h',
            'score': score,
            'entry_price': round(entry_price, 8),
            'stop_loss': round(stop_loss, 8),
            'take_profit': round(take_profit, 8),
            'risk_reward': round(risk_reward, 2),
            'reasons': reasons,
            'rsi_4h': round(rsi_4h, 1),
            'rsi_1h': round(latest_1h['rsi'], 1) if latest_1h is not None else None,
            'rsi_1d': round(latest_1d['rsi'], 1) if latest_1d is not None else None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _check_short_setup(self, symbol, latest_4h, latest_1h, latest_1d, df_4h):
        """
        Vérifie si conditions SHORT sont remplies
        Nécessite CONFLUENCE de plusieurs indicateurs
        """
        score = 0
        reasons = []
        
        # Critère 1: RSI 4h overbought (STRICT)
        rsi_4h = latest_4h['rsi']
        if rsi_4h > self.rsi_overbought:
            score += 3
            reasons.append(f"RSI 4h={rsi_4h:.1f} (overbought)")
        elif rsi_4h > 60:
            score += 1
            reasons.append(f"RSI 4h={rsi_4h:.1f} (high)")
        else:
            # Pas assez overbought, pas de signal
            return None
        
        # Critère 2: Prix proche Bollinger upper
        dist_bb_upper = latest_4h['dist_bb_upper']
        if dist_bb_upper < self.bb_threshold:
            score += 2
            reasons.append(f"Prix à {dist_bb_upper:.1f}% de BB_upper")
        
        # Critère 3: Confirmation RSI 1d
        if latest_1d is not None:
            rsi_1d = latest_1d['rsi']
            if rsi_1d > 65:
                score += 2
                reasons.append(f"RSI 1d={rsi_1d:.1f} (high)")
        
        # Critère 4: Volume en augmentation (signe de climax)
        if len(df_4h) >= 2:
            vol_current = latest_4h['volume']
            vol_avg = df_4h['volume'].tail(10).mean()
            if vol_current > vol_avg * 1.2:
                score += 1
                reasons.append("Volume +20% vs moyenne")
        
        # Critère 5: Pas de rallye violent en cours
        if len(df_4h) >= 3:
            last_3_closes = df_4h['close'].tail(3).values
            # Si les 3 dernières bougies sont en hausse forte, skip
            if all(last_3_closes[i] > last_3_closes[i-1] * 1.03 for i in range(1, 3)):
                return None  # Rallye trop fort, risqué de shorter
        
        # Score minimum requis: 5
        if score < 5:
            return None
        
        # Calculer prix d'entrée, stop et target
        entry_price = latest_4h['close']
        stop_loss = entry_price * 1.03  # +3%
        bb_middle = latest_4h['bb_middle']
        
        # Target: BB middle ou -5%, le plus proche
        target_bb = bb_middle
        target_5pct = entry_price * 0.95
        take_profit = max(target_bb, target_5pct)
        
        risk_reward = (entry_price - take_profit) / (stop_loss - entry_price)
        
        return {
            'type': 'SHORT',
            'symbol': symbol,
            'timeframe': '4h',
            'score': score,
            'entry_price': round(entry_price, 8),
            'stop_loss': round(stop_loss, 8),
            'take_profit': round(take_profit, 8),
            'risk_reward': round(risk_reward, 2),
            'reasons': reasons,
            'rsi_4h': round(rsi_4h, 1),
            'rsi_1h': round(latest_1h['rsi'], 1) if latest_1h is not None else None,
            'rsi_1d': round(latest_1d['rsi'], 1) if latest_1d is not None else None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
