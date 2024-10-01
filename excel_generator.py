import openpyxl


class ExcelGenerator:
    def __init__(self,block_wise_parts_dict) -> None:
        self.block_wise_parts_dict=block_wise_parts_dict
        self.block_header_list=["SNO","ITEM TYPE"	,"SECTION SIZE",	"SUB PART",	"LENGTH", "QTY", 	"UNIT WT.","TOTAL WT",	"SURFACE AREA (M2)","TOTAL SURFACE AREA (M2)",	"PART MARK",	"PART DESCRIPTION",	"LENGTH","WIDTH",	"THK.", "QTY.",	"QTY./BLDG.",	"YIELD",	"WEIGHT",	"SURFACE AREA (M2)"]
    
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
                
                
            
            sheet.append([])
            sheet.append(self.block_header_list)
            sheet.append(["","COLUMN","",block_name,"",phase_qty,total_w,phase_qty*total_w,total_sa,total_sa*phase_qty])
            sheet.append(["","","","","","","","","","","PART MARK","PART DESCRIPTION",	"LENGTH","WIDTH",	"THK.", "QTY.",	"QTY./BLDG.",	"YIELD",	"WEIGHT",	"SURFACE AREA (M2)"])
            for parts_dict in block_details['parts']:
                sheet.append(["","","","","","","","","","",parts_dict["Part Name"],"",parts_dict['Length (mm)'],parts_dict["Width (mm)"],parts_dict["Thickness (mm)"],parts_dict["Quantity"],int(parts_dict["Quantity"])*phase_qty,"",parts_dict["Weight (kg)"],parts_dict["Area (m2)"]])
        
        
        return wb
        
        

    
    
    
    

if __name__=="__main__":
    import json
    with open('test.json', 'r') as file:
        data = json.load(file)

        xl=ExcelGenerator(block_wise_parts_dict=data)
        # print(xl.block_header_list[10:])
        xl.generate_excel_for_phase("PHASE_1")
    # wb.save("hello.xlsx")