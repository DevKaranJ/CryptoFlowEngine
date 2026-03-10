"""
Test script to verify detector functionality.
Run with: python test_detectors.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orderflow import (
    AbsorptionDetector,
    ImbalanceDetector,
)
from strategy import ZoneDetector, InitiationDetector
from config import get_settings


def test_zone_detector():
    """Test zone detector with sample data."""
    print("\n" + "="*60)
    print("TESTING ZONE DETECTOR")
    print("="*60)
    
    detector = ZoneDetector()
    settings = get_settings()
    
    # Create sample candle data (100 candles)
    import random
    base_price = 70000
    
    candles = []
    for i in range(100):
        # Create some swing highs and lows
        if i % 20 == 0:
            high = base_price + random.uniform(100, 300)
            low = base_price - random.uniform(50, 100)
        elif i % 15 == 0:
            high = base_price + random.uniform(50, 100)
            low = base_price - random.uniform(100, 300)
        else:
            high = base_price + random.uniform(20, 80)
            low = base_price - random.uniform(20, 80)
        
        candles.append({
            "high": high,
            "low": low,
            "close": random.uniform(low, high),
            "volume": random.uniform(10000, 50000),
        })
        base_price += random.uniform(-100, 100)
    
    print(f"Input: {len(candles)} candles")
    print(f"Settings require: {settings.strategy.zone_lookback_candles} candles")
    
    result = detector.detect_zones_from_candles(candles)
    
    print(f"\nResults:")
    print(f"  Support zones: {len(result.get('support_zones', []))}")
    print(f"  Resistance zones: {len(result.get('resistance_zones', []))}")
    print(f"  Value Area POC: {result.get('value_area', {}).get('poc', 0):.2f}")
    print(f"  Swing highs: {len(result.get('swing_highs', []))}")
    print(f"  Swing lows: {len(result.get('swing_lows', []))}")
    
    # Test is_near_zone
    test_price = 70200
    support_zones = result.get("support_zones", [])
    resistance_zones = result.get("resistance_zones", [])
    
    near_support = detector.is_near_zone(test_price, support_zones)
    near_resistance = detector.is_near_zone(test_price, resistance_zones)
    
    print(f"\nNear zone test (price={test_price}):")
    print(f"  Near support: {near_support}")
    print(f"  Near resistance: {near_resistance}")
    
    return result


def test_absorption_detector():
    """Test absorption detector with sample data."""
    print("\n" + "="*60)
    print("TESTING ABSORPTION DETECTOR")
    print("="*60)
    
    detector = AbsorptionDetector()
    
    # Test 1: With proper OHLC data
    print("\nTest 1: Proper OHLC data")
    bar_data = {
        "price": 70000,
        "volume": 50000,
        "delta": -20000,  # Heavy selling
        "open": 70200,
        "close": 70100,  # Price didn't drop much despite heavy selling
        "high": 70300,
        "low": 69900,
    }
    
    result = detector.analyze_bar(bar_data)
    print(f"  Bar data: price={bar_data['price']}, volume={bar_data['volume']}, delta={bar_data['delta']}")
    print(f"  OHLC: O={bar_data['open']}, H={bar_data['high']}, L={bar_data['low']}, C={bar_data['close']}")
    print(f"  Result: detected={result.get('detected')}, type={result.get('type')}")
    
    # Test 2: Current broken approach (all prices same)
    print("\nTest 2: Broken approach (same price for all)")
    broken_bar_data = {
        "price": 70000,
        "volume": 50000,
        "delta": -20000,
    }
    
    result2 = detector.analyze_bar(broken_bar_data)
    print(f"  Bar data: price={broken_bar_data['price']}, volume={broken_bar_data['volume']}, delta={broken_bar_data['delta']}")
    print(f"  Result: detected={result2.get('detected')}, type={result2.get('type')}")
    print(f"  --> This is why it always returns False!")
    
    return result


def test_imbalance_detector():
    """Test imbalance detector with sample data."""
    print("\n" + "="*60)
    print("TESTING IMBALANCE DETECTOR")
    print("="*60)
    
    detector = ImbalanceDetector()
    settings = get_settings()
    
    print(f"Settings threshold: {settings.orderflow.imbalance_threshold}")
    
    # Test 1: Your current data
    print("\nTest 1: Your actual data from logs")
    market_data = {
        "price": 70432.51,
        "volume": 32411.86234,
        "delta": -4.65,  # From logs
    }
    
    result = detector.analyze_market(market_data)
    print(f"  Volume: {market_data['volume']}, Delta: {market_data['delta']}")
    buy_vol = (market_data['volume'] + market_data['delta']) / 2
    sell_vol = (market_data['volume'] - market_data['delta']) / 2
    print(f"  Estimated buy: {buy_vol:.2f}, sell: {sell_vol:.2f}")
    ratio = buy_vol / sell_vol if sell_vol > 0 else 999
    print(f"  Ratio: {ratio:.4f}")
    print(f"  Threshold needed: {settings.orderflow.imbalance_threshold}")
    print(f"  Result: detected={result.get('detected')}, type={result.get('type')}, stacked={result.get('stacked')}")
    
    # Test 2: With extreme imbalance
    print("\nTest 2: Extreme buy imbalance (will trigger)")
    extreme_data = {
        "price": 70000,
        "volume": 100000,
        "delta": 80000,  # 90% buying
    }
    
    result2 = detector.analyze_market(extreme_data)
    buy_vol2 = (extreme_data['volume'] + extreme_data['delta']) / 2
    sell_vol2 = (extreme_data['volume'] - extreme_data['delta']) / 2
    ratio2 = buy_vol2 / sell_vol2 if sell_vol2 > 0 else 999
    print(f"  Volume: {extreme_data['volume']}, Delta: {extreme_data['delta']}")
    print(f"  Ratio: {ratio2:.2f}")
    print(f"  Result: detected={result2.get('detected')}, type={result2.get('type')}")
    
    return result


def test_initiation_detector():
    """Test initiation detector with sample data."""
    print("\n" + "="*60)
    print("TESTING INITIATION DETECTOR")
    print("="*60)
    
    detector = InitiationDetector()
    
    # Create candles showing buy absorption then bullish initiation
    candles = [
        {"open": 70000, "close": 69800, "high": 70100, "low": 69700, "volume": 50000},  # Sell pressure
        {"open": 69800, "close": 70300, "high": 70400, "low": 69750, "volume": 60000},  # Bullish initiation
    ]
    
    result = detector.detect_initiation_from_candles(candles, imbalance_type="sell")
    print(f"  Candle 1 (absorption): O=70000, C=69800 (bearish)")
    print(f"  Candle 2 (initiation): O=69800, C=70300 (bullish)")
    print(f"  Result: detected={result.get('detected')}, direction={result.get('direction')}")
    
    # Test with no imbalance
    print("\nTest 2: No imbalance type")
    result2 = detector.detect_initiation_from_candles(candles, imbalance_type="none")
    print(f"  Result: detected={result2.get('detected')}, direction={result2.get('direction')}")
    
    return result


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# CRYPTO BOT DETECTOR TEST SUITE")
    print("#"*60)
    
    test_zone_detector()
    test_absorption_detector()
    test_imbalance_detector()
    test_initiation_detector()
    
    print("\n" + "#"*60)
    print("# SUMMARY OF ISSUES FOUND")
    print("#"*60)
    print("""
1. ZONE DETECTOR:
   - Needs to call is_near_zone() after detecting zones
   - Fix: Add zone proximity check in main.py

2. ABSORPTION DETECTOR:
   - analyze_bar() uses same price for all OHLC values
   - This makes price_range = 0, detection impossible
   - Fix: Pass proper OHLC data or use kline data

3. IMBALANCE DETECTOR:
   - Threshold is 3.0 (needs 3:1 ratio!)
   - Your data has ratio ~1.02 (1:1)
   - Fix: Lower threshold in settings.yaml to 1.5 or 2.0

4. INITIATION DETECTOR:
   - Needs imbalance detected first
   - Fix: Works once imbalance threshold is fixed
""")


if __name__ == "__main__":
    main()

