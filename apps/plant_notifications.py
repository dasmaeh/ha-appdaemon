import appdaemon.plugins.hass.hassapi as hass
import datetime

class PlantNotifications(hass.Hass):

  def initialize(self):
    # Check plants regularly
    time = datetime.time(0, 0, 0)
    #self.run_minutely(self.check_plants, time) # Every minute, used for development
    self.run_hourly(self.check_plants, time) # Every hour, used for production
    # Check plants when somebody comes home
    self.listen_state(self.check_plants_coming_home, "binary_sensor.presence_jan", new='on')
    self.listen_state(self.check_plants_coming_home, "binary_sensor.presence_cornelia", new='on')
    # Check plants when somebody leaves bed
    self.listen_state(self.check_plants_coming_home, "binary_sensor.bed_jan", new='off')
    self.listen_state(self.check_plants_coming_home, "binary_sensor.bed_cornelia", new='off')

  # Callback function for state triggers
  def check_plants_coming_home(self, entity, attribute, old, new, kwargs):
      self.check_plants()

  # Callback function for scheduler
  # also the function doing the work ...
  def check_plants(self, kwargs):
      # Loop through all plants in the config
      for plant in self.args["plants"]:
          # Get the state of each plant
          plant_state = self.get_state(entity=self.args["plants"][plant]["entity_id"])

          # If the state of a plant is 'problem' (and it is not night)
          if( plant_state == "problem" and self.entities.sensor.time_of_day_prog != 'night'):
              # Get details for the problem:
              if( self.get_state(entity=self.args["plants"][plant]["entity_id"], attribute="problem") == 'moisture low'):
                  problem = ' braucht Wasser.'
              elif( self.get_state(entity=self.args["plants"][plant]["entity_id"], attribute="problem") == 'moisture high'):
                  problem = ' hat zuviel Wasser bekommen.'
              elif( self.get_state(entity=self.args["plants"][plant]["entity_id"], attribute="problem") == 'conductivity low'):
                  problem = ' braucht Dünger.'
              elif( self.get_state(entity=self.args["plants"][plant]["entity_id"], attribute="problem") == 'conductivity high'):
                  problem = ' hat zuviel Dünger bekommen.'
              else:
                  problem = ' hat ein unbekanntes Problem.'
              # log the details:
              self.log(self.args["plants"][plant]["description_jan"]+ problem)
              self.log(self.args["plants"][plant]["description_cornelia"]+ problem)
              # Check who is home to receive a note:
              self.log(self.entities.binary_sensor.presence_jan.state)
              if( self.entities.binary_sensor.presence_jan.state == 'on' and self.entities.binary_sensor.bed_jan.state == 'off' ):
                self.call_service("script/notify_mqtt", target="jan", message=self.args["plants"][plant]["description_jan"]+problem)
            elif( self.entities.binary_sensor.presence_cornelia.state == 'on' and self.entities.binary_sensor.bed_cornelia.state == 'off' ):
                self.call_service("script/notify_mqtt", target="cornelia", message=self.args["plants"][plant]["description_cornelia"]+problem)
