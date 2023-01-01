from src import *

# PARA FACILIDAD EN LA SIMULACION GENERANDO ZONAS, MANADAS 
# Y UBICANDOLAS SATISFACTORIAMENTE EN ZONAS SEGUN CSP
def main():
    zone1 = Zone(1, Habitat.tropical)
    zone2 = Zone(2, Habitat.tempered)
    zone3 = Zone(3, Habitat.tropical)
    zone4 = Zone(4, Habitat.desertic)
    flock1 = Flock(Specie.horse, 34, 13)
    flock2 = Flock(Specie.tiger, 34, 13)
    flock3 = Flock(Specie.grizzly_bear, 32, 45)
    flock4 = Flock(Specie.horse, 21, 14)
    flock5 = Flock(Specie.horse, 12, 23)
    flock1.asign_zone(zone1)
    flock2.asign_zone(zone1)
    flock3.asign_zone(zone2)
    flock4.asign_zone(zone3)
    flock5.asign_zone(zone3)
    eco=Ecosystem([zone1,zone2,zone3,zone4])
    sim=Simulator(eco,30)
    sim.simulate()

if __name__ == "__main__":
    main()