from dataclasses import dataclass, field
from typing import Dict

@dataclass
class EmissionModel:
    """Carbon emission model parameters"""
    # Per-vehicle energy consumption
    fuel_consumption_l_per_km: float = 0.10     # 10L/100km
    ev_consumption_kwh_per_km: float = 0.20     # 20kWh/100km

    # Emission factors
    fuel_emission_kg_per_l: float = 2.31        # kg CO2 / liter (gasoline)
    grid_emission_kg_per_kwh: float = 0.50      # kg CO2 / kWh (grid avg)

    # Load effect
    payload_scale_kg: float = 5000.0            # larger => weaker load effect

    # Optional direct per-km fallback (if you want to support "hybrid" quickly)
    # If not set, hybrid will raise error by default unless you add it.
    per_km_factors: Dict[str, float] = field(default_factory=dict)
    
    def calculate_emission(self, vehicle_type: str, distance: float, payload_weight: float = 0.0) -> float:
        """
        Calculate Carbon Emissions
        
        Args:
            vehicle_type
            distance #km
            load_weight #kg
            
        Returns:
            Carbon emissions (kg CO2)
        """
        vt = (vehicle_type or "").strip().lower()
        if vt == "":
            raise ValueError("vehicle_type cannot be empty")

        if distance < 0:
            raise ValueError("distance_km must be >= 0")
        if payload_weight < 0:
            raise ValueError("payload_weight_kg must be >= 0")
        if self.payload_scale_kg <= 0:
            raise ValueError("payload_scale_kg must be > 0")

        # load multiplier (safe)
        load_multiplier = 1.0 + (payload_weight / self.payload_scale_kg)

        # energy-based models
        if vt == "fuel":
            fuel_needed_l = distance * self.fuel_consumption_l_per_km * load_multiplier
            return fuel_needed_l * self.fuel_emission_kg_per_l

        if vt == "ev":
            energy_needed_kwh = distance * self.ev_consumption_kwh_per_km * load_multiplier
            return energy_needed_kwh * self.grid_emission_kg_per_kwh

        # optional per-km fallback factors
        if vt in self.per_km_factors:
            base = self.per_km_factors[vt] * distance
            # load impact: keep it proportional to base (simple, bounded)
            return base * load_multiplier

        raise ValueError(f"Unknown vehicle type: {vehicle_type!r}")
    
    @staticmethod
    def from_dict(data: dict) -> "EmissionModel":
        """Creating a carbon emission model from a dictionary"""
        def _f(key: str, default: float) -> float:
            v = data.get(key, default)
            try:
                return float(v)
            except (TypeError, ValueError):
                return float(default)

        per_km = data.get("per_km_factors", {}) or {}
        if not isinstance(per_km, dict):
            per_km = {}

        # Coerce per_km values to float safely
        per_km_clean: Dict[str, float] = {}
        for k, v in per_km.items():
            try:
                per_km_clean[str(k).lower()] = float(v)
            except (TypeError, ValueError):
                continue

        return EmissionModel(
            fuel_consumption_l_per_km=_f("fuel_consumption_l_per_km", 0.10),
            ev_consumption_kwh_per_km=_f("ev_consumption_kwh_per_km", 0.20),
            fuel_emission_kg_per_l=_f("fuel_emission_kg_per_l", 2.31),
            grid_emission_kg_per_kwh=_f("grid_emission_kg_per_kwh", 0.50),
            payload_scale_kg=_f("payload_scale_kg", 5000.0),
            per_km_factors=per_km_clean,
        )