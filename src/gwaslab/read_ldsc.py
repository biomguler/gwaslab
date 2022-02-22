import re
import pandas as pd
import numpy as np

def read_ldsc(filelist=[],mode="h2"):
#h2 mode
#####################################################################    
    if mode=="h2":
        summary = pd.DataFrame(columns = ['Filename', 'h2_obs', 'h2_se','Lambda_gc','Mean_chi2','Intercept','Intercept_se',"Ratio","Ratio_se"])
        
        for index, ldscfile in enumerate(filelist):
            print("Loading file "+str(index+1)+" :" + ldscfile +" ...")
            row={}
            
            with open(ldscfile,"r") as file:
                row["Filename"]=ldscfile.split("/")[-1]
                line=""
                while not re.compile('^Total Observed scale h2').match(line):
                    line = file.readline()
                    if not line: break
                        
                
                ## first line h2 se
                objects = re.compile('[a-zA-Z\s\d]+:|[-0-9.]+|NA').findall(line)
                row["h2_obs"]=objects[1]
                row["h2_se"]=objects[2]

                ##next line lambda gc

                objects = re.compile('[a-zA-Z\s\d]+:|[-0-9.]+|NA').findall(file.readline())
                row["Lambda_gc"] = objects[1]
                ##next line Mean_chi2

                objects = re.compile('[a-zA-Z\s\d]+:|[-0-9.]+|NA').findall(file.readline())
                row["Mean_chi2"]=objects[1]
                ##next line Intercept

                objects = re.compile('[a-zA-Z\s\d]+:|[-0-9.]+|NA').findall(file.readline())
                row["Intercept"]=objects[2]
                row["Intercept_se"]=objects[2]
                ##next line Ratio
                
                lastline=file.readline()
                if re.compile('NA').findall(lastline):
                    row["Ratio"]="NA"
                    row["Ratio_se"]="NA"
                elif re.compile('<').findall(lastline):
                    row["Ratio"]="Ratio < 0"
                    row["Ratio_se"]="NA"
                else:
                    objects = re.compile('[a-zA-Z\s\d]+:|[-0-9.]+').findall(lastline)
                    row["Ratio"]=objects[1]
                    row["Ratio_se"]=objects[2]
            summary = summary.append(row,ignore_index=True)
        print("Extracting finished !")
###############################################################################
        return summary     