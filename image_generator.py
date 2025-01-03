import logging
from ezdxf.addons.drawing import Frontend, RenderContext, svg, layout,config
import ezdxf
import re


class ImageGenerator:
    def __init__(self,doc) -> None:
        self.doc=doc
        self.logger=logging.getLogger(self.__class__.__name__)
        phase_regex_pattern=r"~PHASE_\d+/\d+"
        for block in doc.blocks:
             for entity in block:
                if entity.dxftype() == 'MTEXT' and  not re.match(phase_regex_pattern,entity.dxf.text):
                    entity.dxf.text = entity.dxf.text.replace(" ", "\u00A0")
                    entity.dxf.width*=5
                    entity.dxf.char_height*=1.4
            
    def generate_image_of_block(self,block_name,width,height):
        block = self.doc.blocks.get(block_name)
        if block.name.startswith('mark_'):
            self.logger.info("Image string generation started")
            context = RenderContext(doc=self.doc)
            backend = svg.SVGBackend()
            cfg=config.Configuration(
                lineweight_scaling=5,
            
            )
        
            frontend = Frontend(context, backend,config=cfg)
            frontend.draw_entities(block)
                
            # page = layout.Page(1920, 608, layout.Units.mm, margins=layout.Margins.all(20))
            page = layout.Page(width, height, layout.Units.px, margins=layout.Margins.all(20))
            svg_string = backend.get_string(page)
            self.logger.info("Image string succesfully generated")
        
    
        return svg_string

if __name__=='__main__':
   doc=ezdxf.readfile('/Users/kalyan/Documents/GitHub/epack/advance.dxf')
   ig=ImageGenerator(doc)
   with open('ok_file.svg','w') as f:
        # f.write(ig.generate_image_of_block('mark_SC1A_00',3508 ,2480))
        f.write(ig.generate_image_of_block('mark_SC1_01',3508 ,2480))

#    print(ig.generate_image_of_block('mark_SC1A_00',300 ,300))
 
                
            
    