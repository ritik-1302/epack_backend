import re
import logging
from image_generator import ImageGenerator
from inventory_handler import InventoryHandler
import math

import re
import math
class DXFExtractor:
    def __init__(self,doc,density) -> None:
        self.parts_regex_pattern = r"\\A1;\d+X\d+X\d+ \w+(\~\d+)?"
        self.phase_regex_pattern=r"~PHASE_\d+/\d+"
        self.pipe_regex_MTEXT_pattern=r'\\A\d+;\d+ PB\d~{\\A\d+;\\C\d+;\d+NB \(M\)PIPE}'
        self.pipe_regex_DIMENSION_pattern=r'<> PB\d~{\\A\d+;\\C\d+;\d+NB \(M\)PIPE}'
        self.doc=doc
        self.density=density
        self.logger=logging.getLogger(self.__class__.__name__)


    def extract_parts_from_block(self,image_width,image_height):
        self.logger.info("Extracting parts from block")
        inventory_list = InventoryHandler().get_inventory_list()
        block_wise_parts_dict={}
        ig=ImageGenerator(self.doc)
        duplicate_check_dict={}
        for block in self.doc.blocks:
            if block.name.startswith('mark_'):
                block_wise_parts_dict[block.name] = {"parts": [], "phase": {}, "image_url": ig.generate_image_of_block(block_name=block.name, width=image_width, height=image_height)}
                duplicate_check_dict[block.name]={}
                for entity in block:
                    if entity.dxftype()=="DIMENSION":
                        for virtual_entity in entity.virtual_entities():
                            if virtual_entity.dxftype() == "MTEXT" and re.match(self.parts_regex_pattern,virtual_entity.dxf.text) :
                                try:
                                    part_str=virtual_entity.dxf.text[4:]
                                    dimention,name=part_str.split(" ")
                                    length, width, thickness = dimention.split("X")
                                    length = int(length)
                                    width = int( width)
                                    thickness = int(thickness)
                                    area = ((length * width) * 2 + (length * thickness) * 2 + (width * thickness) * 2)/ 1000000  # Calculate area
                                    volume = length * width * thickness / 1000000000  
                                    weight = volume * float(self.density)
                                    
                                    
                                    if '~' in name:
                                        part_name,qty=name.split('~')
                                    else:
                                        qty=1
                                        part_name=name
                                        
                                    if part_name not in duplicate_check_dict[block.name]:
                                        block_wise_parts_dict[block.name]['parts'].append({
                                        "Part Name": part_name.upper(),
                                        "Thickness (mm)": int(thickness),
                                        "Quantity": int(qty),
                                        "Length (mm)": int(length),
                                        "Width (mm)": int(width),
                                        "Area (m2)": round(area,2) if round(area,2)!=0 else area,
                                        "Volume (m3)": round(volume,2) if round(volume,2) else volume ,
                                        "Weight (kg)": round(weight,2) if round(weight, 2) else weight
                                        })
                                        duplicate_check_dict[block.name][part_name]=True
                                        
                                except Exception as e:
                                    self.logger.error(f"Error  {e}")
                            elif virtual_entity.dxftype()=="MTEXT" and re.match(self.pipe_regex_MTEXT_pattern,virtual_entity.dxf.text):
                                
                                try:
                                    part_str=virtual_entity.dxf.text[4:]
                                    length,str0,pipename=part_str.split(" ")
                                    partname,str1=str0.split('~')
                                    pipe_name=str1.split(';')[2]
                                    pipe_mark=pipe_name+pipename[0:3]
                                    pipe=next((item for item in inventory_list if item["itemDescription"] == pipe_mark), None)
                                    area=(2*math.pi*math.pow(int(pipe["thickness"])/2,2)+math.pi*int(pipe["thickness"])*int(length))/1000000
                                    volume=(math.pi*math.pow(int(pipe["thickness"])/2,2)*int(length))/1000000000
                                    weight=int(pipe["weightPerMeter"])*int(length)/1000
                                    
                                    if partname not in duplicate_check_dict[block.name]:
                                        block_wise_parts_dict[block.name]['parts'].append({
                                        "Part Name": partname.upper()+" "+f"({pipe_mark} PIPE)",
                                        "Thickness (mm)": int(pipe["thickness"]),
                                        "Quantity": 1,
                                        "Length (mm)": int(length),
                                        "Width (mm)": int(pipe["thickness"]),
                                        "Area (m2)": round(area,2) if round(area,2)!=0 else area,
                                        "Volume (m3)": round(volume,2) if round(volume,2)!=0 else volume,
                                        "Weight (kg)": round(weight,2) if round(weight,2)!=0 else weight 
                                        })
                                        duplicate_check_dict[block.name][partname]=True
                                except Exception as e:
                                    self.logger.error(f"Error  yoo  {e}")
                                    
                    elif entity.dxftype() == "MTEXT" and re.match(self.phase_regex_pattern, entity.dxf.text):
                       try:
                            phase_strings= re.findall(self.phase_regex_pattern,entity.dxf.text)
                            for phase_str in phase_strings:
                                    phase_str=phase_str[1:]
                                    phase_name,phase_qty=phase_str.split("/")
                                    block_wise_parts_dict[block.name]["phase"][phase_name]=float(phase_qty)
                       except Exception as e:
                           self.logger.error(f"Error  {e}")
                            
                    elif entity.dxftype() == "MTEXT" and re.match(self.parts_regex_pattern[5:],entity.dxf.text):
                        try:
                            part_str=entity.dxf.text.strip()
                            dimention,name=part_str.split(" ")
                            length, width, thickness = dimention.split("X")
                            length = int(length)
                            width = int( width)
                            thickness = int(thickness)
                            area = ((length * width) * 2 + (length * thickness) * 2 + (width * thickness) * 2)/ 1000000  # Calculate area
                            volume = length * width * thickness / 1000000000  
                            weight = volume * float(self.density)
                            
                            
                            if '~' in name:
                                part_name,qty=name.split('~')
                            else:
                                qty=1
                                part_name=name
                                
                            
                            if part_name not in duplicate_check_dict[block.name]:
                                block_wise_parts_dict[block.name]['parts'].append({
                                "Part Name": part_name.upper(),
                                "Thickness (mm)": int(thickness),
                                "Quantity": int(qty),
                                "Length (mm)": int(length),
                                "Width (mm)": int(width),
                                "Area (m2)": round(area,2) if round(area,2)!=0 else area,
                                "Volume (m3)": round(volume,2) if round(volume,2)!=0 else volume ,
                                "Weight (kg)": round(weight,2) if round(weight,2)!=0 else weight
                                })
                                duplicate_check_dict[block.name][part_name]=True
                            
                        except Exception as e:
                            self.logger.error(f"Error  {e}")
        
                        
        self.logger.info("Sucessfully generated blockwise parts dict")
        return block_wise_parts_dict                            
                            
                
        

                            
                            

                        
                       
        
        
if __name__=="__main__":    

       import json
       import ezdxf
       doc=ezdxf.readfile('/Users/kalyan/Documents/GitHub/epack/advance.dxf')
       extractor=DXFExtractor(doc,3)
    #    print(extractor.extract_parts_from_block(300,300))
       with open('data.json', 'w') as outfile:
           json.dump(extractor.extract_parts_from_block(300, 300), outfile)
    



                    
                    
                    
            
        
        

    
    
    