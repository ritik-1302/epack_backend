import openpyxl


class ExcelGenerator:
    def __init__(self,block_wise_parts_dict) -> None:
        self.block_wise_parts_dict=block_wise_parts_dict
        self.block_header_list=["SNO","ITEM TYPE"	,"SECTION SIZE",	"SUB PART",	"LENGTH", "QTY", 	"UNIT WT.","TOTAL WT",	"SURFACE AREA (M2)","TOTAL SURFACE AREA (M2)",	"PART MARK",	"PART DESCRIPTION",	"LENGTH","WIDTH",	"THK.", "QTY.",	"QTY./BLDG.",	"YIELD",	"WEIGHT",	"SURFACE AREA (M2)"]
        self.item_type_dict={
    "SC": "Column",
    "RF": "Rafter",
    "PC": "Portal Column",
    "PB": "Portal Beam",
    "GST": "Gusset Plate",
    "PBR": "Pipe Bracing",
    "BR": "Pipe Bracing",
    "STP": "Strut Pipe",
    "CL": "Clip",
    "ANG": "Angle",
    "RA": "Angle",
    "PP": "Packing Plate",
    "4CBM9A": "Crane Beam",
    "MB": "Mezzanine Beam",
    "JS": "Mezzanine Joist",
    "ISMC": "ISMC00",
    "BKT": "Bracket",
    "ST": "Stiffener",
    "EC": "End Wall Column",
    "MC": "Mezzanine Column",
    "T": "Splice Plate",
    "LPX": "Fascia Column",
    "ICO": "Intermediate Column",
    "IC": "Intermediate Column",
    "CRF": "Canopy Rafter",
    "SBX": "Surge Beam",
    "CON": "Canopy Connector",
    "CC": "Canopy Connector",
    "LD": "Cage Ladder",
    "CJ": "'C' Section Jamb",
    "HR": "Hand Rail",
    "PL": "Loose Splice Plate",
    "LC": "Len To Column",
    "JB": "Jack Beam",
    "MRF": "Monitor Rafter",
    "KAG": "Crane Beam Angle",
    "CCL": "Crane Beam Clip",
    "CSTP": "Crane Stopper",
    "CHQ": "Chequered Plate",
    "GTR": "Grating",
    "ER": "End Wall Rafter",
    "ISMB": "ISMC00",
    "CHP": "Header Plate",
    "BM": "Tie Beam",
    "LP": "Life Line",
    "TR": "Truss",
    "ABR": "Angle Bracing",
    "STD-SPL0": "Shim Plate",
    "SA": "Sag Angle",
    "SSC": "Staircase Stringer",
    "TD": "Trade",
    "SCL": "Stair Clip",
    "SB": "Stair Beam",
    "WB": "Walkway Beam",
    "WCL": "Walkway Clip",
    "LCL": "Lean To Column",
    "STC": "Stub Column",
    "STB": "Stub Beam"
}

    
    
    def generate_excel_for_phase(self,phase_name):
        
        wb=openpyxl.Workbook()
        sheet=wb.active
        
        
        for block_name,block_details in  self.block_wise_parts_dict.items():
            total_sa=0
            total_w=0
            
            if block_details['phase'].get(phase_name) is not None:
                phase_qty=int(block_details['phase'][phase_name])
            else:
                phase_qty=1
                
            for parts_dict in block_details['parts']:
                total_sa=total_sa+parts_dict["Area (m2)"]
                total_w=total_w+parts_dict["Weight (kg)"]
            
            item_type="UNKNOWN"
            
            for key,value in self.item_type_dict.items():
                try:
                    item_name=block_name.split("_")[1];
                    print(item_name)
                    item_name=''.join(i for i in item_name if i.isdigit()==False)
                    print(item_name)
                    if key.lower() == item_name.lower():
                        item_type=value
                        break
                except Exception as e:
                    self.logger.error(f"Error  {e}")
                    continue
                
            
            sheet.append([])
            sheet.append(self.block_header_list)
            sheet.append(["",item_type.upper(),"",block_name,"",phase_qty,total_w,phase_qty*total_w,total_sa,total_sa*phase_qty])
            sheet.append(["","","","","","","","","","","PART MARK","PART DESCRIPTION",	"LENGTH","WIDTH",	"THK.", "QTY.",	"QTY./BLDG.",	"YIELD",	"WEIGHT",	"SURFACE AREA (M2)"])
            for parts_dict in block_details['parts']:
                yeild="240" if "PIPE" in parts_dict["Part Name"] else "345"
                sheet.append(["","","","","","","","","","",parts_dict["Part Name"],"",parts_dict['Length (mm)'],parts_dict["Width (mm)"],parts_dict["Thickness (mm)"],parts_dict["Quantity"],int(parts_dict["Quantity"])*phase_qty,yeild,parts_dict["Weight (kg)"],parts_dict["Area (m2)"]])
        
        
        return wb
        
        

    
    
    
    

if __name__=="__main__":
    import json
    with open('data.json', 'r') as file:
        data = json.load(file)

        xl=ExcelGenerator(block_wise_parts_dict=data)
        # print(xl.block_header_list[10:])
        # xl.generate_excel_for_phase("PHASE_1")
        #save the excel into a file
        xl.generate_excel_for_phase("PHASE_1").save("test.xlsx")
        
    