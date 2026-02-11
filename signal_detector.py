"""
Module de détection de signaux trading - VERSION 2.0
Filtres ULTRA-STRICTS pour éviter les falling knives
Ajout: tendance, structure, volume directionnel, divergences
"""

import pandas as pd
import numpy as np
from datetime import datetime

class SignalDetector:
    def __init__(self):
        """Initialise le détecteur avec seuils stricts"""
        # Seuils RSI
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        # Seuils Bollinger
        self.bb_threshold = 2.0  # % de distance aux bandes
        
        # Score minimum AUGMENTÉ
        self.min_score_long = 8   # Au lieu de 5
        self.min_score_short = 8
        
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
            symbol, latest_4h, latest_1h, latest_1d, df_4h, df_1d
        )
        if long_signal:
            signals.append(long_signal)
        
        # === DÉTECTION SHORT ===
        short_signal = self._check_short_setup(
            symbol, latest_4h, latest_1h, latest_1d, df_4h, df_1d
        )
        if short_signal:
            signals.append(short_signal)
        
        return signals
    
    def _calculate_market_structure(self, df, lookback=10):
        """
        Détermine la structure de marché: uptrend, downtrend, range
        Basé sur les higher/lower highs et lows
        """
        closes = df['close'].tail(lookback).values
        highs = df['high'].tail(lookback).values
        lows = df['low'].tail(lookback).values
        
        # Trouver les pivots
        higher_highs = 0
        lower_highs = 0
        higher_lows = 0
        lower_lows = 0
        
        for i in range(2, len(highs)):
            # Higher/Lower Highs
            if highs[i] > highs[i-1] and highs[i-1] > highs[i-2]:
                higher_highs += 1
            elif highs[i] < highs[i-1] and highs[i-1] < highs[i-2]:
                lower_highs += 1
            
            # Higher/Lower Lows
            if lows[i] > lows[i-1] and lows[i-1] > lows[i-2]:
                higher_lows += 1
            elif lows[i] < lows[i-1] and lows[i-1] < lows[i-2]:
                lower_lows += 1
        
        # Déterminer la structure
        if higher_highs > lower_highs and higher_lows > lower_lows:
            return "uptrend"
        elif lower_highs > higher_highs and lower_lows > higher_lows:
            return "downtrend"
        else:
            return "range"
    
    def _check_rsi_divergence(self, df, divergence_type='bullish', lookback=20):
        """
        Détecte les divergences RSI
        - Bullish: prix fait lower low, RSI fait higher low
        - Bearish: prix fait higher high, RSI fait lower high
        """
        closes = df['close'].tail(lookback).values
        rsi_values = df['rsi'].tail(lookback).values
        
        if len(closes) < 10:
            return False
        
        if divergence_type == 'bullish':
            # Trouver les 2 derniers creux de prix
            price_lows_idx = []
            for i in range(2, len(closes)-2):
                if closes[i] < closes[i-1] and closes[i] < closes[i-2] and \
                   closes[i] < closes[i+1] and closes[i] < closes[i+2]:
                    price_lows_idx.append(i)
            
            if len(price_lows_idx) >= 2:
                idx1, idx2 = price_lows_idx[-2], price_lows_idx[-1]
                # Prix fait lower low, RSI fait higher low
                if closes[idx2] < closes[idx1] and rsi_values[idx2] > rsi_values[idx1]:
                    return True
        
        elif divergence_type == 'bearish':
            # Trouver les 2 derniers sommets de prix
            price_highs_idx = []
            for i in range(2, len(closes)-2):
                if closes[i] > closes[i-1] and closes[i] > closes[i-2] and \
                   closes[i] > closes[i+1] and closes[i] > closes[i+2]:
                    price_highs_idx.append(i)
            
            if len(price_highs_idx) >= 2:
                idx1, idx2 = price_highs_idx[-2], price_highs_idx[-1]
                # Prix fait higher high, RSI fait lower high
                if closes[idx2] > closes[idx1] and rsi_values[idx2] < rsi_values[idx1]:
                    return True
        
        return False
    
    def _calculate_directional_volume(self, df, lookback=10):
        """
        Calcule le volume directionnel:
        - Bougies vertes (hausse) vs bougies rouges (baisse)
        """
        recent = df.tail(lookback)
        
        volume_up = recent[recent['close'] > recent['open']]['volume'].sum()
        volume_down = recent[recent['close'] < recent['open']]['volume'].sum()
        
        total_volume = volume_up + volume_down
        if total_volume == 0:
            return 0
        
        # Ratio volume haussier / volume total
        return volume_up / total_volume
    
    def _check_rejection_wick(self, candle, direction='bullish'):
        """
        Vérifie si la bougie a un rejection wick significatif
        - Bullish: long wick en bas (rejet de la baisse)
        - Bearish: long wick en haut (rejet de la hausse)
        """
        body_size = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return False
        
        if direction == 'bullish':
            lower_wick = min(candle['open'], candle['close']) - candle['low']
            # Wick > 2x le body ET > 50% du range total
            return lower_wick > 2 * body_size and lower_wick > 0.5 * total_range
        
        elif direction == 'bearish':
            upper_wick = candle['high'] - max(candle['open'], candle['close'])
            return upper_wick > 2 * body_size and upper_wick > 0.5 * total_range
        
        return False
    
    def _check_long_setup(self, symbol, latest_4h, latest_1h, latest_1d, df_4h, df_1d):
        """
        Vérifie si conditions LONG sont remplies
        FILTRES ULTRA-STRICTS pour éviter les falling knives
        """
        score = 0
        reasons = []
        
        # =====================================================
        # 🚨 FILTRE #1: TENDANCE EMA 200 (CRITIQUE)
        # =====================================================
        price = latest_4h['close']
        ema_200 = latest_4h['ema_200']
        
        if price < ema_200:
            # Prix sous EMA 200 = tendance baissière
            # On PÉNALISE fortement, voire on refuse
            pct_below_ema = ((ema_200 - price) / ema_200) * 100
            
            if pct_below_ema > 5:
                # Plus de 5% sous EMA200 = NO GO
                reasons.append(f"❌ REJETÉ: Prix {pct_below_ema:.1f}% sous EMA200 (downtrend fort)")
                return None
            else:
                # Entre 0-5% sous EMA200 = pénalité de score
                score -= 2
                reasons.append(f"⚠️ Prix {pct_below_ema:.1f}% sous EMA200 (risqué)")
        else:
            # Prix au-dessus EMA 200 = bon signe
            score += 3
            reasons.append("✅ Prix > EMA200 (uptrend)")
        
        # =====================================================
        # 🚨 FILTRE #2: STRUCTURE DE MARCHÉ
        # =====================================================
        market_structure = self._calculate_market_structure(df_4h, lookback=10)
        
        if market_structure == "downtrend":
            # Structure baissière = très risqué
            reasons.append("❌ REJETÉ: Structure downtrend (lower lows)")
            return None
        elif market_structure == "uptrend":
            score += 2
            reasons.append("✅ Structure uptrend (higher lows)")
        else:
            # Range = neutre
            score += 1
            reasons.append("⚠️ Structure range (consolidation)")
        
        # =====================================================
        # FILTRE #3: RSI OVERSOLD (mais moins de poids qu'avant)
        # =====================================================
        rsi_4h = latest_4h['rsi']
        if rsi_4h < 25:
            # Très oversold
            score += 2
            reasons.append(f"RSI 4h={rsi_4h:.1f} (très oversold)")
        elif rsi_4h < self.rsi_oversold:
            score += 1
            reasons.append(f"RSI 4h={rsi_4h:.1f} (oversold)")
        else:
            # Pas assez oversold
            return None
        
        # =====================================================
        # FILTRE #4: DIVERGENCE RSI BULLISH
        # =====================================================
        if self._check_rsi_divergence(df_4h, 'bullish'):
            score += 3  # Très bon signe
            reasons.append("✅ Divergence bullish RSI détectée")
        
        # =====================================================
        # FILTRE #5: VOLUME DIRECTIONNEL
        # =====================================================
        vol_ratio = self._calculate_directional_volume(df_4h, lookback=10)
        
        if vol_ratio < 0.3:
            # Volume majoritairement baissier (70%+ de volume rouge)
            # = selling pressure forte
            score -= 2
            reasons.append(f"⚠️ Volume baissier dominant ({(1-vol_ratio)*100:.0f}% red)")
        elif vol_ratio < 0.4:
            # 60-70% volume rouge = neutre/faible
            reasons.append(f"Volume légèrement baissier ({(1-vol_ratio)*100:.0f}% red)")
        else:
            # Volume équilibré ou haussier
            score += 1
            reasons.append(f"Volume équilibré ({vol_ratio*100:.0f}% green)")
        
        # =====================================================
        # FILTRE #6: REJECTION WICK (pattern de chandelier)
        # =====================================================
        if self._check_rejection_wick(latest_4h, 'bullish'):
            score += 2
            reasons.append("✅ Rejection wick bullish (rejet de la baisse)")
        
        # =====================================================
        # FILTRE #7: PRIX PROCHE BOLLINGER LOWER
        # =====================================================
        dist_bb_lower = latest_4h['dist_bb_lower']
        if dist_bb_lower < self.bb_threshold:
            score += 2
            reasons.append(f"Prix à {dist_bb_lower:.1f}% de BB_lower")
        
        # =====================================================
        # FILTRE #8: CONFIRMATION TIMEFRAME SUPÉRIEUR (1D)
        # =====================================================
        if latest_1d is not None and df_1d is not None:
            rsi_1d = latest_1d['rsi']
            ema_200_1d = latest_1d['ema_200']
            price_1d = latest_1d['close']
            
            # RSI 1d aussi oversold
            if rsi_1d < 35:
                score += 2
                reasons.append(f"RSI 1d={rsi_1d:.1f} (oversold)")
            
            # Prix 1d au-dessus EMA200
            if price_1d > ema_200_1d:
                score += 1
                reasons.append("Prix 1d > EMA200 (macro uptrend)")
            else:
                score -= 1
                reasons.append("⚠️ Prix 1d < EMA200 (macro downtrend)")
        
        # =====================================================
        # FILTRE #9: PAS DE CHUTE VIOLENTE EN COURS
        # =====================================================
        if len(df_4h) >= 5:
            last_5_closes = df_4h['close'].tail(5).values
            
            # Calculer la baisse moyenne sur les 5 dernières bougies
            drops = []
            for i in range(1, len(last_5_closes)):
                pct_change = (last_5_closes[i] - last_5_closes[i-1]) / last_5_closes[i-1]
                drops.append(pct_change)
            
            avg_drop = np.mean(drops) * 100
            
            if avg_drop < -2:
                # Chute moyenne > 2% par bougie = falling knife
                reasons.append(f"❌ REJETÉ: Chute violente en cours ({avg_drop:.1f}%/bougie)")
                return None
            elif avg_drop < -1:
                score -= 1
                reasons.append(f"⚠️ Baisse modérée ({avg_drop:.1f}%/bougie)")
        
        # =====================================================
        # SCORE MINIMUM REQUIS: 8 (au lieu de 5)
        # =====================================================
        if score < self.min_score_long:
            reasons.append(f"❌ Score insuffisant: {score}/{self.min_score_long}")
            return None
        
        # =====================================================
        # CALCUL DES PRIX (Entry, Stop, Target)
        # =====================================================
        entry_price = latest_4h['close']
        stop_loss = entry_price * 0.97  # -3%
        bb_middle = latest_4h['bb_middle']
        
        # Target: BB middle ou +6%, le plus proche
        target_bb = bb_middle
        target_pct = entry_price * 1.06
        take_profit = min(target_bb, target_pct)
        
        risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)
        
        # Ne garder que si R/R > 1.5
        if risk_reward < 1.5:
            reasons.append(f"❌ R/R trop faible: {risk_reward:.2f}")
            return None
        
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
            'market_structure': market_structure,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _check_short_setup(self, symbol, latest_4h, latest_1h, latest_1d, df_4h, df_1d):
        """
        Vérifie si conditions SHORT sont remplies
        Filtres stricts symétriques aux LONG
        """
        score = 0
        reasons = []
        
        # =====================================================
        # FILTRE #1: TENDANCE EMA 200
        # =====================================================
        price = latest_4h['close']
        ema_200 = latest_4h['ema_200']
        
        if price > ema_200:
            # Prix au-dessus EMA 200 en uptrend
            pct_above_ema = ((price - ema_200) / ema_200) * 100
            
            if pct_above_ema > 5:
                # Plus de 5% au-dessus = uptrend fort, pas de short
                reasons.append(f"❌ REJETÉ: Prix {pct_above_ema:.1f}% au-dessus EMA200")
                return None
            else:
                score -= 2
                reasons.append(f"⚠️ Prix {pct_above_ema:.1f}% au-dessus EMA200")
        else:
            score += 3
            reasons.append("✅ Prix < EMA200 (downtrend)")
        
        # =====================================================
        # FILTRE #2: STRUCTURE DE MARCHÉ
        # =====================================================
        market_structure = self._calculate_market_structure(df_4h, lookback=10)
        
        if market_structure == "uptrend":
            reasons.append("❌ REJETÉ: Structure uptrend (higher highs)")
            return None
        elif market_structure == "downtrend":
            score += 2
            reasons.append("✅ Structure downtrend (lower highs)")
        else:
            score += 1
            reasons.append("⚠️ Structure range")
        
        # =====================================================
        # FILTRE #3: RSI OVERBOUGHT
        # =====================================================
        rsi_4h = latest_4h['rsi']
        if rsi_4h > 75:
            score += 2
            reasons.append(f"RSI 4h={rsi_4h:.1f} (très overbought)")
        elif rsi_4h > self.rsi_overbought:
            score += 1
            reasons.append(f"RSI 4h={rsi_4h:.1f} (overbought)")
        else:
            return None
        
        # =====================================================
        # FILTRE #4: DIVERGENCE RSI BEARISH
        # =====================================================
        if self._check_rsi_divergence(df_4h, 'bearish'):
            score += 3
            reasons.append("✅ Divergence bearish RSI détectée")
        
        # =====================================================
        # FILTRE #5: VOLUME DIRECTIONNEL
        # =====================================================
        vol_ratio = self._calculate_directional_volume(df_4h, lookback=10)
        
        if vol_ratio > 0.7:
            # Volume très haussier = buying pressure
            score -= 2
            reasons.append(f"⚠️ Volume haussier dominant ({vol_ratio*100:.0f}% green)")
        elif vol_ratio > 0.6:
            reasons.append(f"Volume légèrement haussier ({vol_ratio*100:.0f}% green)")
        else:
            score += 1
            reasons.append(f"Volume équilibré ({(1-vol_ratio)*100:.0f}% red)")
        
        # =====================================================
        # FILTRE #6: REJECTION WICK
        # =====================================================
        if self._check_rejection_wick(latest_4h, 'bearish'):
            score += 2
            reasons.append("✅ Rejection wick bearish (rejet de la hausse)")
        
        # =====================================================
        # FILTRE #7: PRIX PROCHE BOLLINGER UPPER
        # =====================================================
        dist_bb_upper = latest_4h['dist_bb_upper']
        if dist_bb_upper < self.bb_threshold:
            score += 2
            reasons.append(f"Prix à {dist_bb_upper:.1f}% de BB_upper")
        
        # =====================================================
        # FILTRE #8: CONFIRMATION 1D
        # =====================================================
        if latest_1d is not None and df_1d is not None:
            rsi_1d = latest_1d['rsi']
            ema_200_1d = latest_1d['ema_200']
            price_1d = latest_1d['close']
            
            if rsi_1d > 65:
                score += 2
                reasons.append(f"RSI 1d={rsi_1d:.1f} (overbought)")
            
            if price_1d < ema_200_1d:
                score += 1
                reasons.append("Prix 1d < EMA200 (macro downtrend)")
            else:
                score -= 1
                reasons.append("⚠️ Prix 1d > EMA200 (macro uptrend)")
        
        # =====================================================
        # FILTRE #9: PAS DE RALLYE VIOLENT
        # =====================================================
        if len(df_4h) >= 5:
            last_5_closes = df_4h['close'].tail(5).values
            
            gains = []
            for i in range(1, len(last_5_closes)):
                pct_change = (last_5_closes[i] - last_5_closes[i-1]) / last_5_closes[i-1]
                gains.append(pct_change)
            
            avg_gain = np.mean(gains) * 100
            
            if avg_gain > 2:
                reasons.append(f"❌ REJETÉ: Rallye violent ({avg_gain:.1f}%/bougie)")
                return None
            elif avg_gain > 1:
                score -= 1
                reasons.append(f"⚠️ Hausse modérée ({avg_gain:.1f}%/bougie)")
        
        # Score minimum
        if score < self.min_score_short:
            reasons.append(f"❌ Score insuffisant: {score}/{self.min_score_short}")
            return None
        
        # Calcul prix
        entry_price = latest_4h['close']
        stop_loss = entry_price * 1.03  # +3%
        bb_middle = latest_4h['bb_middle']
        
        target_bb = bb_middle
        target_pct = entry_price * 0.94
        take_profit = max(target_bb, target_pct)
        
        risk_reward = (entry_price - take_profit) / (stop_loss - entry_price)
        
        if risk_reward < 1.5:
            reasons.append(f"❌ R/R trop faible: {risk_reward:.2f}")
            return None
        
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
            'market_structure': market_structure,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
