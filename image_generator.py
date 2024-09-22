import logging
from ezdxf.addons.drawing import Frontend, RenderContext, svg, layout,config
import ezdxf

class ImageGenerator:
    def __init__(self,doc) -> None:
        self.doc=doc
        self.logger=logging.getLogger(self.__class__.__name__)
    
    def generate_image_of_block(self,block_name,width,height):
        block = self.doc.blocks.get(block_name)
        if block.name.startswith('mark_'):
            context = RenderContext(doc=self.doc)
            backend = svg.SVGBackend()
            # cfg = config.Configuration(
            #     background_policy=config.BackgroundPolicy.WHITE,
            #     color_policy=config.ColorPolicy.BLACK,
            #     # lineweight_policy= config.LineweightPolicy.ABSOLUTE,
            #     # custom_fg_color='#000000'
            # )
            cfg = config.Configuration(
                background_policy=config.BackgroundPolicy.WHITE,
                color_policy=config.ColorPolicy.WHITE,
                lineweight_policy= config.LineweightPolicy.ABSOLUTE,
            )
        
            frontend = Frontend(context, backend,config=cfg)
            frontend.draw_entities(block)
                
            # page = layout.Page(1920, 608, layout.Units.mm, margins=layout.Margins.all(20))
            page = layout.Page(width, height, layout.Units.px, margins=layout.Margins.all(20))
            svg_string = backend.get_string(page)
            self.logger.info("Image string succesfully generated")
        
    
        return svg_string

# if __name__=='__main__':
#    doc=ezdxf.readfile('/home/ritikshah/Downloads/ADVANCE SOFTWEAR DRAWING.dxf')
#    ig=ImageGenerator(doc)
#    print(ig.generate_image_of_block('mark_SC1_01',300 ,300))
 
                
            
    