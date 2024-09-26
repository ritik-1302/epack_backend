import re
import logging
import ezdxf
from image_generator import ImageGenerator

class DXFExtractor:
    def __init__(self,doc,density) -> None:
        self.parts_regex_pattern = r"\\A1;\d+X\d+X\d+ \w+(\~\d+)?"
        self.phase_regex_pattern=r"~PHASE_\d+/\d+"
        self.doc=doc
        self.density=density
        self.logger=logging.getLogger(self.__class__.__name__)
        
    
    def make_parts_dict(self):
        parts_dict={}
        for block in self.doc.blocks:
            if block.name.startswith('mark_'):
                parts_dict[block.name]={}
                for entity in block:
                    
                    if entity.dxftype()=="DIMENSION":
                        if "X" in entity.dxf.text and "{" not in entity.dxf.text and "\\" not in entity.dxf.text:
                            part_str=entity.dxf.text[2:]
                            dimension,name=part_str.split(" ")
                            
                            if '~' in name:
                                part_name,parts_qty=name.split('~')
                                parts_qty=float(parts_qty)
                            else:
                                part_name=name
                                parts_qty=1.0
                            
                           
                                
                                
                            if 'X' in dimension:
                                val=dimension.split('X')
                                parts_dict[block.name][part_name]=val[1]+'x'+val[2]        
                                           
        return parts_dict

    
    
    def extract_parts_from_block(self,image_width,image_height):
        block_wise_parts_dict={}
        parts_dict=self.make_parts_dict()
        track_dict={}
        ig=ImageGenerator(self.doc)
        for key,value in parts_dict.items():
                block_wise_parts_dict[key]={"parts":[],"phase":{},"image_url":ig.generate_image_of_block(block_name=key,width=image_width,height=image_height)}
                track_dict[key]={}
                
        for block in self.doc.blocks: 
            for entity in block:                
                    if entity.dxftype()=="MTEXT" and re.match(self.parts_regex_pattern,entity.dxf.text):
                        part_str=entity.dxf.text[4:]
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
                            
                        
                        
                        for key,value in parts_dict.items():
                            if value.get(part_name) and value[part_name]==str(width)+'x'+str(thickness) and track_dict[key].get(part_name) is None:
                                block_wise_parts_dict[key]['parts'].append({
                            "Part Name": part_name.upper(),
                            "Thickness (mm)": int(thickness),
                            "Quantity": int(qty),
                            "Length (mm)": int(length),
                            "Width (mm)": int(width),
                            "Area (m2)": area,
                            "Volume (m3)": volume,
                            "Weight (kg)": weight
                            })
                    
                                track_dict[key][part_name]=True
                                
                    elif entity.dxftype()=="MTEXT" and re.match(self.phase_regex_pattern,entity.dxf.text):
                        phase_strings= re.findall(self.phase_regex_pattern,entity.dxf.text)
                        for phase_str in phase_strings:
                            phase_str=phase_str[1:]
                            phase_name,phase_qty=phase_str.split("/")
                            block_wise_parts_dict[block.name]["phase"][phase_name]=float(phase_qty)
                      
        
        self.logger.info("Sucessfully generated blockwise parts dict")
                                       
                        
        return block_wise_parts_dict

                            
                            

                        
                       
        
        
if __name__=="__main__":    

       import json
       doc=ezdxf.readfile('/home/ritikshah/Downloads/ADVANCE SOFTWEAR DRAWING.dxf')
       extractor=DXFExtractor(doc,3)
       json_object=json.dumps(extractor.extract_parts_from_block(300,300))
       with open("test.json","w") as outfile:
           outfile.write(json_object)
    #    print(extractor.extract_parts_from_block())
    



                    
                    
                    
            
        
        

    
    
    