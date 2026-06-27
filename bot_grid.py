"""
Grid Trading Bot - Paper Trading
Simula um bot de grid trading que coloca ordens em múltiplos níveis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class GridOrder:
    """Representa uma ordem no grid"""
    order_id: int
    price: float
    quantity: float
    side: str  # 'BUY' ou 'SELL'
    status: str  # 'PENDING', 'FILLED', 'CANCELLED'
    created_at: datetime
    filled_at: datetime = None
    filled_price: float = None


class GridTradingBot:
    """Bot de Grid Trading em papel"""
    
    def __init__(self, 
                 symbol: str,
                 capital: float,
                 grid_levels: int = 10,
                 lower_price: float = 100.0,
                 upper_price: float = 200.0):
        """
        Args:
            symbol: Par de negociação (ex: 'BTC/USD')
            capital: Capital inicial em USD
            grid_levels: Número de níveis de grid
            lower_price: Preço mínimo do grid
            upper_price: Preço máximo do grid
        """
        self.symbol = symbol
        self.capital = capital
        self.initial_capital = capital
        self.grid_levels = grid_levels
        self.lower_price = lower_price
        self.upper_price = upper_price
        
        self.orders: List[GridOrder] = []
        self.trades_history: List[Dict] = []
        self.portfolio = {"USD": capital, "COIN": 0.0}
        self.order_counter = 0
        
        # Calcula preços do grid
        self.grid_prices = np.linspace(lower_price, upper_price, grid_levels)
        self.quantity_per_order = capital / (grid_levels * lower_price) * 0.5
        
    def create_grid_orders(self, current_price: float) -> List[GridOrder]:
        """
        Cria as ordens iniciais do grid
        Coloca BUY abaixo do preço atual e SELL acima
        """
        now = datetime.now()
        
        for price in self.grid_prices:
            self.order_counter += 1
            
            if price < current_price:
                side = 'BUY'
            elif price > current_price:
                side = 'SELL'
            else:
                continue
                
            order = GridOrder(
                order_id=self.order_counter,
                price=price,
                quantity=self.quantity_per_order,
                side=side,
                status='PENDING',
                created_at=now
            )
            self.orders.append(order)
            
        return self.orders
    
    def process_price(self, current_price: float) -> List[Dict]:
        """
        Processa um novo preço e executa ordens que atingiram o preço
        """
        executed_orders = []
        
        for order in self.orders:
            if order.status == 'PENDING':
                # Verifica se o preço atingiu o nível
                if ((order.side == 'BUY' and current_price <= order.price) or
                    (order.side == 'SELL' and current_price >= order.price)):
                    
                    # Executa a ordem
                    order.status = 'FILLED'
                    order.filled_at = datetime.now()
                    order.filled_price = current_price
                    
                    # Atualiza portfólio
                    if order.side == 'BUY':
                        cost = order.quantity * current_price
                        if self.portfolio['USD'] >= cost:
                            self.portfolio['USD'] -= cost
                            self.portfolio['COIN'] += order.quantity
                            
                            trade = {
                                'timestamp': order.filled_at,
                                'side': 'BUY',
                                'price': current_price,
                                'quantity': order.quantity,
                                'total': cost,
                                'portfolio_coin': self.portfolio['COIN'],
                                'portfolio_usd': self.portfolio['USD']
                            }
                            self.trades_history.append(trade)
                            executed_orders.append(trade)
                            
                            # Cria ordem de venda correspondente
                            self._create_sell_order(order, current_price)
                    
                    else:  # SELL
                        if self.portfolio['COIN'] >= order.quantity:
                            revenue = order.quantity * current_price
                            self.portfolio['COIN'] -= order.quantity
                            self.portfolio['USD'] += revenue
                            
                            trade = {
                                'timestamp': order.filled_at,
                                'side': 'SELL',
                                'price': current_price,
                                'quantity': order.quantity,
                                'total': revenue,
                                'portfolio_coin': self.portfolio['COIN'],
                                'portfolio_usd': self.portfolio['USD']
                            }
                            self.trades_history.append(trade)
                            executed_orders.append(trade)
                            
                            # Cria ordem de compra correspondente
                            self._create_buy_order(order, current_price)
        
        return executed_orders
    
    def _create_buy_order(self, sell_order: GridOrder, current_price: float):
        """Cria uma ordem de compra abaixo da ordem de venda executada"""
        new_price = sell_order.price * 0.98  # 2% abaixo
        
        if new_price >= self.lower_price:
            self.order_counter += 1
            new_order = GridOrder(
                order_id=self.order_counter,
                price=new_price,
                quantity=sell_order.quantity,
                side='BUY',
                status='PENDING',
                created_at=datetime.now()
            )
            self.orders.append(new_order)
    
    def _create_sell_order(self, buy_order: GridOrder, current_price: float):
        """Cria uma ordem de venda acima da ordem de compra executada"""
        new_price = buy_order.price * 1.02  # 2% acima
        
        if new_price <= self.upper_price:
            self.order_counter += 1
            new_order = GridOrder(
                order_id=self.order_counter,
                price=new_price,
                quantity=buy_order.quantity,
                side='SELL',
                status='PENDING',
                created_at=datetime.now()
            )
            self.orders.append(new_order)
    
    def get_portfolio_value(self, current_price: float) -> float:
        """Calcula o valor total do portfólio"""
        return self.portfolio['USD'] + (self.portfolio['COIN'] * current_price)
    
    def get_pnl(self, current_price: float) -> Dict:
        """Calcula o PnL"""
        portfolio_value = self.get_portfolio_value(current_price)
        pnl = portfolio_value - self.initial_capital
        pnl_percentage = (pnl / self.initial_capital) * 100
        
        return {
            'portfolio_value': portfolio_value,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage,
            'capital': self.portfolio['USD'],
            'coin_holdings': self.portfolio['COIN']
        }
    
    def get_pending_orders(self) -> List[Dict]:
        """Retorna as ordens pendentes"""
        pending = [
            {
                'order_id': o.order_id,
                'price': o.price,
                'quantity': o.quantity,
                'side': o.side
            }
            for o in self.orders if o.status == 'PENDING'
        ]
        return pending
    
    def get_trades_df(self) -> pd.DataFrame:
        """Retorna histórico de trades como DataFrame"""
        if not self.trades_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.trades_history)
        df['profit_loss'] = 0.0
        
        # Calcula profit/loss para cada trade
        for i in range(1, len(df)):
            if df.iloc[i]['side'] == 'SELL' and df.iloc[i-1]['side'] == 'BUY':
                buy_price = df.iloc[i-1]['price']
                sell_price = df.iloc[i]['price']
                profit = (sell_price - buy_price) * df.iloc[i]['quantity']
                df.at[i, 'profit_loss'] = profit
        
        return df


# Exemplo de uso
if __name__ == "__main__":
    # Cria o bot
    bot = GridTradingBot(
        symbol='BTC/USD',
        capital=10000.0,
        grid_levels=10,
        lower_price=95.0,
        upper_price=105.0
    )
    
    # Preço inicial
    current_price = 100.0
    
    # Cria o grid inicial
    bot.create_grid_orders(current_price)
    
    print(f"Grid criado com {len(bot.orders)} ordens")
    print(f"Ordens pendentes: {len(bot.get_pending_orders())}")
    print()
    
    # Simula movimentos de preço
    prices = [100.0, 99.5, 99.0, 100.2, 101.0, 100.5, 99.8, 100.3]
    
    for price in prices:
        print(f"Preço: ${price}")
        executed = bot.process_price(price)
        
        if executed:
            print(f"  Trades executados: {len(executed)}")
            for trade in executed:
                print(f"    {trade['side']} {trade['quantity']:.4f} @ ${trade['price']}")
        
        pnl = bot.get_pnl(price)
        print(f"  Portfólio: ${pnl['portfolio_value']:.2f}")
        print(f"  PnL: ${pnl['pnl']:.2f} ({pnl['pnl_percentage']:.2f}%)")
        print()
    
    # Mostra relatório final
    print("\n=== RELATÓRIO FINAL ===")
    print(f"Total de trades: {len(bot.trades_history)}")
    print(f"Capital: ${bot.portfolio['USD']:.2f}")
    print(f"Coin holdings: {bot.portfolio['COIN']:.6f}")
    
    df = bot.get_trades_df()
    if not df.empty:
        print("\nÚltimos 5 trades:")
        print(df.tail(5)[['timestamp', 'side', 'price', 'quantity', 'profit_loss']])
