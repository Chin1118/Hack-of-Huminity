import unittest
from backend.features.carbon.emission import calculate_carbon_emission

class TestEmission(unittest.TestCase):
    def test_fuel_emission_driving(self):
        # 100km, 1 hour, 0 load
        # Fuel: 0.10 L/km * 100km = 10 Liters
        # CO2: 10 * 2.31 = 23.1 kg
        co2 = calculate_carbon_emission('fuel', distance_km=100.0, time_hours=1.0, payload_weight=0.0)
        self.assertAlmostEqual(co2, 23.1, delta=0.01)

    def test_ev_emission_driving(self):
        # 100km, 1 hour, 0 load
        # Energy: 0.20 kWh/km * 100km = 20 kWh
        # CO2: 20 * 0.5 = 10.0 kg
        co2 = calculate_carbon_emission('ev', distance_km=100.0, time_hours=1.0, payload_weight=0.0)
        self.assertAlmostEqual(co2, 10.0, delta=0.01)

    def test_fuel_idling(self):
        # 0km, 1 hour idle
        # Fuel: 1.2 L/hr * 1 = 1.2 L
        # CO2: 1.2 * 2.31 = 2.772 kg
        co2 = calculate_carbon_emission('fuel', distance_km=0.0, time_hours=1.0, is_stopping=True)
        self.assertAlmostEqual(co2, 2.772, delta=0.01)

    def test_heavy_load_increase(self):
        # Load factor test
        base = calculate_carbon_emission('fuel', 100.0, 1.0, payload_weight=0.0)
        heavy = calculate_carbon_emission('fuel', 100.0, 1.0, payload_weight=5000.0) # Double load factor
        # Should be significantly higher (doubled consumption in our simplified formula)
        self.assertGreater(heavy, base)
        self.assertAlmostEqual(heavy, base * 2.0, delta=0.01)

    def test_invalid_vehicle(self):
        co2 = calculate_carbon_emission('bicycle', 100.0, 1.0)
        self.assertEqual(co2, 0.0)

if __name__ == '__main__':
    unittest.main()
