import logging
from ezdxf.addons.drawing import Frontend, RenderContext, svg, layout,config
import ezdxf
import re


class ImageGenerator:
    def __init__(self,doc) -> None:
        self.doc=doc
        self.logger=logging.getLogger(self.__class__.__name__)
        self.phase_regex_pattern=r"~PHASE_\d+/\d+"
        
        for block in doc.blocks:
            for entity in block:
                if entity.dxftype() == 'MTEXT' and  not re.match(self.phase_regex_pattern, entity.dxf.text):
                    entity.dxf.width*=0
                    entity.dxf.char_height*=1.3
                    entity.dxf.text = entity.plain_text(fast=False).strip().replace("\n","")
                    entity.dxf.text = entity.dxf.text.replace(" ", "\u00A0")
                    
                    
                         
    def generate_image_of_block(self,block_name,width,height,lineweight):
        block = self.doc.blocks.get(block_name)
        if block.name.startswith('mark_'):
            # for entity in block:
            #     if entity.dxftype() == 'MTEXT' :
            #           print(entity.dxf.text)
            #Editing Image
            # for entity in block:
            #     if entity.dxftype() == 'MTEXT' and  not re.match(self.phase_regex_pattern,entity.dxf.text):
            #         entity.dxf.text = entity.dxf.text.replace(" ", "\u00A0")
            #         entity.dxf.width=0
            #         entity.dxf.char_height*=1.3
            #     elif entity.dxftype() == 'DIMENSION':
            #         for virtual_entity in entity.virtual_entities():
            #             if virtual_entity.dxftype() == 'MTEXT' and not re.match(self.phase_regex_pattern, virtual_entity.dxf.text):
            #                 virtual_entity.dxf.text = virtual_entity.plain_text(fast=False)
            #                 virtual_entity.dxf.text = virtual_entity.dxf.text.replace(" ", "\u00A0")
            #                 virtual_entity.dxf.width=0
            #                 virtual_entity.dxf.char_height*=1.3
            
            self.logger.info("Image string generation started")
            context = RenderContext(doc=self.doc)
            backend = svg.SVGBackend()
            cfg=config.Configuration(
                lineweight_scaling=lineweight,
            )
        
            frontend = Frontend(context, backend,config=cfg)
            frontend.draw_entities(block)
                
            # page = layout.Page(1920, 608, layout.Units.mm, margins=layout.Margins.all(20))
            page = layout.Page(width, height, layout.Units.px, margins=layout.Margins.all(20))
            svg_string = backend.get_string(page)
            self.logger.info("Image string succesfully generated")
        
    
        return svg_string

if __name__=='__main__':
   doc=ezdxf.readfile('/home/ritikshah/Downloads/RAWAT.dxf')
   ig=ImageGenerator(doc)
   for block in doc.blocks:
       if block.name.startswith('mark_'):
           with open (f'{block.name}.svg', 'w') as f:
               f.write(ig.generate_image_of_block(block.name, 1920, 1080))
               print(f"Image of {block.name} generated successfully")

#    print(ig.generate_image_of_block('mark_SC1_01',300 ,300)