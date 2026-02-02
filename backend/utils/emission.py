from dataclasses import dataclass
from typing import Dict

@dataclass
class EmissionModel:
    """Carbon emission model parameters"""
    #Vehicle carbon emission coefficient (kg CO2/km)
    emission_factors: Dict[str, float] = None
    base_consumption: float = 0.15  #Basic energy consumption (kWh/km or L/km)
    load_factor: float = 0.01       #The influence coefficient of load on energy consumption
    
    def __post_init__(self):
        """Initialize default emission factor"""
        if self.emission_factors is None:
            self.emission_factors = {
                "ev": 0.0,      #EV: 0 emissions (assuming green electricity is used)
                "fuel": 0.25,   #0.25 kg CO2/km
                "hybrid": 0.12  #0.12 kg CO2/km
            }
    
    def calculate_emission(self, vehicle_type: str, distance: float, 
                          load_weight: float = 0.0) -> float:
        """
        Calculate Carbon Emissions
        
        Args:
            vehicle_type
            distance #km
            load_weight #kg
            
        Returns:
            Carbon emissions (kg CO2)
        """
        if vehicle_type not in self.emission_factors:
            raise ValueError(f"Unknown vehicle type: {vehicle_type}")
        
        #Basic emissions
        base_emission = self.emission_factors[vehicle_type] * distance
        
        #Load capacity impact (the heavier the load, the higher the emissions).
        load_impact = self.load_factor * load_weight * distance
        
        return base_emission + load_impact
    
    @staticmethod
    def from_dict(data: dict) -> "EmissionModel":
        """Creating a carbon emission model from a dictionary"""
        return EmissionModel(
            emission_factors=data.get("emission_factors"),
            base_consumption=data.get("base_consumption", 0.15),
            load_factor=data.get("load_factor", 0.01)
        )