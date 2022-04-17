import sys
import gwaslab as gl
import os, psutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as ss
import seaborn as sns

#20220417
def compare_effect(path1,
                   cols_name_list_1, effect_cols_list_1,
                   path2,
                   cols_name_list_2, effect_cols_list_2,
                   label1="Sumstats_1",
                   label2="Sumstats_2",
                   label3="Both",
                   label0="Not in any",
                   snplist=None,
                   mode="beta",
                   anno=False,
                   null_beta=0,
                   sig_level=5e-8,
                   legend_title=r'$ P < 5 x 10^{-8}$ in:',
                   legend_pos='upper left',
                   is_reg=True,
                   is_45_helper_line=True,
                   scatterargs={"s":20},
                   plt_args={"figsize":(8,8),"dpi":300},
                   helper_line_args={"color":'black', "linestyle":'-',"lw":1},
                   fontargs={'family':'sans','fontname':'Arial','fontsize':12},
                   errargs={"ecolor":"#cccccc","elinewidth":1},
                   verbose=False):
    
    #[snpid,p,ea,nea]        ,[effect,se]
    #[snpid,p,ea,nea,chr,pos],[effect,se]
    #[snpid,p,ea,nea,chr,pos],[OR,OR_l,OR_h]
    
    ######### 1 check the value used to plot
    if mode not in ["Beta","beta","BETA","OR","or"]:
        raise ValueError("Please input Beta or OR")
    
    ######### 2 extract snplist2
    if verbose: print("Loading "+label2+" SNP list...")
    sumstats = pd.read_table(path2,sep="\s+",usecols=[cols_name_list_2[0]])
    common_snp_set=set(sumstats[cols_name_list_2[0]].values)
    
    ######### 3 extract snplist1
    if snplist is not None:
        cols_to_extract = [cols_name_list_1[0],cols_name_list_1[1]]
    else:
        cols_to_extract = [cols_name_list_1[0],cols_name_list_1[1],cols_name_list_1[4],cols_name_list_1[5]]
    
    ######### 4 load sumstats1
    if verbose: print("Loading sumstats: "+label1+"...")
    sumstats = pd.read_table(path1,sep="\s+",usecols=cols_to_extract)
    
    ######### 5 extract the common set
    common_snp_set = common_snp_set.intersection(sumstats[cols_name_list_1[0]].values)
    if verbose: print("Counting common snps : ",len(common_snp_set)," variants...")
    
    ######### 6 rename the sumstats
    rename_dict = { cols_name_list_1[0]:"SNPID",
                    cols_name_list_1[1]:"P",
    }
    if snplist is None: 
        rename_dict[cols_name_list_1[4]]="CHR"
        rename_dict[cols_name_list_1[5]]="POS"
    sumstats.rename(columns=rename_dict,inplace=True)
    
    ######### 7 exctract only common variants from sumstats1 
    sumstats=sumstats.loc[sumstats["SNPID"].isin(common_snp_set),:]
    if verbose: print("Using only common snps : ",len(common_snp_set)," variants...")
    
    ######### 8 extact SNPs for comparison 
    
    if verbose: print("Extract top/given snps from "+label1+"...")
    
    if snplist is not None: 
        ######### 8.1 if a snplist is provided, use the snp list
        if verbose: print("Extract snps in the given list from "+label1+"...")
        sig_list_1 = sumstats.loc[sumstats["SNPID"].isin(snplist),:]
    else:
        ######### 8,2 otherwise use the sutomatically detected lead SNPs
        sig_list_1 = gl.getsig(sumstats,"SNPID","CHR","POS","P",
                               verbose=verbose,sig_level=sig_level)

    ######### 9 extract snplist2
    if snplist is not None:
        cols_to_extract = [cols_name_list_2[0],cols_name_list_2[1]]
    else:
        cols_to_extract = [cols_name_list_2[0],cols_name_list_2[1],cols_name_list_2[4],cols_name_list_2[5]]
    if verbose: print("Loading sumstats:"+label2+"...")
    sumstats = pd.read_table(path2,sep="\s+",usecols=cols_to_extract)
    
    ######### 10 rename sumstats2
    rename_dict = { cols_name_list_2[0]:"SNPID",
                    cols_name_list_2[1]:"P",
    }
    if snplist is None: 
        rename_dict[cols_name_list_2[4]]="CHR"
        rename_dict[cols_name_list_2[5]]="POS"
    sumstats.rename(columns=rename_dict,inplace=True)
    
    ######### 11 exctract only common variants from sumstats2
    sumstats=sumstats.loc[sumstats["SNPID"].isin(common_snp_set),:]
    if verbose: print("Using only common snps : ",len(common_snp_set)," variants...")
    
    
    ######## 12 extact SNPs for comparison 
    if snplist: 
        ######### 12.1 if a snplist is provided, use the snp list
        if verbose: print("Extract snps in the given list from "+label2+"...")
        sig_list_2 = sumstats.loc[sumstats["SNPID"].isin(snplist),:]
    else: 
        if verbose: print("Extract lead snps from "+label2+"...")
        ######### 12.2 otherwise use the sutomatically detected lead SNPs
        sig_list_2 = gl.getsig(sumstats,"SNPID","CHR","POS","P",
                                 verbose=verbose,sig_level=sig_level)
    
    ######### 13 Merge two list using SNPID
    ##############################################################################
    if verbose: print("Merging snps from "+label1+" and "+label2+"...")
    sig_list_merged = pd.merge(sig_list_1,sig_list_2,left_on="SNPID",right_on="SNPID",how="outer",suffixes=('_1', '_2'))
    
    ###############################################################################
    
    ########## 14 Merging sumstats1
    if verbose: print("Extract EFFECT_ALLELE, NON_EFFECT_ALLELE, EFFECT_SIZE/SE, OR/OR_L/OR_H of selected snps from "+label1+"...")
    if mode=="beta" or mode=="BETA" or mode=="Beta":
        cols_to_extract = [cols_name_list_1[0],cols_name_list_1[2],cols_name_list_1[3], effect_cols_list_1[0], effect_cols_list_1[1]]
    else:
        cols_to_extract = [cols_name_list_1[0],cols_name_list_1[2],cols_name_list_1[3], effect_cols_list_1[0], effect_cols_list_1[1], effect_cols_list_1[2]]
        
    sumstats = pd.read_table(path1,sep="\s+",usecols=cols_to_extract)
    
    if mode=="beta" or mode=="BETA" or mode=="Beta":
          rename_dict = { cols_name_list_1[0]:"SNPID",
                        cols_name_list_1[2]:"EA_1",
                        cols_name_list_1[3]:"NEA_1",
                        effect_cols_list_1[0]:"EFFECT_1",
                        effect_cols_list_1[1]:"SE_1",
    }
    else:
                    rename_dict = { cols_name_list_1[0]:"SNPID",
                        cols_name_list_1[2]:"EA_1",
                        cols_name_list_1[3]:"NEA_1",
                        effect_cols_list_1[0]:"OR_1",
                        effect_cols_list_1[1]:"OR_L_1",
                        effect_cols_list_1[2]:"OR_H_1"
    }
    
    sumstats.rename(columns=rename_dict, inplace=True)
    
    if verbose: print("Merging "+label1+" effect information...")
    sig_list_merged = pd.merge(sig_list_merged,sumstats,
                               left_on="SNPID",right_on="SNPID",
                               how="left")
    
    ############ 15 merging sumstats2
    if verbose: print("Extract EFFECT_ALLELE, NON_EFFECT_ALLELE, EFFECT_SIZE/SE , OR/OR_L/OR_H of selected snps from "+label2+"...")
    if mode=="beta" or mode=="BETA" or mode=="Beta":
        cols_to_extract = [cols_name_list_2[0],cols_name_list_2[2],cols_name_list_2[3], effect_cols_list_2[0], effect_cols_list_2[1]]
    else:
        cols_to_extract = [cols_name_list_2[0],cols_name_list_2[2],cols_name_list_2[3], effect_cols_list_2[0], effect_cols_list_2[1], effect_cols_list_2[2]]
    
    sumstats = pd.read_table(path2,sep="\s+",usecols=cols_to_extract)
    
    if mode=="beta" or mode=="BETA" or mode=="Beta":
          rename_dict = { cols_name_list_2[0]:"SNPID",
                        cols_name_list_2[2]:"EA_2",
                        cols_name_list_2[3]:"NEA_2",
                        effect_cols_list_2[0]:"EFFECT_2",
                        effect_cols_list_2[1]:"SE_2",
    }
    else:
                    rename_dict = { cols_name_list_2[0]:"SNPID",
                        cols_name_list_2[2]:"EA_2",
                        cols_name_list_2[3]:"NEA_2",
                        effect_cols_list_2[0]:"OR_2",
                        effect_cols_list_2[1]:"OR_L_2",
                        effect_cols_list_2[2]:"OR_H_2"
    }
    sumstats.rename(columns=rename_dict, inplace=True)         
    
    
    if verbose: print("Merging "+label2+" effect information...")
    sig_list_merged = pd.merge(sig_list_merged,sumstats,
                               left_on="SNPID",right_on="SNPID",
                               how="left")
    
    sig_list_merged.set_index("SNPID",inplace=True)
    
    ################ 16 update sumstats1
    sumstats = pd.read_table(path1,sep="\s+",usecols=[cols_name_list_1[0],cols_name_list_1[1]])
    sumstats.rename(columns={
                        cols_name_list_1[0]:"SNPID",
                        cols_name_list_1[1]:"P_1"
                              },
                     inplace=True)
    sumstats.set_index("SNPID",inplace=True)
    sig_list_merged.update(sumstats)
    
    ################# 17 update sumstats2
    sumstats = pd.read_table(path2,sep="\s+",usecols=[cols_name_list_2[0],cols_name_list_2[1]])
    sumstats.rename(columns={
                        cols_name_list_2[0]:"SNPID",
                        cols_name_list_2[1]:"P_2"
                              },
                     inplace=True)
    sumstats.set_index("SNPID",inplace=True)
    sig_list_merged.update(sumstats)
    
    ####
#################################################################################
    
    ############## 18 init indicator
    sig_list_merged["indicator"] = 0
    sig_list_merged.loc[sig_list_merged["P_1"]<sig_level,"indicator"]=1+sig_list_merged.loc[sig_list_merged["P_1"]<sig_level,"indicator"]
    sig_list_merged.loc[sig_list_merged["P_2"]<sig_level,"indicator"]=2+sig_list_merged.loc[sig_list_merged["P_2"]<sig_level,"indicator"]
    if snplist is None:
        sig_list_merged["CHR"]=np.max(sig_list_merged[["CHR_1","CHR_2"]], axis=1).astype(int)
        sig_list_merged["POS"]=np.max(sig_list_merged[["POS_1","POS_2"]], axis=1).astype(int)
        sig_list_merged.drop(labels=['CHR_1', 'CHR_2','POS_1', 'POS_2'], axis=1,inplace=True)
    
    ############### 19 align allele effect with sumstats 1
    if mode=="beta" or mode=="BETA" or mode=="Beta":
        sig_list_merged["EA_2_aligned"]=sig_list_merged["EA_2"]
        sig_list_merged["NEA_2_aligned"]=sig_list_merged["NEA_2"]
        sig_list_merged["EFFECT_2_aligned"]=sig_list_merged["EFFECT_2"]

        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"EA_2_aligned"]= sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"NEA_2"]
        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"NEA_2_aligned"]= sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"EA_2"]
        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"EFFECT_2_aligned"]= -sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"EFFECT_2"]
    else:
        #or - +
        sig_list_merged["OR_L_1"]=np.abs(sig_list_merged["OR_L_1"]-sig_list_merged["OR_1"])
        sig_list_merged["OR_H_1"]=np.abs(sig_list_merged["OR_H_1"]-sig_list_merged["OR_1"])
        sig_list_merged["OR_L_2"]=np.abs(sig_list_merged["OR_L_2"]-sig_list_merged["OR_2"])
        sig_list_merged["OR_H_2"]=np.abs(sig_list_merged["OR_H_2"]-sig_list_merged["OR_2"])
        
        sig_list_merged["EA_2_aligned"]=sig_list_merged["EA_2"]
        sig_list_merged["NEA_2_aligned"]=sig_list_merged["NEA_2"]
        sig_list_merged["OR_2_aligned"]=sig_list_merged["OR_2"]
        sig_list_merged["OR_L_2_aligned"]=sig_list_merged["OR_L_2"]
        sig_list_merged["OR_H_2_aligned"]=sig_list_merged["OR_H_2"]

        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"EA_2_aligned"]= sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"NEA_2"]
        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"NEA_2_aligned"]= sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"EA_2"]
        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"OR_2_aligned"]= 1/sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"OR_2"]
        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"OR_L_2_aligned"]= 1/sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"OR_L_2"]
        sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"OR_H_2_aligned"]= 1/sig_list_merged.loc[sig_list_merged["EA_1"]!=sig_list_merged["EA_2"],"OR_H_2"]
        
    
    ####################################################################################################################################
    save_path = label1+"_"+label2+"_beta_sig_list_merged.tsv"
    sig_list_merged.to_csv(save_path,"\t")
    
    sum0 = sig_list_merged.loc[sig_list_merged["indicator"]==0,:].dropna(axis=0)
    sum1only = sig_list_merged.loc[sig_list_merged["indicator"]==1,:].dropna(axis=0)
    sum2only = sig_list_merged.loc[sig_list_merged["indicator"]==2,:].dropna(axis=0)
    both     = sig_list_merged.loc[sig_list_merged["indicator"]==3,:].dropna(axis=0)
    
    if verbose: print("Identified "+str(len(sum0)) + " variants which are not significant in " + label3+".")
    if verbose: print("Identified "+str(len(sum1only)) + " variants which are only significant in " + label1+".")
    if verbose: print("Identified "+str(len(sum2only)) + " variants which are only significant in " + label2+".")
    if verbose: print("Identified "+str(len(both)) + " variants which are significant in " + label3 + ".")
    
    ##plot########################################################################################
    if verbose: print("Plotting the scatter plot for effect size comparison...")
    #plt.style.use("ggplot")
    sns.set_style("ticks")
    fig,ax = plt.subplots(**plt_args) 
    
    if mode=="beta" or mode=="BETA" or mode=="Beta":
        if len(sum0)>0:
            ax.errorbar(sum0["EFFECT_1"],sum0["EFFECT_2_aligned"], xerr=sum0["SE_1"],yerr=sum0["SE_2"],
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(sum0["EFFECT_1"],sum0["EFFECT_2_aligned"],label=label0,zorder=2,color="#cccccc",marker="^",**scatterargs)
        if len(sum1only)>0:
            ax.errorbar(sum1only["EFFECT_1"],sum1only["EFFECT_2_aligned"], xerr=sum1only["SE_1"],yerr=sum1only["SE_2"],
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(sum1only["EFFECT_1"],sum1only["EFFECT_2_aligned"],label=label1,zorder=2,color="#e6320e",marker="^",**scatterargs)

        if len(sum2only)>0:
            ax.errorbar(sum2only["EFFECT_1"],sum2only["EFFECT_2_aligned"], xerr=sum2only["SE_1"],yerr=sum2only["SE_2"],
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(sum2only["EFFECT_1"],sum2only["EFFECT_2_aligned"],label=label2,zorder=2,color="#41e620",marker="o",**scatterargs)

        if len(both)>0:
            ax.errorbar(both["EFFECT_1"],both["EFFECT_2_aligned"], xerr=both["SE_1"],yerr=both["SE_2"],
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(both["EFFECT_1"],both["EFFECT_2_aligned"],label=label3,zorder=2,color="#205be6",marker="s",**scatterargs)  
    else:
        ## if OR
        if len(sum0)>0:
            ax.errorbar(sum0["OR_1"],sum0["OR_2_aligned"], xerr=sum0[["OR_L_1","OR_H_1"]],yerr=sum0[["OR_L_2_aligned","OR_H_2_aligned"]],
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(sum0["OR_1"],sum0["OR_2_aligned"],label=label0,zorder=2,color="#cccccc",marker="^",**scatterargs)
        if len(sum1only)>0:
            ax.errorbar(sum1only["OR_1"],sum1only["OR_2_aligned"], xerr=sum1only[["OR_L_1","OR_H_1"]],yerr=sum1only[["OR_L_2_aligned","OR_H_2_aligned"]],
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(sum1only["OR_1"],sum1only["OR_2_aligned"],label=label1,zorder=2,color="#205be6",marker="^",**scatterargs)

        if len(sum2only)>0:
            ax.errorbar(sum2only["OR_1"],sum2only["OR_2_aligned"], xerr=sum2only[["OR_L_1","OR_H_1"]],yerr=sum2only[["OR_L_2_aligned","OR_H_2_aligned"]],
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(sum2only["OR_1"],sum2only["OR_2_aligned"],label=label2,zorder=2,color="#41e620",marker="o",**scatterargs)

        if len(both)>0:
            ax.errorbar(both["OR_1"],both["OR_2_aligned"], xerr=both[["OR_L_1","OR_H_1"]].values.T,yerr=both[["OR_L_2_aligned","OR_H_2_aligned"]].values.T,
                        linewidth=0,zorder=1,**errargs)
            ax.scatter(both["OR_1"],both["OR_2_aligned"],label=label3,zorder=2,color="#e6320e",marker="s",**scatterargs)
    
    ## annotation
    if anno==True:
        from adjustText import adjust_text
        sig_list_toanno = sig_list_merged.dropna(axis=0)
        texts=[]
        for index, row in sig_list_toanno.iterrows():
            if mode=="beta" or mode=="BETA" or mode=="Beta":
                texts.append(plt.text(row["EFFECT_1"], row["EFFECT_2_aligned"],index, ha='center', va='center')) 
            else:
                texts.append(plt.text(row["OR_1"], row["OR_2_aligned"],index, ha='center', va='center')) 
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='grey'))
    
    elif type(anno) is dict:
        # if input is a dict
        sig_list_toanno = sig_list_toanno.loc[sig_list_toanno.index.isin(list(anno.keys())),:]
        texts=[]
        for index, row in sig_list_toanno.iterrows():
            texts.append(plt.text(row["EFFECT_1"], row["EFFECT_2_aligned"],anno[index], ha='right', va='top')) 
        adjust_text(texts,ha='right', va='top',arrowprops=dict(arrowstyle='->', color='grey'))
        
    ax.set_xlabel("Per-allele effect size in "+label1,**fontargs)
    ax.set_ylabel("Per-allele effect size in "+label2,**fontargs)
    
    # plot x=0,y=0, and a 45 degree line
    xl,xh=ax.get_xlim()
    yl,yh=ax.get_ylim()
    
    if mode=="beta" or mode=="BETA" or mode=="Beta":
        #if using beta
        ax.axhline(y=0, zorder=1,**helper_line_args)
        ax.axvline(x=0, zorder=1,**helper_line_args)
    else:
        #if using OR
        ax.axhline(y=1, zorder=1,**helper_line_args)
        ax.axvline(x=1, zorder=1,**helper_line_args)
    
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
        
    if is_reg is True:
        if mode=="beta" or mode=="BETA" or mode=="Beta":
            reg = ss.linregress(sig_list_merged["EFFECT_1"],sig_list_merged["EFFECT_2_aligned"])
        else:
            reg = ss.linregress(sig_list_merged["OR_1"],sig_list_merged["OR_2_aligned"])
        
        #### calculate p values based on selected value , default = 0 
        t_score = (reg[0]-null_beta) / reg[4]
        degree = len(sig_list_merged.dropna())-2
        p = ss.t.sf(abs(t_score), df=degree)*2
        print("Beta_se = ", reg[4])
        print("H0 beta=",null_beta ,", p =", p)
        
        
        if reg[0] > 0:
            #if regression coeeficient >0 : auxiliary line slope = 1
            if is_45_helper_line is True:
                if mode=="beta" or mode=="BETA" or mode=="Beta": 
                    #if beta: auxiliary line pass (0,0)
                    ax.axline([min(xl,yl),min(xl,yl)], [max(xh, yh),max(xh, yh)],zorder=1,**helper_line_args)
                else:
                    #if OR: auxiliary line pass (1,1)
                    ax.axline([min(xl,yl)+1,min(xl,yl)+1], [max(xh, yh)+1,max(xh, yh)+1],zorder=1, **helper_line_args)
            ax.text(0.98,0.02,"$y =$ "+"{:.2f}".format(reg[1]) +" $+$ "+ "{:.2f}".format(reg[0])+" $x$, $p =$ "+ "{:.2e}".format(p)+ ", $r^{2} =$" +"{:.2f}".format(reg[2]),va="bottom",ha="right",transform=ax.transAxes,**fontargs)
        else:
            #if regression coeeficient <0 : auxiliary line slope = -1
            if is_45_helper_line is True:
                if mode=="beta" or mode=="BETA" or mode=="Beta": 
                    ax.axline([min(xl,yl),-min(xl,yl)], [max(xh, yh),-max(xh, yh)],zorder=1,**helper_line_args)
                else:
                    ax.axline([min(xl,yl)+1,-min(xl,yl)+1], [max(xh, yh)+1,-max(xh, yh)+1],zorder=1,**helper_line_args)
            ax.text(0.98,0.02,"$y =$ "+"{:.2f}".format(reg[1]) +" $-$ "+ "{:.2f}".format(abs(reg[0]))+" $x$, $p =$ "+"{:.2e}".format(p)+ ", $r^{2} =$" +"{:.2f}".format(reg[2]),va="bottom",ha="right",transform=ax.transAxes,**fontargs)
        
        if mode=="beta" or mode=="BETA" or mode=="Beta":
            middle = sig_list_merged["EFFECT_1"].mean()
        else:
            middle = sig_list_merged["OR_1"].mean()
        
        ax.axline(xy1=(0,reg[1]),slope=reg[0],color="#cccccc",linestyle='--',zorder=1)
    
    L = ax.legend(title=legend_title,loc=legend_pos)
    plt.setp(L.texts,**fontargs)
    plt.setp(L.get_title(),**fontargs)
    ##plot finished########################################################################################
    
    return [sig_list_merged, fig]