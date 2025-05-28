import traci
import xml.etree.ElementTree as ET
from collections import defaultdict

class SUMO:
    def __init__(self, ampelDict, projectFolder, netFile, sumoCfgFile, simulationTime, showSimulation = False):
        self.ampelDict = ampelDict
        self.projectFolder = projectFolder
        self.netFile = netFile
        self.sumoCfgFile = sumoCfgFile
        self.simulationTime = simulationTime
        self.showSimulation = showSimulation


    def loadTimeParameters(self, netPath):
        """Carga los parámetros de tiempo a los semáforos para ejecutar la simulación con dichos parámetros actualizados"""
        for id, ampelFeatures in self.ampelDict.items():
            ampelID = id
            times = ampelFeatures[0]
            # Cargar el archivo XML
            tree = ET.parse(netPath)
            root = tree.getroot()
            position = 0 # Posición en el arreglo times

            # Modificar la duración de las fases verdes de un semáforo específico:
            for tlLogic in root.findall(".//tlLogic"):
                if tlLogic.attrib["id"] == ampelID:
                    for phase in tlLogic.findall("phase"):
                        if "G" in phase.attrib["state"]:  # Cambiar solo fases con luz verde
                            phase.attrib["duration"] = str(times[position])  # Actualizar duración correspondiente
                            position += 1 # Para actualizar la siguiente posición
                            print(f"Fase {phase.attrib['state']} del semáforo {id} modificada a {phase.attrib['duration']} segundos.")
                            if position >= len(times):
                                break

            # Guardar los cambios en el mismo archivo
            tree.write(netPath)
            #print(f"Archivo actualizado: {netPath}")

    def getVehicleRates(self):
        """Obtiene la tasa de vehículos que pasaron por cada semáforo durante el tiempo de la simulación"""
        for id, apelFeatures in self.ampelDict.items():
            detectorFiles = apelFeatures[1]
            rates = defaultdict(list)
            position = 0 # Contador auxiliar para los prints

            for detector in detectorFiles:
                detectorPath = self.projectFolder + detector
                # Carga el archivo de salida del detector entryExitDetector de cada semáforo:
                tree = ET.parse(detectorPath)
                root = tree.getroot()
                vehicleSum = 0

                # Recorrer los datos y extraer el vehicleSum
                for interval in root.findall("interval"):
                    vehicleSum += int(interval.attrib["vehicleSum"])

                rate = vehicleSum/self.simulationTime # Tasa de vehículos
                rates[id].append(rate)
                print(f"La tasa del semáforo {position} es de: {rate}")
                position += 1

        return rates


    def simulateConditions(self, stepSize=300): #Avanzar intervalos de 10 segundos por bloque
        """Ejecuta la simulación en SUMO en base a los parámetros de tiempo de los semáforos y devuelve la tasa de vehículos de cada semáforo"""
        sumoCfgPath = self.projectFolder + self.sumoCfgFile
        netPath = self.projectFolder + self.netFile # SUMO Net path

        #Iniciar SUMO mediante la dependencia TraCI:
        if self.showSimulation:
            traci.start(["sumo-gui", "-c", sumoCfgPath, "--start", "--quit-on-end"]) #Simulación en GUI
            #Parámetros de vista en GUI de la simulación:
            traci.gui.setOffset("View #0", 1090, 950)  # Centrar la vista en coordenadas específica X, Y
            traci.gui.setZoom("View #0", 1000)  # Ajustar el nivel de zoom
            traci.gui.setSchema("View #0", "real world")  # Configurar esquema de colores
        
        else:
            traci.start(["sumo", "-c", sumoCfgPath, "--start", "--quit-on-end"]) # Simulación sin GUI

        # Cargar condiciones de prueba en el archivo XML de la red:
        self.loadTimeParameters(netPath)

        #Ejecutar simulación:
        try:
            currentTime = 0
            while currentTime < self.simulationTime:
                # Avanzar en bloques
                traci.simulationStep(currentTime + stepSize)
                currentTime = traci.simulation.getTime()
                #print(f"Simulación avanzada a: {currentTime} segundos")
                #print(f"Tiempo actual de la simulación: {currentTime}")

        finally:
                traci.close()
                print("\n **************** Simulación Completada ******************")

        #Obtener los parámetros de salida por cada semáforo: vehículos por intervalo de tiempo.
        vehicleRates = self.getVehicleRates()
        print("\n ************** Tasa de vehículos obtenida ****************")

        return vehicleRates