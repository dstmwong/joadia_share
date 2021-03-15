# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:25:26 2019

@author: wongm
"""

import PySimpleGUI as sg 
from PIL import ImageTk
from tkinter.font import Font
import json

from core.model import LiftEntity, C130, MobileEntity, Population, Side, Supply, Civilian, Phase, Surface, MRH, FishingBoat, P8, MotCoy, OPV, Inf
from core.engine import HumanPlayer
from core.load_replay_moves import LoadedReplay

#==============================================================================

def _distance_squared(point1, point2):
    return pow(point1[0] - point2[0], 2) + pow(point1[1] - point2[1], 2)


#==============================================================================
class MapView(sg.Canvas):
    STEM_LINE_COLOR = "BLACK"
    
    def __init__(self, parent_window):
        super().__init__(key='mapview')
        self.parent = parent_window
        self.game = parent_window.engine.game
        self.listen_events = ["ADD_ENTITY", "REMOVE_ENTITY", "ENTITY_MOVED", "RESUPPLY", "CONSUME", "TERRITORY_REVEAL", "CIVILIANS_HEALED", "CIVILIANS_INJURED", "CIVILIAN_RESCUED", "CIVILIAN_DIED", "END_TURN", "SUPPLIES_CHANGED"]
        for e in self.listen_events:
            self.game.add_listener(self, e)
        self.map_file = './images/joadia_map_1333x1000.png'
        self.map_img = None
        self.entity_images = []
        self.entity2canvas = {}
        self.canvas2entity = {}
        self.boat_markers = {}
        self.selected_entity_marker = None
        self.selected_entity_bb = None
        #self.selected_entity_line = None
        self.entity_stem_lines = {}
        
        # this data is used to keep track of an 
        # item being dragged
        self._drag_data = {"x": 0, "y": 0, "item": None}
        
        self.auto_update = True
        
        self.rescue_deaths_label = None
        self.num_rescues = 0
        self.num_deaths = 0
        
        
    def _update_territory_label(self, territory):
        if territory != None: 
            the_obj = self.TKCanvas.find_withtag(territory.name)

            if territory.blue_revealed:
                text_color = "BLACK"
                if territory.state == Population.HUNGRY:
                    text_color = "ORANGE"
            
                elif territory.state == Population.UNREST:
                    text_color = "RED"
                
                civilians = territory.get_civilians()
                num_healthy = len([c for c in civilians if c.state == Civilian.HEALTHY])
                num_injured = len([c for c in civilians if c.state == Civilian.INJURED])
                
                self.TKCanvas.itemconfigure(the_obj, text=territory.name + 
                " [" + str(territory.num_supplies()) + "S, " + str(num_healthy) + "H, " + 
                   str(num_injured) + "I]"
                      , fill=text_color)
#            else:
#                self.TKCanvas.itemconfigure(the_obj, text=territory.name + 
#                "?", fill=text_color)
            else:
                self.TKCanvas.itemconfigure(the_obj, text=territory.name + " [" + \
                                                                              str(territory.num_supplies()) + "S]", fill="BLACK")
                
                #self.TKCanvas.tag_raise(territory.name)
            
    def _set_territory_label_color(self, territory, color):
        if territory != None: 
            the_obj = self.TKCanvas.find_withtag(territory.name)
            self.TKCanvas.itemconfigure(the_obj, fill=color)
            self.TKCanvas.tag_raise(territory.name)
     
    def _update_rescues_deaths_label(self):
        self.TKCanvas.itemconfigure(self.rescue_deaths_label, text="Rescues:" + str(self.num_rescues) + " Deaths:" + str(self.num_deaths))
        
    def on_event(self, event_name, *args):
        if not self.auto_update:
            return
        
        if event_name == "ADD_ENTITY":
            entity = args[0]
            if isinstance(entity, Civilian):
                self._update_territory_label(entity.territory)
            else:
                self._create_entity(entity)
        elif event_name == "REMOVE_ENTITY":
            entity = args[0]
            if isinstance(entity, Civilian):
                territory = args[1]
                self._update_territory_label(territory)
            else:
                self._delete_entity(entity)
        elif event_name == "ENTITY_MOVED":
            entity = args[0]
            if len(args) == 1:
                self._move_entity(entity)
            elif len(args) == 2:
                loc = args[1]
                self._move_entity(entity, loc)
                   
        elif event_name == "RESUPPLY":
            pass
        elif event_name == "CONSUME":
            pass
        elif event_name == "TERRITORY_REVEAL":
            territory = args[0]
            entity = args[1]
            if entity.side == Side.BLUE:
                self._update_territory_label(territory)        
        elif event_name == "CIVILIANS_HEALED":
            territory = args[0]
            self._update_territory_label(territory)
        elif event_name == "CIVILIANS_INJURED":
            pass
        elif event_name == "CIVILIAN_RESCUED":
            self.num_rescues += 1
            self._update_rescues_deaths_label()
            print("Civilian Rescued! Total Rescues:" + str(self.num_rescues) + ", Total Deaths:" + str(self.num_deaths))
        elif event_name == "CIVILIAN_DIED":
            self.num_deaths += 1
            self._update_rescues_deaths_label()
            print("Civilian Died! Total Rescues:" + str(self.num_rescues) + ", Total Deaths:" + str(self.num_deaths))
        elif event_name == "END_TURN":
            if self.game.turn_num == 10:
                print("")
                print("************************************")
                print("You have reached the end of the game!")
                print("")
                print("State of JOADIA crisis:")
                print(str(self.game.rescues) + " rescues and " + str(self.game.deaths) + " deaths")
                print("Final Score: " + str(self.game.get_score()))
                print("")
                print("Feel free to continue playing in FreePlay mode or start a new game, File > New Game")
                print("************************************")
                print("")
        elif event_name == "SUPPLIES_CHANGED":
            territory = args[0]
            self._update_territory_label(territory)
 
                
    def _create_entity(self, entity):
        #create the canvas entity and the stem line
        if entity.surface != None:
            stem_line = self.TKCanvas.create_line((entity.x, entity.y, entity.surface.x, entity.surface.y), fill="BLACK", width=3.0, dash=(40,40))
            self.entity_stem_lines[entity.name] = stem_line
            
            if _distance_squared((entity.x, entity.y), (entity.surface.x, entity.surface.y)) >= 2500:
                self.TKCanvas.itemconfig(stem_line, state="normal")
            else:
                self.TKCanvas.itemconfig(stem_line, state="hidden")
        else:
            print("entity.surface is None")
          
                            
        img = ImageTk.PhotoImage(file = entity.img_file)
        self.entity_images.append(img)
        canvas_obj = self.TKCanvas.create_image(entity.x, entity.y, image = img, tags= entity.name)
        self.entity2canvas[entity.name] = canvas_obj
        self.canvas2entity[canvas_obj] = entity.name
           
        #add some button events on the canvas entity so we can do mouse interactions
        self.TKCanvas.tag_bind(canvas_obj, "<ButtonPress-1>", self.on_entity_press)
        self.TKCanvas.tag_bind(canvas_obj, "<ButtonRelease-1>", self.on_entity_release)
        self.TKCanvas.tag_bind(canvas_obj, "<B1-Motion>", self.on_entity_motion)
                          
    def _delete_entity(self, entity):
        canvas_obj = self.entity2canvas[entity.name]
        if canvas_obj != None:
            self.TKCanvas.delete(canvas_obj)
            stem_line = self.entity_stem_lines.pop(entity.name, None)
            if stem_line != None:
                self.TKCanvas.delete(stem_line)
                
    def _move_entity(self, entity, loc = None):
        canvas_obj = self.entity2canvas[entity.name]
        if loc == None:
            loc = entity.surface
            
        x, y = loc.get_placement_position()
        if canvas_obj != None:
            #print("moving icon", canvas_obj)
            self.TKCanvas.coords(canvas_obj, (x, y))
            stem_line = self.entity_stem_lines[entity.name]
            if stem_line !=None:
                self.TKCanvas.coords(stem_line, (x, y, x, y))
                
    def reset(self):
        #create the map
        if self.map_img == None:
            self.map_img = ImageTk.PhotoImage(file=self.map_file)
            self.TKCanvas.config(width= self.map_img.width(), height = self.map_img.height())
            self.TKCanvas.bind("<Motion>", self.on_mouse_motion)
                
        self.TKCanvas.delete("all")
        self.entity_images.clear()
        self.entity2canvas.clear()
        self.canvas2entity.clear()
        
        map_obj = self.TKCanvas.create_image(self.map_img.width()*0.5 , self.map_img.height()*0.5, 
                                   image=self.map_img, tags="map")
        self.TKCanvas.tag_bind(map_obj, "<ButtonPress-1>", self.unselect)
        
        #create all the objects in the game
        for tok in self.game.entities.values():
            if not isinstance(tok, Civilian):
                self._create_entity(tok)
                              
        #create all the surface markers in the game
        for territory in self.game.territories.values():
            surfaces = territory.get_all_surfaces()
            for surface in surfaces:
                #create the territory markers
                marker_obj = self.TKCanvas.create_oval(surface.x-10, surface.y-10, surface.x+10, surface.y+10, tags=surface.name, fill="")
                self.canvas2entity[marker_obj] = surface.name
                self.TKCanvas.tag_bind(marker_obj, '<ButtonPress-1>', self.on_territory_marker_clicked)
                
                #create the territory labels
                if surface.mobility_type == Surface.LAND:
                    text_obj = self.TKCanvas.create_text(surface.x, surface.y-20, tags=surface.territory.name, text=surface.territory.name, fill="BLACK", font=Font(family="Helvetica", size=12, weight="bold"), state="disabled")
                    self.canvas2entity[text_obj] = surface.territory.name
         
        self.num_deaths = 0
        self.num_rescues = 0                             
        self.rescue_deaths_label = self.TKCanvas.create_text(self.map_img.width() * 0.5, 20, tags="Num_rescues_deaths", text="Rescues:0 Deaths:0", fill="BLACK", font=Font(family="Helvetica", size=12, weight="bold"), state="disabled")
        
        self.update_territory_labels()
        self.selected_entity_marker = self.TKCanvas.create_text(0,0,text="v", fill="BLUE", font="Ariel 15 bold", tags="entity_marker")
        
        self.selected_entity_bb = self.TKCanvas.create_rectangle((0,0,50,50), outline="RED", tags="entity_bb")
        #self.selected_entity_line = self.TKCanvas.create_line((0,0,50,50), fill="RED", width=3, dash=(40,40))
        
    def update_territory_labels(self):
        for t in self.game.territories.values():
            #the_obj = self.TKCanvas.find_withtag(t.name)
            #if t.blue_revealed:
            self._update_territory_label(t)
            #else:
            #    self.TKCanvas.itemconfigure(the_obj, text=t.name + "?")
        
    def set_visible_territory_markers(self, visible=True):
        #global selected_entity
        #if isinstance(selected_entity, MobileEntity):
        tags = []
        for obj in self.TKCanvas.find_all():
            obj_tag = self.TKCanvas.gettags(obj)
            if len(obj_tag) != 0:
                tags.append(obj_tag[0])
        
        
        territory_markers = [tag for tag in tags if (tag[0] == "L" or tag[0] == "A" or tag[0] == "S")]
        #unhighlight all the previously highlighted markers
        for marker in territory_markers:
            self.TKCanvas.itemconfigure(marker, fill="")

        for marker in self.boat_markers.values():
            self.TKCanvas.delete(marker)
        self.boat_markers.clear()
            
        if isinstance(self.parent.selected_entity, MobileEntity):
            lands, seas, airs = self.parent.selected_entity.get_valid_moves()
            land_names = [land.name for land in lands]
            air_names = [air.name for air in airs]
            sea_names = [sea.name for sea in seas]
            
            visible_markers = [tag for tag in territory_markers if (tag in land_names or tag in air_names or tag in sea_names)]
            
            for marker in territory_markers:
                if marker in visible_markers and visible:
                    self.TKCanvas.itemconfigure(marker, fill="#00ff00")
                #else:
                #    self.TKCanvas.itemconfigure(marker, fill="")

            if isinstance(self.parent.selected_entity, P8):
                if self.parent.selected_entity.movement_points > 0:
                    for board_entity in self.game.entities_on_board:
                        if isinstance(self.game.entities_on_board[board_entity], FishingBoat):
                            boat_on_board = self.game.entities_on_board[board_entity]
                            boat_marker = self.TKCanvas.create_oval(boat_on_board.x-10, boat_on_board.y-10, boat_on_board.x+10, boat_on_board.y+10, tags=boat_on_board.name, fill="#ff4500")
                            self.boat_markers[boat_on_board.name] = boat_marker
                            self.TKCanvas.tag_bind(boat_marker, '<ButtonPress-1>', self.on_boat_reveal_clicked)                                                          
    
    def on_mouse_motion(self, event):
        global mouse_position
        mouse_position = (event.x, event.y)
    
    def on_territory_marker_clicked(self, event):
        surface_id = self.TKCanvas.find_closest(event.x, event.y)
        if surface_id[0] in self.canvas2entity.keys():
            if self.TKCanvas.itemcget(surface_id[0], "fill") == "#00ff00":
                surface_name = self.canvas2entity[surface_id[0]]
                #self.parent.selected_entity.move(self.game.surfaces[surface_name])
                self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "move", surface_name)
                self.TKCanvas.coords(self.parent.selected_entity.name, self.parent.selected_entity.x, self.parent.selected_entity.y)
                self.update_selected_ui_elems()
                
                self.set_visible_territory_markers()
                if isinstance(self.parent.selected_entity, MRH):
                    self.parent.movement_frame.movement_points_info.Update(value="Movement points: " + str(int(self.parent.selected_entity.movement_points)) + "/" + str(self.parent.selected_entity.max_movement_points) + " Fuel: " + str(self.parent.selected_entity.fuel) + "/" + str(MRH.MAX_FUEL))
                else:
                    self.parent.movement_frame.movement_points_info.Update(value="Movement points: " + str(int(self.parent.selected_entity.movement_points)) + "/" + str(self.parent.selected_entity.max_movement_points))
                self.update_territory_labels()
    
    def on_boat_reveal_clicked(self, event):
        boat_id = self.TKCanvas.find_closest(event.x, event.y)
        boat_clicked = None
        for boat in self.boat_markers:
            if self.boat_markers[boat] == boat_id[0]:
                boat_clicked = boat
        if boat_clicked != None:
            boat_entity = self.game.entities_on_board[boat_clicked]
            if isinstance(self.parent.selected_entity, P8):
                self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "identify", boat_entity.name)
                self.parent.movement_frame.movement_points_info.Update(value="Movement points: " + str(int(self.parent.selected_entity.movement_points)) + "/" + str(self.parent.selected_entity.max_movement_points))
        self.set_visible_territory_markers()

     
    def unselect(self, *args):
        self.TKCanvas.itemconfig(self.selected_entity_bb, state="hidden")
        #self.TKCanvas.itemconfig(self.selected_entity_line, state="hidden")
         
    def update_selected_ui_elems(self):
        if not self.parent.selected_entity.name in self.entity2canvas:
            return
        
        dim = 50
        canvas_obj = self.entity2canvas[self.parent.selected_entity.name]
        coords = self.TKCanvas.coords(canvas_obj)
        x = coords[0]
        y = coords[1]
        #self.TKCanvas.coords(self.selected_entity_bb, (self.parent.selected_entity.x - dim*0.5, self.parent.selected_entity.y - dim*0.5, self.parent.selected_entity.x + dim*0.5, self.parent.selected_entity.y + dim*0.5))
        self.TKCanvas.coords(self.selected_entity_bb, (x - dim*0.5, y - dim*0.5, x + dim*0.5, y + dim*0.5))
        
        self.TKCanvas.itemconfig(self.selected_entity_bb, state="normal")
        self.move_to_top(self.selected_entity_bb)
        #self.TKCanvas.itemconfig(self.selected_entity_line, state="normal")
        #self.move_to_top(self.selected_entity_line)
        
        #if the stem line has already been created
        if self.parent.selected_entity.name in self.entity_stem_lines.keys():
            stem_line = self.entity_stem_lines[self.parent.selected_entity.name]
            #self.TKCanvas.coords(stem_line, (self.parent.selected_entity.x, self.parent.selected_entity.y, self.parent.selected_entity.surface.x, self.parent.selected_entity.surface.y))
            stemline_coords = self.TKCanvas.coords(stem_line)
            self.TKCanvas.coords(stem_line, (x, y, stemline_coords[2], stemline_coords[3]))
            
            #if _distance_squared((self.parent.selected_entity.x, self.parent.selected_entity.y), (self.parent.selected_entity.surface.x, self.parent.selected_entity.surface.y)) >= 10000:
            if _distance_squared((x, y), (stemline_coords[2], stemline_coords[3])) >= 10000:
                self.TKCanvas.itemconfig(stem_line, state="normal")
            else:
                self.TKCanvas.itemconfig(stem_line, state="hidden")
        #else create the stem line
        else:
            #stem_line = self.TKCanvas.create_line((self.parent.selected_entity.x, self.parent.selected_entity.y, self.parent.selected_entity.surface.x, self.parent.selected_entity.surface.y), fill="BLACK", width=3.0, dash=(40,40))
            #stem_line = self.TKCanvas.create_line((x, y, self.parent.selected_entity.surface.x, self.parent.selected_entity.surface.y), fill="BLACK", width=3.0, dash=(40,40))
            stem_line = self.TKCanvas.create_line((x, y, x, y), fill="BLACK", width=3.0, dash=(40,40))
            self.entity_stem_lines[self.parent.selected_entity.name] = stem_line
        
        #self.TKCanvas.coords(self.selected_entity_line, (self.parent.selected_entity.x, self.parent.selected_entity.y, self.parent.selected_entity.surface.x, self.parent.selected_entity.surface.y))
        #self.TKCanvas.coords(self.selected_entity_line, (x, y, self.parent.selected_entity.surface.x, self.parent.selected_entity.surface.y))
    
    def on_entity_press(self, event):
        '''Begining drag of an object'''
        # record the item and its location
        item = self.TKCanvas.find_closest(event.x, event.y)[0]
        entity_name = self.TKCanvas.gettags(item)[0]
        
        if entity_name in self.parent.engine.game.entities.keys():
            self.parent.on_select_entity(entity_name)
            #self._drag_data["item"] = item
            self._drag_data["entityname"] = entity_name
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
                           
    def on_entity_release(self, event):
        '''End drag of an object'''
        # reset the drag information
        #self._drag_data["item"] = None
        self._drag_data["entityname"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def on_entity_motion(self, event):
        '''Handle dragging of an object'''
        #if "item" in self._drag_data.keys():
        if "entityname" in self._drag_data.keys():
            if self._drag_data["entityname"] in self.entity2canvas.keys():
                self.TKCanvas.coords(self.entity2canvas[self._drag_data["entityname"]], event.x, event.y)
                self._drag_data["x"] = event.x
                self._drag_data["y"] = event.y            
                self.parent.selected_entity.x = event.x
                self.parent.selected_entity.y = event.y
                self.update_selected_ui_elems()
 
    def move_to_top(self, item):
        self.TKCanvas.tag_raise(item)
        
    def refresh():
        pass
    
        
#------------------------------------------------------------------------------
class LoadEntityFrame(sg.Frame):
    LOAD_MODE = "LOAD_MODE"
    UNLOAD_MODE = "UNLOAD_MODE"
    MOVE_MODE = "MOVE_MODE"
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.info_text = sg.Text("                   ")
        self.cargo_list = sg.Listbox([""], key="cargo_list", enable_events=True)
        self.cargo_list.Size = (20,5)
        self.unload_cargo_btn = sg.Button("Unload", key="unload_cargo")
        self.load_supply_btn = sg.Button("Load supply ", key="load_supply")
        self.load_max_supply_btn = sg.Button("Load max supply ", key="load_max_supply")
        self.load_civ_btn = sg.Button("Load civilian", key="load_civilian")
        self.liftable_unit_list = sg.InputCombo([""], key="liftable_unit_list")
        self.liftable_unit_list.Size = (10, 5)
        
        self.territory_list = sg.InputCombo([t.name for t in self.parent.engine.game.territories.values()], key="territory_list_C130")
        self.territory_list.Size = (10, 10)
        
        self.load_unit_btn = sg.Button("Load unit     ", key="load_unit")
        
        super().__init__(title="", layout = [[self.info_text], 
             [self.cargo_list, sg.Column(layout=[[self.unload_cargo_btn], [self.territory_list]])], 
             [self.load_supply_btn],
             [self.load_max_supply_btn], 
             [self.load_civ_btn], 
             [self.load_unit_btn], 
             [self.liftable_unit_list]]
             )
    
        self.mode = LoadEntityFrame.LOAD_MODE
        self.is_C130 = False

    def reset(self):
        self.cargo_list.Update(values="")
        self.load_supply_btn.Update(visible=True)
        self.load_max_supply_btn.Update(visible=False)
        self.load_civ_btn.Update(visible=True)
        self.load_unit_btn.Update(visible=True)
        self.liftable_unit_list.Update(values="", visible=True)
        
    def set_selected_entity(self, entity):
        if isinstance(entity, LiftEntity):
            self.is_C130 = False
            self.cargo_list.Update(values=[cargo.name for cargo in entity.cargo])
            self.territory_list.Update(visible=False)
            
            #load mode is used during the DAWN phase
            if self.mode == LoadEntityFrame.LOAD_MODE:
                if entity.is_empty():
                    self.load_supply_btn.Update(visible=True)
                    self.load_max_supply_btn.Update(visible=False)
                    self.load_civ_btn.Update(visible=True)
                    self.load_unit_btn.Update(visible=True)
                    self.liftable_unit_list.Update(values=[ent.name for ent in entity.get_liftable_mobile_entities()], visible=True)
                    self.unload_cargo_btn.Update(visible=True)
                    if isinstance(entity, MRH):
                        self.load_supply_btn.Update(visible=False)
                else:
                    if entity.carry_mode == LiftEntity.PAX:
                        self.load_supply_btn.Update(visible=False)
                        self.load_max_supply_btn.Update(visible=False)
                        self.load_civ_btn.Update(visible=True)
                        self.load_unit_btn.Update(visible=True)
                        self.liftable_unit_list.Update(values=[ent.name for ent in entity.get_liftable_mobile_entities()], visible=True)
                    elif entity.carry_mode == LiftEntity.SUPPLY:
                        self.load_supply_btn.Update(visible=True)
                        self.load_max_supply_btn.Update(visible=False)
                        self.load_civ_btn.Update(visible=False)
                        self.load_unit_btn.Update(visible=False)
                        self.liftable_unit_list.Update(values=[ent.name for ent in entity.get_liftable_mobile_entities()], visible=False)
                        
            #unload mode is used during the DUSK phase            
            elif self.mode == LoadEntityFrame.UNLOAD_MODE:
                self.load_supply_btn.Update(visible=False)
                self.load_max_supply_btn.Update(visible=False)
                self.load_civ_btn.Update(visible=False)
                self.load_unit_btn.Update(visible=False)
                self.liftable_unit_list.Update(visible=False)
                self.unload_cargo_btn.Update(visible=True)
                #OPV cannot unload in DUSK phase if they interdicted a boat in the current turn
                if isinstance(entity, OPV):
                    if (entity.interdictedBoat):
                        self.unload_cargo_btn.Update(visible=False)


            elif self.mode == LoadEntityFrame.MOVE_MODE:
                self.cargo_list.Update(visible=True)
                self.unload_cargo_btn.Update(visible=False)
                self.load_supply_btn.Update(visible=False)
                self.load_max_supply_btn.Update(visible=False)
                self.load_civ_btn.Update(visible=False)
                self.liftable_unit_list.Update(visible=False)
                self.territory_list.Update(visible=False)
                self.load_unit_btn.Update(visible=False) 
                    
            self.Update(visible=True)
        
        elif isinstance(entity, C130):
            self.is_C130 = True
            self.cargo_list.Update(values=[cargo.name for cargo in entity.cargo])
            
            
            #load mode is used during the DAWN phase
            if self.mode == LoadEntityFrame.LOAD_MODE:
                self.territory_list.Update(visible = True)
                if entity.cargo == []:
                    self.load_supply_btn.Update(visible=True)
                    self.load_max_supply_btn.Update(visible=True)
                    self.load_civ_btn.Update(visible=True)
                    self.load_unit_btn.Update(visible=True)
                    self.liftable_unit_list.Update(values=[ent.name for ent in entity.get_liftable_mobile_entities()], visible=True)
                else:
                    #if we are carrying a civilian, then we can't carry anything else
                    if isinstance(entity.cargo[0], Civilian):
                        self.load_supply_btn.Update(visible=False)
                        self.load_max_supply_btn.Update(visible=False)
                        self.load_civ_btn.Update(visible=True)
                        self.load_unit_btn.Update(visible=False)
                        self.liftable_unit_list.Update(values=[ent.name for ent in entity.get_liftable_mobile_entities()], visible=False)
                    #if we are carrying supplies, then we can't carry anything else
                    elif isinstance(entity.cargo[0], Supply):
                        self.load_supply_btn.Update(visible=True)
                        self.load_max_supply_btn.Update(visible=True)
                        self.load_civ_btn.Update(visible=False)
                        self.load_unit_btn.Update(visible=False)
                        self.liftable_unit_list.Update(values=[ent.name for ent in entity.get_liftable_mobile_entities()], visible=False)
                    #if we are carrying units, then we can't carry anything else
                    elif isinstance(entity.cargo[0], MobileEntity):
                        self.load_supply_btn.Update(visible=False)
                        self.load_max_supply_btn.Update(visible=False)
                        self.load_civ_btn.Update(visible=False)
                        self.load_unit_btn.Update(visible=True)
                        self.liftable_unit_list.Update(values=[ent.name for ent in entity.get_liftable_mobile_entities()], visible=True)
                    
            #unload mode is used during the DUSK phase            
            elif self.mode == LoadEntityFrame.UNLOAD_MODE:
                self.load_supply_btn.Update(visible=False)
                self.load_max_supply_btn.Update(visible=False)
                self.load_civ_btn.Update(visible=False)
                self.load_unit_btn.Update(visible=False)
                self.liftable_unit_list.Update(visible=False)
                self.territory_list.Update(visible=True)
                self.unload_cargo_btn.Update(visible=True)


            elif self.mode == LoadEntityFrame.MOVE_MODE:
                self.cargo_list.Update(visible=True)
                self.unload_cargo_btn.Update(visible=False)
                self.load_supply_btn.Update(visible=False)
                self.load_max_supply_btn.Update(visible=False)
                self.load_civ_btn.Update(visible=False)
                self.liftable_unit_list.Update(visible=False)
                self.territory_list.Update(visible=False)
                self.load_unit_btn.Update(visible=False)
                    
            self.Update(visible=True)
        else:
            self.is_C130 = False
            self.Update(visible=False)
            
    def set_mode(self, mode):
        """
        Enables/disables functionality depending on which phase we are using it
        for
        """
        if mode == LoadEntityFrame.LOAD_MODE:
            self.info_text.Update(value= "Action: LOAD")
            self.mode = mode
        elif mode == LoadEntityFrame.UNLOAD_MODE:
            self.info_text.Update(value= "Action: UNLOAD")
            self.mode = mode
        elif mode == LoadEntityFrame.MOVE_MODE:
            self.info_text.Update(value= "Action: MOVE")
            self.mode = mode
            
    def cargo_list_select(self, values):
        #MRH can unload Inf units whilst on the move
        if self.parent.engine.game.phase == Phase.DAY:
            if isinstance(self.parent.selected_entity, MRH):
                selected_cargo_name = values['cargo_list']
                if isinstance(self.parent.engine.game.entities[selected_cargo_name[0]], Inf):
                    self.unload_cargo_btn.Update(visible=True)
                    return
            self.unload_cargo_btn.Update(visible=False)

    def on_unload_cargo(self, values):
        """
        unloads the selected cargo in the unit's cargo list
        """
        if self.is_C130:
            #if the unload button is clicked on the dusk phase then we are 
            #really performing the action
            if self.parent.engine.game.phase == Phase.DUSK:
                if self.parent.selected_entity.cargo != []:
                    #if cargo is full of civilians
                    if isinstance(self.parent.selected_entity.cargo[0], Civilian):
                        #self.parent.selected_entity.evacuate_civilians()
                        self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "evacuate")
                    elif isinstance(self.parent.selected_entity.cargo[0], MobileEntity):
                        #self.parent.selected_entity.airlift_entities()
                        self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "lift units")
                    elif isinstance(self.parent.selected_entity.cargo[0], Supply):
                        territory = values["territory_list_C130"]
                        if territory != '':
                            target_territory = self.parent.engine.game.territories[territory]
                            if target_territory != None:
                                #self.parent.selected_entity.airdrop_supplies(target_territory, 1)
                                self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "airdrop supplies", target_territory.name)
                        else:
                            print("Please select a Territory from the unload dropdown menu")

            #if the unload button is clicked on the dawn phase, then we are really
            #just undoing the previous action 
            elif self.parent.engine.game.phase == Phase.DAWN:
                selected_cargoes = values["cargo_list"]
                if len(selected_cargoes) != 0:    
                    for selected_cargo_name in selected_cargoes:
                        for cargo in self.parent.selected_entity.cargo:
                            if cargo.name is selected_cargo_name:
                                selected_cargo = cargo
                                self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "unload cargo", selected_cargo.name)
                                # if isinstance(selected_cargo, Civilian):
                                #     self.parent.selected_entity.territory.add_civilian(selected_cargo)
                                # elif isinstance(selected_cargo, Supply):
                                #     self.parent.selected_entity.territory.add_supplies(selected_cargo)
                                # elif isinstance(selected_cargo, MobileEntity):
                                #     selected_cargo.place(self.parent.selected_entity.surface)
                                # self.parent.selected_entity.cargo.remove(selected_cargo)
                                break
                else:
                    print("Please select a cargo from the load cargo list")
                
            self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
            self.liftable_unit_list.Update(values = [entity.name for entity in self.parent.selected_entity.get_liftable_mobile_entities()])
            
            if self.parent.engine.game.phase == Phase.DAWN:
                if self.parent.selected_entity.cargo == []:
                    self.load_supply_btn.Update(visible=True)
                    self.load_civ_btn.Update(visible=True)
                    self.load_unit_btn.Update(visible=True)
                    self.liftable_unit_list.Update(visible=True)
                    
                            
        else:
            selected_cargoes = values["cargo_list"]
            for selected_cargo_name in selected_cargoes:
                
                for cargo in self.parent.selected_entity.cargo:
                    if cargo.name is selected_cargo_name:
                        selected_cargo = cargo
                        break
                
                if isinstance(selected_cargo, Supply):
                    #self.parent.selected_entity.drop_supply(1)
                    self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "drop supplies", 1)
                elif isinstance(selected_cargo, Civilian) or isinstance(selected_cargo, MobileEntity):
                    #self.parent.selected_entity.drop_pax(selected_cargo)
                    self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "drop PAX", selected_cargo.name)
                    
                selected_cargo = None
                        
                self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                self.liftable_unit_list.Update(values = [entity.name for entity in self.parent.selected_entity.get_liftable_mobile_entities()])
                
                if self.parent.engine.game.phase == Phase.DAWN:
                    if self.parent.selected_entity.is_empty():
                        self.load_supply_btn.Update(visible=True)
                        self.load_civ_btn.Update(visible=True)
                        self.load_unit_btn.Update(visible=True)
                        self.liftable_unit_list.Update(visible=True)
            
    def on_load_supply(self):
        """
        loads one supply into the LiftEntity's cargo bays
        """
        if self.is_C130:
            #if self.parent.selected_entity.load_supplies():
            if self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "load supplies", 1):
                #if successful with load, then update the UI
                self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                self.load_civ_btn.Update(visible=False)
                self.load_unit_btn.Update(visible=False)
                self.liftable_unit_list.Update(visible=False)
        else:
            if self.parent.selected_entity.is_empty() or (self.parent.selected_entity.carry_mode == LiftEntity.SUPPLY and not self.parent.selected_entity.is_full()):
                num_supplies = self.parent.selected_entity.surface.territory.num_supplies()
                if num_supplies != 0:
                    #if self.parent.selected_entity.lift_supply(1):
                    if self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "lift supply", 1):
                        self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                        
                        #hide the load refugees and load unit buttons because we can't load
                        #both supplies and passengers
                        self.load_civ_btn.Update(visible=False)
                        self.load_unit_btn.Update(visible=False)
                        self.liftable_unit_list.Update(visible=False)
                    else:
                        print(self.parent.selected_entity.name, "cannot lift supply.")
                else:
                    print("No supplies in", self.parent.selected_entity.territory.name, "to load by", self.parent.selected_entity.name)
                        
    def on_load_max_supply(self):
        if self.is_C130:
            #if self.parent.selected_entity.load_supplies():
            if self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "load max supplies"):
                #if successful with load, then update the UI
                self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                self.load_civ_btn.Update(visible=False)
                self.load_unit_btn.Update(visible=False)
                self.liftable_unit_list.Update(visible=False)
    
    def on_load_civilian(self):
        """
        loads one civilian into the LiftEntity's cargo bays
        """
        if self.is_C130:
            #if self.parent.selected_entity.load_civilians():
            if self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "load civ"):
                #if successful with load, then update the UI
                self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                self.load_supply_btn.Update(visible=False)
                self.load_unit_btn.Update(visible=False)
                self.liftable_unit_list.Update(visible=False)
        else:
            if self.parent.selected_entity.is_empty() or (self.parent.selected_entity.carry_mode == LiftEntity.PAX and not self.parent.selected_entity.is_full()):
                liftable_civilians = self.parent.selected_entity.get_liftable_civilians()
                if len(liftable_civilians) != 0:
                    civilian = liftable_civilians[0]
                    #if self.parent.selected_entity.lift_pax(civilian):
                    if self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "lift PAX", civilian.name):
                        self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                        #hide the load supply button because we can't load both supplies and 
                        #passengers
                        self.load_supply_btn.Update(visible=False)
                    else:
                        print(self.parent.selected_entity.name, "cannot lift civilian", civilian.name)
                else:
                    print("No civilians in", self.parent.selected_entity.territory.name, "to load by", self.parent.selected_entity.name)
                
    def on_load_unit(self, values):
        """
        loads the unit chosen from the combobox into the LiftEntity's cargo bays
        """
        if self.is_C130:
            unit_name = values["liftable_unit_list"]
            for entity in self.parent.selected_entity.get_liftable_mobile_entities():
                if entity.name == unit_name:
                    #if self.parent.selected_entity.load_entity(entity):
                    if self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "load units", entity.name):
                        #if successful with load, then update the UI
                        self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                        self.liftable_unit_list.Update(values = [entity.name for entity in self.parent.selected_entity.get_liftable_mobile_entities()])
                        self.load_supply_btn.Update(visible=False)
                        self.load_civ_btn.Update(visible=False)
        else:
            if self.parent.selected_entity.is_empty() or (self.parent.selected_entity.carry_mode == LiftEntity.PAX and not self.parent.selected_entity.is_full()):
                unit_name = values["liftable_unit_list"]
                for entity in self.parent.selected_entity.get_liftable_mobile_entities():
                    if entity.name == unit_name:
                        #if self.parent.selected_entity.lift_pax(entity):
                        if self.parent.engine.blue_player.execute_move(self.parent.selected_entity.name, "lift PAX", entity.name):
                            self.cargo_list.Update(values = [cargo.name for cargo in self.parent.selected_entity.cargo])
                            self.liftable_unit_list.Update(values = [entity.name for entity in self.parent.selected_entity.get_liftable_mobile_entities()])
                            #hide the load supply button because we can't load both supplies and 
                            #passengers
                            self.load_supply_btn.Update(visible=False)
                        else:
                             print(self.parent.selected_entity.name, "cannot lift", entity.name)
                    

#------------------------------------------------------------------------------
class MovementFrame(sg.Frame):
    def __init__(self):
        self.movement_points_info = sg.Text("Movement points:                    ")
        self.move_isr_btn = sg.Button("Perform ISR", key="moving_isr", visible=False)
        super().__init__(title ="Action: Move", layout=[[self.movement_points_info, self.move_isr_btn]])
    
    def isr_on_move(self):
        if self.ParentForm.selected_entity.territory.blue_revealed == False:
            self.ParentForm.engine.blue_player.execute_move(self.ParentForm.selected_entity.name, "do isr")
            self.ParentForm.map_view.set_visible_territory_markers()
            self.movement_points_info.Update(value="Movement points: " + str(int(self.ParentForm.selected_entity.movement_points)) + "/" + str(self.ParentForm.selected_entity.max_movement_points))
        else:
            print(self.ParentForm.selected_entity.territory.name + " is already revealed")

#------------------------------------------------------------------------------    
class Replay():
    def __init__(self, parent_app):
        self.parent = parent_app
        self.map = self.parent.map_view
        self.engine = self.parent.engine
        self.moves = []
        
        self.last_loaded_units = {}
        
        
    def load_moves(self, all_moves):
        self.moves = list(all_moves)
        
        
    def step(self):
        if self.moves == []:
            return
           
        move = self.moves.pop(0)
        #print(self.moves)
        entity_name = move[0]
        move_label = move[1]
        
        if len(move) > 2:
            args = move[2]

        if move_label == "move":
            entity = self.engine.game.entities[entity_name]
            self.map.on_event("ENTITY_MOVED", entity, self.engine.game.get_surface(move[2]))
            print(entity_name, "moved to", move[2])
        
        elif move_label == "lift PAX":
            entity = self.engine.game.entities[entity_name]
            lifted_entity = self.engine.game.entities[move[2]]
            self.map.on_event("REMOVE_ENTITY", lifted_entity, entity.territory)
            
            if entity.territory != None:
                print(entity_name, "lifted", move[2], "from territory", entity.territory.name)
            else:
                print(entity_name, "lifted", move[2])
            
        elif move_label == "lift supply":
            entity = self.engine.game.entities[entity_name]
            self.map.update_territory_labels()
            self.map._update_territory_label(entity.territory)
            print(entity_name, "lifted", move[2],  "supplies")
            
        elif move_label == "load max supplies":
            entity = self.engine.game.entities[entity_name]
            self.map.update_territory_labels()
            self.map._update_territory_label(entity.territory)
            print(entity_name, "lifted max supplies")
          
        elif move_label == "load civ":
            entity = self.engine.game.entities[entity_name]
            self.map._update_territory_label(entity.territory)
            print(entity_name, "loaded civilians from territory", entity.territory.name)
            
        elif move_label == "load supplies":
            entity = self.engine.game.entities[entity_name]
            self.map._update_territory_label(entity.territory)
            print(entity_name, "loaded supplies from territory", entity.territory.name)
            
        elif move_label == "load units":
            entity = self.engine.game.entities[entity_name]
            lifted_entity = self.engine.game.entities[move[2]]
            self.map.on_event("REMOVE_ENTITY", lifted_entity)
            print(entity_name, "loaded unit", move[2], "from territory", entity.territory.name)
            if entity_name in self.last_loaded_units.keys():
                last_load = self.last_loaded_units[entity_name]
                self.last_loaded_units[entity_name] = last_load.append(move[2])
            else:
                self.last_loaded_units[entity_name] = [move[2]]
 
        elif move_label == "evacuate":
            print(entity_name, "evacuated civilians")
                        
        elif move_label == "airdrop supplies":
            to_territory = self.engine.game.territories[move[2]]
            self.map._update_territory_label(to_territory)
            print(entity_name, "airdropped supplies to", to_territory.name)                   

        elif move_label == "do isr":
            print(entity_name, "performs isr on", move[2])

        elif move_label == "drop supplies":
            entity = self.engine.game.entities[entity_name]
            supplies=int(move[2])
            self.map._update_territory_label(entity.territory)
            print(entity_name, "dropped", supplies, "supplies")
          
        elif move_label == "lift units":
            print(entity_name, "airlifted entities")
            C130_load = self.last_loaded_units[entity_name]
            
            for unit in C130_load:
                entity = self.engine.game.entities[unit]
                self.map.on_event("ADD_ENTITY", entity)
                print(entity.name, "airlifted")
                
            self.last_loaded_units.pop(entity_name, None)
          
        elif move_label == "identify":
            entity = self.engine.game.entities[entity_name]
            self.map.on_event("ENTITY_MOVED", entity, entity.surface)
            boat=self.engine.game.entities[move[2]]
            print(entity_name, "identified", boat.name)                             
          
        elif move_label == "interdict":
            print(entity_name, "interdicted")

        elif move_label == "drop PAX":
            entity = self.engine.game.entities[entity_name]
            dropped_entity = self.engine.game.entities[move[2]]
            self.map.on_event("ADD_ENTITY", dropped_entity)
            print(entity_name, "dropped", move[2], "in territory", entity.territory.name)
        
        elif move_label == "launch boat":
            entity = self.engine.game.entities[entity_name]
            self.map.on_event("ADD_ENTITY", entity)
            print(entity_name, "launched in territory", entity.territory.name)
            
        elif move_label == "deploy militia":
            entity = self.engine.game.entities[entity_name]
            self.map.on_event("ADD_ENTITY", entity.militia)
            print("Militia", entity.militia.name, "deployed in territory", entity.militia.territory.name)
            
        elif move_label == "injure population":
            entity = self.engine.game.entities[entity_name]
            print("Militia", entity.name, "injured ", args, "population in territory", entity.territory.name)
            
        elif move_label == "cause unrest":
            entity = self.engine.game.entities[entity_name]
            self.map._set_territory_label_color(entity.territory, "RED")
            print("Militia", entity.name, "caused unrest in territory", entity.territory.name)
            
        elif move_label == "sabotage supply":
            entity = self.engine.game.entities[entity_name]
            print("Militia", entity.name, "sabotaged supplies in territory", entity.territory.name)
        
        elif move_label == "TERRITORY_REVEAL":
            entity = self.engine.game.entities[entity_name]
            territory = self.engine.game.territories[move[2]]
            self.map.on_event(move_label, territory, entity)
            print(entity_name, "revealed territory", move[2])
            
        elif move_label == "CIVILIAN_RESCUED":                    
            print(entity_name, "rescued!")
            entity = self.engine.game.entities[entity_name]
            self.map.on_event(move_label, entity)
        
        elif move_label == "CIVILIAN_DIED":
            print(entity_name, "died!")
            entity = self.engine.game.entities[entity_name]
            self.map.on_event(move_label, entity)
            
        else:
            print("Replay:unknown move", move)
           
        self.parent.on_select_entity(entity_name)
#==============================================================================


class JoadiaWindowApp(sg.Window):
    def __init__(self, engine):
        self.engine = engine
        #Control Panel components
        self.turn_label = sg.Text("Turn: " + str(engine.game.turn_num) + "   ")
        self.selected_entity_input = sg.InputCombo(["XXXXXXXXXXXXXX"], key="selected_entity_input", enable_events=True)
        self.phase_label = sg.Text("Phase: " + engine.game.phase)
        self.player_info_label = sg.Text("Player                                   ")
        self.territory_label = sg.Text("Territory:                     ")
        self.load_entity_frame = LoadEntityFrame(self)
        self.movement_frame = MovementFrame()
        self.movement_frame.Size = (200, 20)
        self.message_log = sg.Output()
        self.message_log.Size = (39, 18)
        self.menu_def = [['File', ['New Game', 'Save Replay', 'Load Replay']]]
        #self.load_entity_frame.Update(visible=False)
        #self.movement_frame.Update(visible=False)
        self.end_phase_btn = sg.Button("Next Phase", key="end_phase")
        self.next_unit_btn = sg.Button("Next Unit", key="next_unit")
        self.next_btn = sg.Button("Next move", key="next_move")
        self.restart_game_btn = sg.Button("Restart game", key="restart_game")
        
        self.map_view = MapView(self)
        self.replay = Replay(self)
        self.loaded_replay_moves = None

        self.selected_entity = None
        self.selected_entity_index = 0
        
        super().__init__("JOADIA", resizable=True, size=(1920, 1080))
        self.layout = [ [sg.Menu(self.menu_def, )],     
                         [self.map_view, sg.Frame("", layout = [[sg.Column([[self.turn_label], 
                         [self.phase_label],
                         [self.player_info_label],
                         [self.selected_entity_input],
                         [self.territory_label],
                         [self.movement_frame], 
                         [self.load_entity_frame],
                         [sg.Frame("Message Log", layout = [[self.message_log]])],
                         [self.next_unit_btn, self.end_phase_btn, self.next_btn]])]])]
                    ] 

        self.Layout(self.layout)
        self.Finalize()
        self.TKroot.bind("<space>", self.on_space)
        #self.TKroot.bind("<Button-1>", on_mouse_down)
        
        self.reset()
        
    
    def save_replay_file(self):
        filePath = sg.popup_get_file('Please enter a file name', save_as=True, file_types=(('JSON', '*.json'),), keep_on_top=True, no_window=True)
        if self.engine.save_state_to_file(filePath):
            print("Saved as " + filePath)


    def load_replay_file(self, uploadFile = None):
        if uploadFile == None:
            uploadFile = sg.popup_get_file('Please enter a file name', file_types=(('JSON', '*.json'),), keep_on_top=True, no_window=True)
        replay = self.engine.load_state_from_file(uploadFile)
        if replay == None:
            print("Error loading: " + uploadFile)
        else:
            self.reset(True)
            self.loaded_replay_moves = LoadedReplay(self, replay)
            print(uploadFile + " loaded.")
        

    def on_select_entity(self, entity_name):
        #if entity name is None then we unselect
        if entity_name == None:
            self.map_view.unselect()
            return
        
        if entity_name in self.engine.game.entities_on_board.keys():
            entity = self.engine.game.entities_on_board[entity_name]
            self.selected_entity = entity

            if (entity.player == self.engine.current_player) & (self.engine.game.phase != Phase.NIGHT):
                self.selected_entity_input.Update(visible=True)
                self.load_entity_frame.Update(visible=True)
                self.movement_frame.Update(visible=False)
                self.territory_label.Update(visible=True)
                
                self.selected_entity_input.Update(value=entity.name)
                self.map_view.move_to_top(entity.name)
                self.map_view.update_selected_ui_elems()
                self.map_view.move_to_top(entity.territory.name)
                
                territory_info_txt = entity.territory.name
                self.territory_label.Update(value="Territory: " + territory_info_txt)
                
                if self.engine.game.phase == Phase.DAWN:
                    self.load_entity_frame.set_selected_entity(entity)
                elif self.engine.game.phase == Phase.DAY:
                    self.load_entity_frame.set_selected_entity(entity)    
                    if isinstance(self.selected_entity, MobileEntity):
                        self.movement_frame.Update(visible=True)
                        if isinstance(self.selected_entity, MotCoy):
                            self.movement_frame.move_isr_btn.Update(visible=True)
                        else:
                            self.movement_frame.move_isr_btn.Update(visible=False)
                        if isinstance(self.selected_entity, MRH):
                            self.movement_frame.movement_points_info.Update(value="Movement points: " + str(int(self.selected_entity.movement_points)) + "/" + str(self.selected_entity.max_movement_points) + " Fuel: " + str(self.selected_entity.fuel) + "/" + str(MRH.MAX_FUEL))
                        else:
                            self.movement_frame.movement_points_info.Update(value="Movement points: " + str(int(self.selected_entity.movement_points)) + "/" + str(self.selected_entity.max_movement_points))
                    else:
                        self.movement_frame.Update(visible=False)
                    self.map_view.set_visible_territory_markers(True)
                elif self.engine.game.phase == Phase.DUSK:
                    self.load_entity_frame.set_selected_entity(entity)
                    
                self.previous_position = (self.selected_entity.x, self.selected_entity.y)

            return

        self.selected_entity_input.Update(visible=False)
        self.load_entity_frame.Update(visible=False)
        self.movement_frame.Update(visible=False)
        self.territory_label.Update(visible=False)
    
    
    def on_do_replay_phase(self):
        """
        Handler for the next phase button when the UI is on replay mode
        """
        if self.loaded_replay_moves != None:
            self.loaded_replay_moves.step_phase()
            self._update_panel_UI()
            
        
    def on_do_replay_move(self):
        """
        Handler for the next move button when the UI is on replay mode
        """
        if self.loaded_replay_moves != None:
            if self.loaded_replay_moves.current_move == 0:
                self._update_panel_UI()
            self.loaded_replay_moves.step_move()
        

    def on_do_phase(self):
        #check if we need to force which FOB the MRH must return to
        if self.engine.game.phase == Phase.DAY:
            heli = None
            for e in self.engine.blue_player.entities:
                if isinstance(e, MRH):
                    heli = e
            if heli != None:
                if (heli.fuel == 1) & (heli.territory.pods == []):
                    print(heli.name + " was not instructed to return to a FOB and will automatically return to its originating FOB")
                    self.engine.blue_player.execute_move(heli.name, 'move', heli.previousFOB.airs[0].name)

        #human player sets the phase_done flag true because by clicking on the
        #next phase button, it is confirmation that the phase is done
        if isinstance(self.engine.current_player, HumanPlayer):    
            self.engine.current_player.phase_done = True
            
        else:
            #else turn off the auto update to the map view so we get a chance
            #to play them back to the user
            self.map_view.auto_update = False
         
        #prevents a player from doing actions in a phase more than once
        if self.engine.current_player.phase_done == False:
            self.engine.do_phase()
            phase = self.engine.game.phase
            turn_num = self.engine.game.turn_num
            
            #loads all the moves into the recorded moves
            if self.engine.current_player.recorded_moves != []:
                turn_moves = self.engine.current_player.recorded_moves[turn_num - 1]
                if phase == Phase.DAWN:
                    phase_moves = turn_moves[0]
                elif phase == Phase.DAY:
                    phase_moves = turn_moves[1]
                elif phase == Phase.DUSK:
                    phase_moves = turn_moves[2]
                elif phase == Phase.NIGHT:
                    phase_moves = turn_moves[3]
                
                self.replay.load_moves(phase_moves)
                 
        #if the current player is not the Human Player, then we give the human
        #player the option to step through the moves, before going to the next phase
        if isinstance(self.engine.current_player, HumanPlayer):
            self._proceed_to_next_phase()    
        else:
            if self.replay.moves == []:
                self._proceed_to_next_phase()
            else:
                print(len(self.replay.moves), "moves in this phase by " + self.engine.current_player.name)
                print("Press 'Next move' to step through moves")
                print("---")
            
        
    def _proceed_to_next_phase(self):
        self.engine.next_phase()
        self._update_panel_UI()
        
            
    def _update_panel_UI(self):
        #update the UI elements
        #----------
        self.selected_entity = None
        self.load_entity_frame.set_selected_entity(None)
        self.map_view.unselect(None)
        self.goto_phase(self.engine.game.phase)
        self.turn_label.Update(value= "Turn: " + str(self.engine.game.turn_num))
        self.phase_label.Update(value= "Phase: " + self.engine.game.phase)
        self.player_info_label.Update(value = "Player: " + self.engine.current_player.name + " (" + self.engine.current_player.side + ")")
        print("---Turn: " + str(self.engine.game.turn_num) + ", Phase: "+ self.engine.game.phase + "---")
        #repopulate the input list only if we have changed between red and blue players
        if self.engine.game.phase == Phase.DAWN or self.engine.game.phase == Phase.NIGHT:
            entitylist = [tok.name for tok in self.engine.game.entities.values() if tok.player == self.engine.current_player]
            if entitylist != []:
                self.selected_entity_input.Update(values=entitylist)
        #----------        
                
        
        #check the number of deaths to see if we need to update the deaths label
        if self.map_view.num_deaths != self.engine.game.deaths:
            num_died = self.engine.game.deaths - self.map_view.num_deaths
            print(num_died, "civilians have died during turn", self.engine.game.turn_num - 1)
            self.map_view.num_deaths = self.engine.game.deaths
            self.map_view._update_rescues_deaths_label()
       
        self.map_view.update_territory_labels()
        
        #if self.selected_entity_input.Size != 0:
        #    self.on_select_entity(self.selected_entity_input.Values[self.selected_entity_input.TKCombo.current()])
    
    
    def goto_phase(self, phase):
        if phase == Phase.DAWN:
            self.load_entity_frame.set_mode(LoadEntityFrame.LOAD_MODE)
            self.load_entity_frame.Title = "Action: Load"
            self.map_view.set_visible_territory_markers(False)
            self.load_entity_frame.Update(visible=False)
            self.movement_frame.Update(visible=False)
            
            if isinstance(self.engine.current_player, HumanPlayer):
                self.selected_entity_input.Update(visible=True)
                #self.load_entity_frame.Update(visible=True)
                self.territory_label.Update(visible=True)
                
        elif phase == Phase.DAY:
            self.load_entity_frame.set_mode(LoadEntityFrame.MOVE_MODE)
            self.load_entity_frame.Update(visible=False)
            self.movement_frame.Update(visible=False)
            self.map_view.set_visible_territory_markers(False)
            
        elif phase == Phase.DUSK:
            self.load_entity_frame.set_mode(LoadEntityFrame.UNLOAD_MODE)
            self.load_entity_frame.Title = "Action: Unload"
            self.load_entity_frame.Update(visible=False)
            self.movement_frame.Update(visible=False)
            self.map_view.set_visible_territory_markers(False)
            
        elif phase == Phase.NIGHT:
            self.map_view.set_visible_territory_markers(False)
            
            if not isinstance(self.engine.current_player, HumanPlayer):
                self.selected_entity_input.Update(visible=False)
                self.load_entity_frame.Update(visible=False)
                self.territory_label.Update(visible=False)
                self.movement_frame.Update(visible=False)
    
        
    def reset(self, replayReset=False):
        if not replayReset:
            self.engine.reset()
            self.loaded_replay_moves = None
            
        self.message_log.Update(value="")
        self.engine.first_turn()
        mapview = self.FindElement('mapview')
        mapview.reset()
        self.load_entity_frame.reset()
        
        self.turn_label.Update(value= "Turn: " + str(self.engine.game.turn_num))
        self.phase_label.Update(value= "Phase: " + self.engine.game.phase)
        self.player_info_label.Update(value= "Player: " + self.engine.current_player.name + " (" + self.engine.current_player.side + ")")
        
        player_tokens = [tok.name for tok in self.engine.game.entities.values() if not isinstance(tok, Civilian)]
        self.selected_entity_input.Update(values=player_tokens)

# TODO: reactivate for human in the loop        
#        if isinstance(self.engine.current_player, HumanPlayer):
#            self.selected_entity_input.Update(values=[tok.name for tok in self.engine.game.entities.values()])
#            #select the default selected entity from the input combo
#            self.on_select_entity(self.selected_entity_input.Values[self.selected_entity_input.TKCombo.current()])
#        else:
#            self.on_select_entity(None)
        
        self.goto_phase(self.engine.game.phase)
        
    
    def on_next_unit(self):
        #global selected_entity_index
        self.selected_entity_index += 1
        listvalues = self.selected_entity_input.Values
        if self.selected_entity_index >= len(listvalues):
            self.selected_entity_index = 0
        self.on_select_entity(listvalues[self.selected_entity_index])
    
    
    def on_next_move(self):
        #if we have run out of moves for the current phase move on the next
        #phase
        if self.replay.moves == []:
            #self.map_view.auto_update = False
            print("There are no further moves to show.") 
            print("Press 'Next Phase' to go to the next phase.")
            #self.on_do_phase()
        #else step through the saved replay moves
        else:
            self.map_view.auto_update = True
            self.replay.step()
    
    
    def on_space(self, event):
        self.on_next_unit()
    
    
    def run(self):
        while True:      
            event, values = self.Read()      
            
            if event is None or event == 'Quit':      
                break  
            elif event is "selected_entity_input":
                self.on_select_entity(values[event])
            elif event is "cargo_list":
                if self.loaded_replay_moves == None:
                    self.load_entity_frame.cargo_list_select(values)
                else:
                    print("Disabled in replay mode")
            elif event is "load_supply":
                if self.loaded_replay_moves == None:
                    self.load_entity_frame.on_load_supply()
                else:
                    print("Disabled in replay mode")
            elif event is "load_max_supply":
                if self.loaded_replay_moves == None:
                    self.load_entity_frame.on_load_max_supply()
                else:
                    print("Disabled in replay mode")
            elif event is "unload_cargo":
                if self.loaded_replay_moves == None:
                    self.load_entity_frame.on_unload_cargo(values)
                else:
                    print("Disabled in replay mode")
            elif event is "load_civilian":
                if self.loaded_replay_moves == None:
                    self.load_entity_frame.on_load_civilian()
                else:
                    print("Disabled in replay mode")
            elif event is "load_unit":
                if self.loaded_replay_moves == None:
                    self.load_entity_frame.on_load_unit(values)
                else:
                    print("Disabled in replay mode")
            elif event is "moving_isr":
                if self.loaded_replay_moves == None:
                    self.movement_frame.isr_on_move()
                else:
                    print("Disabled in replay mode")
            elif event is "end_phase":
                if self.loaded_replay_moves == None:
                    self.on_do_phase()
                else:
                    self.on_do_replay_phase()
            elif event is "next_unit":
                self.on_next_unit()
            elif event is "next_move":
                if self.loaded_replay_moves == None:
                    self.on_next_move()
                else:
                    self.on_do_replay_move()
            elif event is "restart_game":
                self.reset()
            elif event == "New Game":
                self.reset()
            elif event == "Save Replay":
                self.save_replay_file()
            elif event == "Load Replay":
                self.load_replay_file()
    

#==============================================================================







