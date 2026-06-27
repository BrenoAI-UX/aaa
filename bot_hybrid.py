"""
Hybrid Grid + DCA Bot - Paper Trading
Combina Grid Trading com DCA para otimizar entradas e saídas
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum


class BotMode(Enum):
    """Modo de operação do bot"""
    UPTREND = "uptrend"      # Mais vendas que compras
    DOWNTREND = "downtrend"  # Mais compras que vendas
    RANGING = "ranging"      # Balanceado


@dataclass
class HybridTrade:
    """Representa um trade do bot híbrido"""
    trade_id: int
    timestamp: datetime
    side: str  # 'BUY' ou 'SELL'
    price: float
    quantity: float
    source: str  # 'GRID' ou 'DCA'
    portfolio_value: float
    pnl: float


class HybridGridDCABot:
    """Bot híbrido que combina Grid Trading e DCA"""
    
    def __init__(self,
                 symbol: str,
                 capital: float,
                 grid_levels: int = 8,
                 lower_price: float = 100.0,
                 upper_price: float = 200.0,
                 dca_amount: float = 500.0,
                 dca_interval_days: int = 7):
        """
        Args:
            symbol: Par de negociação
            capital: Capital inicial
            grid_levels: Número de níveis do grid
            lower_price: Preço mínimo
            upper_price: Preço máximo
            dca_amount: Valor de cada compra DCA
            dca_interval_days: Intervalo entre compras DCA (dias)
        """
        self.symbol = symbol
        self.capital = capital
        self.initial_capital = capital
        self.grid_levels = grid_levels
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.dca_amount = dca_amount
        self.dca_interval_days = dca_interval_days
        
        self.portfolio = {"USD": capital, "COIN": 0.0}
        self.trades: List[HybridTrade] = []
        self.trade_counter = 0
        
        # Controle de preços
        self.grid_prices = np.linspace(lower_price, upper_price, grid_levels)
        self.last_dca_time = datetime.now()
        self.price_history: List[float] = []
        self.mode = BotMode.RANGING
        
        # Estatísticas
        self.total_buys = 0
        self.total_sells = 0
        self.grid_buys = 0
        self.grid_sells = 0
        self.dca_buys = 0
        
    def _calculate_mode(self, prices: List[float]) -> BotMode:
        """Calcula o modo baseado no histórico de preços"""
        if len(prices) < 2:
            return BotMode.RANGING
        
        recent_change = (prices[-1] - prices[0]) / prices[0]
        
        if recent_change > 0.05:  # 5% de alta
            return BotMode.UPTREND
        elif recent_change < -0.05:  # 5% de queda
            return BotMode.DOWNTREND
        else:
            return BotMode.RANGING
    
    def _get_grid_quantity(self) -> float:
        """Calcula quantidade por ordem de grid"""
        return self.initial_capital / (self.grid_levels * self.lower_price) * 0.3
    
    def process_price(self, current_price: float, current_time: datetime) -> Dict:
        """
        Processa um novo preço e executa trades apropriados
        """
        self.price_history.append(current_price)
        self.mode = self._calculate_mode(self.price_history[-20:])  # Últimas 20 velas
        
        executed_trades = []
        
        # GRID TRADING LOGIC
        executed_trades.extend(self._execute_grid_orders(current_price, current_time))
        
        # DCA LOGIC
        if self._should_dca(current_time):
            trade = self._execute_dca(current_price, current_time)
            if trade:
                executed_trades.append(trade)
        
        return {
            'trades': executed_trades,
            'mode': self.mode.value,
            'portfolio_value': self.get_portfolio_value(current_price),
            'pnl': self.get_pnl(current_price)
        }
    
    def _execute_grid_orders(self, current_price: float, current_time: datetime) -> List[HybridTrade]:
        """Executa ordens do grid"""
        executed = []
        
        for price_level in self.grid_prices:
            quantity = self._get_grid_quantity()
            
            # BUY abaixo do preço atual
            if price_level < current_price * 0.98:
                if abs(current_price - price_level) / current_price < 0.01:  # Próximo o suficiente
                    if self.portfolio['USD'] >= price_level * quantity:
                        self.trade_counter += 1
                        self.portfolio['USD'] -= price_level * quantity
                        self.portfolio['COIN'] += quantity
                        self.total_buys += 1
                        self.grid_buys += 1
                        
                        trade = HybridTrade(
                            trade_id=self.trade_counter,
                            timestamp=current_time,
                            side='BUY',
                            price=current_price,
                            quantity=quantity,
                            source='GRID',
                            portfolio_value=self.get_portfolio_value(current_price),
                            pnl=self.get_pnl(current_price)['pnl']
                        )
                        self.trades.append(trade)
                        executed.append(trade)
            
            # SELL acima do preço atual
            elif price_level > current_price * 1.02:
                if abs(current_price - price_level) / current_price < 0.01:
                    if self.portfolio['COIN'] >= quantity:
                        self.trade_counter += 1
                        self.portfolio['COIN'] -= quantity
                        self.portfolio['USD'] += current_price * quantity
                        self.total_sells += 1
                        self.grid_sells += 1
                        
                        trade = HybridTrade(
                            trade_id=self.trade_counter,
                            timestamp=current_time,
                            side='SELL',
                            price=current_price,
                            quantity=quantity,
                            source='GRID',
                            portfolio_value=self.get_portfolio_value(current_price),
                            pnl=self.get_pnl(current_price)['pnl']
                        )
                        self.trades.append(trade)
                        executed.append(trade)
        
        return executed
    
    def _should_dca(self, current_time: datetime) -> bool:
        """Verifica se é hora de fazer compra DCA"""
        time_since_last = current_time - self.last_dca_time
        should_buy = time_since_last >= timedelta(days=self.dca_interval_days)
        
        # Em downtrend, aumenta frequência de DCA
        if self.mode == BotMode.DOWNTREND and time_since_last >= timedelta(days=self.dca_interval_days * 0.5):
            should_buy = True
        
        return should_buy
    
    def _execute_dca(self, current_price: float, current_time: datetime) -> HybridTrade:
        """Executa compra DCA"""
        if self.portfolio['USD'] < self.dca_amount:
            return None
        
        quantity = self.dca_amount / current_price
        
        self.trade_counter += 1
        self.portfolio['USD'] -= self.dca_amount
        self.portfolio['COIN'] += quantity
        self.total_buys += 1
        self.dca_buys += 1
        self.last_dca_time = current_time
        
        trade = HybridTrade(
            trade_id=self.trade_counter,
            timestamp=current_time,
            side='BUY',
            price=current_price,
            quantity=quantity,
            source='DCA',
            portfolio_value=self.get_portfolio_value(current_price),
            pnl=self.get_pnl(current_price)['pnl']
        )
        
        self.trades.append(trade)
        return trade
    
    def get_portfolio_value(self, current_price: float) -> float:
        """Calcula valor total do portfólio"""
        return self.portfolio['USD'] + (self.portfolio['COIN'] * current_price)
    
    def get_pnl(self, current_price: float) -> Dict:
        """Calcula PnL"""
        portfolio_value = self.get_portfolio_value(current_price)
        pnl = portfolio_value - self.initial_capital
        pnl_percentage = (pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        return {
            'portfolio_value': portfolio_value,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage
        }
    
    def get_statistics(self, current_price: float) -> Dict:
        """Retorna estatísticas completas"""
        pnl = self.get_pnl(current_price)
        
        average_entry = 0
        if self.portfolio['COIN'] > 0:
            total_spent = self.initial_capital - self.portfolio['USD']
            average_entry = total_spent / self.portfolio['COIN']
        
        return {
            'symbol': self.symbol,
            'mode': self.mode.value,
            'total_trades': len(self.trades),
            'total_buys': self.total_buys,
            'total_sells': self.total_sells,
            'grid_buys': self.grid_buys,
            'grid_sells': self.grid_sells,
            'dca_buys': self.dca_buys,
            'portfolio_value': pnl['portfolio_value'],
            'pnl': pnl['pnl'],
            'pnl_percentage': pnl['pnl_percentage'],
            'current_price': current_price,
            'coin_holdings': self.portfolio['COIN'],
            'usd_balance': self.portfolio['USD'],
            'average_entry_price': average_entry
        }
    
    def get_trades_df(self) -> pd.DataFrame:
        """Retorna histórico de trades como DataFrame"""
        if not self.trades:
            return pd.DataFrame()
        
        data = [
            {
                'trade_id': t.trade_id,
                'timestamp': t.timestamp,
                'side': t.side,
                'source': t.source,
                'price': t.price,
                'quantity': t.quantity,
                'total': t.price * t.quantity,
                'portfolio_value': t.portfolio_value,
                'pnl': t.pnl
            }
            for t in self.trades
        ]
        
        return pd.DataFrame(data)


# Exemplo de uso
if __name__ == "__main__":
    # Cria o bot
    bot = HybridGridDCABot(
        symbol='BTC/USD',
        capital=15000.0,
        grid_levels=8,
        lower_price=95.0,
        upper_price=105.0,
        dca_amount=500.0,
        dca_interval_days=7
    )
    
    print(f"Hybrid Grid+DCA Bot - {bot.symbol}")
    print(f"Capital inicial: ${bot.initial_capital:.2f}")
    print("=" * 70)
    print()
    
    # Simula movimentos de preço
    current_time = datetime(2024, 1, 1)
    prices = [
        100.0, 99.5, 99.0, 98.5, 98.0, 99.0, 100.0,  # Downtrend
        101.0, 102.0, 101.5, 102.5, 103.0,           # Uptrend
        102.5, 101.5, 100.5, 101.0, 102.0            # Volatilidade
    ]
    
    for i, price in enumerate(prices):
        current_time += timedelta(days=1)
        result = bot.process_price(price, current_time)
        
        print(f"Dia {i+1} - Preço: ${price:.2f} | Modo: {result['mode'].upper()}")
        
        if result['trades']:
            for trade in result['trades']:
                print(f"  {trade.side:4} {trade.quantity:.6f} @ ${trade.price:.2f} ({trade.source})")
        
        pnl = result['pnl']
        print(f"  Portfólio: ${pnl['portfolio_value']:.2f} | PnL: ${pnl['pnl']:.2f} ({pnl['pnl_percentage']:.2f}%)")
        print()
    
    # Relatório final
    print("\n=== RELATÓRIO FINAL ===")
    stats = bot.get_statistics(prices[-1])
    
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}" if value > 100 or key != 'coin_holdings' else f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")
    
    print("\nÚltimos 10 trades:")
    df = bot.get_trades_df()
    print(df.tail(10)[['timestamp', 'side', 'source', 'price', 'quantity', 'pnl']].to_string(index=False))
