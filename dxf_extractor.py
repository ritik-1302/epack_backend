import re
import logging
import ezdxf
from image_generator import ImageGenerator
from inventory_handler import InventoryHandler
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
    
    def filter_blocks_list(self):
        latest_revision_dict={}
        block_list=[]
        for block in self.doc.blocks:
            if block.name.startswith('mark_'):
                match=re.search(r'(\d+)$',block.name)
                revisionless_block_name=block.name.replace(match.group(1),'')
                if match:
                    revision_number = int(match.group(1))
                    if block.name in latest_revision_dict:
                        if revision_number > latest_revision_dict[block.name]:
                            latest_revision_dict[revisionless_block_name] = revision_number
                    else:
                        latest_revision_dict[revisionless_block_name] = revision_number
        
        
        for block in self.doc.blocks:
            if block.name.startswith('mark_'):
                match=re.search(r'(\d+)$', block.name)
                revisionless_block_name=block.name.replace(match.group(1), '')
                if match:
                    revision_number = int(match.group(1))
                    if revision_number == latest_revision_dict[revisionless_block_name]:
                        block_list.append(block.name)
        return block_list

        
    
    def make_parts_dict(self):
        latest_revision_block_list=self.filter_blocks_list()
        parts_dict={}
        for block in self.doc.blocks:
            if block.name.startswith('mark_') and block.name in latest_revision_block_list :
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
                                
                        elif re.match(self.pipe_regex_DIMENSION_pattern, entity.dxf.text):
                            part_txt=entity.dxf.text[2:]
                            name,extra_text= part_txt.split('~')
                            name=name.strip()
                            parts_dict[block.name][name]=name
                                           
        return parts_dict

    
    
    def extract_parts_from_block(self,image_width,image_height):
        inventory_list = InventoryHandler().get_inventory_list()
        latest_revision_block_list=self.filter_blocks_list()
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
                                
                    elif entity.dxftype()=="MTEXT" and re.match(self.phase_regex_pattern,entity.dxf.text) and block.name in latest_revision_block_list:
                        phase_strings= re.findall(self.phase_regex_pattern,entity.dxf.text)
                        for phase_str in phase_strings:
                            phase_str=phase_str[1:]
                            phase_name,phase_qty=phase_str.split("/")
                            block_wise_parts_dict[block.name]["phase"][phase_name]=float(phase_qty)
                            
                    
                    elif entity.dxftype()=="MTEXT" and re.match(self.pipe_regex_MTEXT_pattern, entity.dxf.text):
                        part_str=entity.dxf.text[4:]
                        length,str0,pipename=part_str.split(" ")
                        partname,str1=str0.split('~')
                        pipe_name=str1.split(';')[2]
                        pipe_mark=pipe_name+pipename[0:3]
                        # print(partname,length,pipe_name+pipename[0:3])
                        pipe=next((item for item in inventory_list if item["itemDescription"] == pipe_mark), None)
                        # print(temp)
                        for key,value in parts_dict.items():
                            if value.get(partname) and track_dict[key].get(partname) is None:
                                block_wise_parts_dict[key]['parts'].append({
                            "Part Name": partname.upper(),
                            "Thickness (mm)": int(pipe["thickness"]),
                            "Quantity": 1,
                            "Length (mm)": int(length),
                            "Width (mm)": int(pipe["thickness"]),
                            "Area (m2)": (2*math.pi*math.pow(int(pipe["thickness"])/2,2)+math.pi*int(pipe["thickness"])*int(length))/1000000,
                            "Volume (m3)": (math.pi*math.pow(int(pipe["thickness"])/2,2)*int(length))/1000000000,
                            "Weight (kg)": int(pipe["weightPerMeter"])*int(length)/1000
                            })
                        
        
        self.logger.info("Sucessfully generated blockwise parts dict")
                                       
                        
        return block_wise_parts_dict

                            
                            

                        
                       
        
        
if __name__=="__main__":    

       import json
       doc=ezdxf.readfile('/home/ritikshah/Downloads/inventory_1.dxf')
       extractor=DXFExtractor(doc,3)
    #    print(extractor.filter_blocks_list())
    #    print(extractor.extract_parts_from_block(300,300))
    #    print(extractor.extract_parts_from_block(300,300))
       with open('data.json', 'w') as outfile:
           json.dump(extractor.extract_parts_from_block(300, 300), outfile)
    



                    
                    
                    
            
        
        

    
    
    