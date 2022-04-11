#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 13:41:28 2015

@author: Mohamed
"""

import commands
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from optparse import OptionParser
from subprocess import Popen, PIPE
import os


def message(information):
    seq="****************"
    for i in range(len(information)):
        seq=seq+"*"
    print ""
    print seq
    print "*       "+information+"       *"
    print seq
    print ""

def initMatrix(lis):
    m=[]
    l = ["-"]
    for f in lis : 
        l.append(f)
    for i in range(len(lis)+1) : 
            if i==0 :
                m.append(l)
            else :
                s=[]
                s.append(lis[i-1])
                for j in range(len(lis)) :
                  s.append("-")
                m.append(s)
    return m   

def dic_file(lis) :
    dic={}
    for i in range(len(lis)) : 
        dic[lis[i]]=i
    return dic

def read_file(inputFolder):
    files = commands.getoutput("ls "+inputFolder)
    list_folder = files.split("\n")
    list_files = []
    for fasta in list_folder :
        feature = fasta.split(".")
        if len(feature) > 1 and (feature[len(feature)-1]=="fasta" or feature[len(feature)-1]=="fna") :
            list_files.append(fasta)
    return list_files
    
def concatenate(fileName,outDir,inputFolder):
    Seq1 = ""
    for cur_record in SeqIO.parse(inputFolder+"/"+fileName, "fasta") :
        Seq1 = Seq1 + str(cur_record.seq)
    record = SeqRecord(Seq(Seq1),name=fileName.split(".")[0],id=fileName.split(".")[0],description="")
    SeqIO.write(record, outDir+"/"+fileName, "fasta")
    
        
def changeHeader(fileName,outDir,inputFolder) :
   out = open(outDir+"/"+fileName,"w")
   inputFile = open(inputFolder+"/"+fileName,"r")
   line = inputFile.readline()
   while line : 
       if ">" in line : 
           out.write(">"+fileName.split(".")[0]+"\n")
       else :
           out.write(line)
       line = inputFile.readline()
   out.close()
   inputFile.close()
       
       
       
def createNewDir(outDir,inputFolder) : 
    list_files = read_file(inputFolder)
    commands.getoutput("mkdir " + outDir)
    for fasta in list_files : 
        cmd = commands.getoutput("""grep ">" """+inputFolder+"/"+fasta+""" | wc -l """ )
        cmd = cmd.replace(" ","")
        cmd = int(cmd)
        if cmd == 1 :
            changeHeader(fasta,outDir,inputFolder)
        else : 
            concatenate(fasta,outDir,inputFolder)
            
def size_table(outDir) : 
    out = open(outDir+"/genome_size.txt","w")
    lis = read_file(outDir)
    dic = {}
    for fileName in lis :
        size = 0
        for cur_record in SeqIO.parse(outDir+"/"+fileName, "fasta") :
            size = size + len(cur_record)
        dic[fileName]=size
    for fileName in dic.keys() :
        genome = fileName.split(".")[0]
        out.write(genome + "\t"+ str(dic[fileName]) + "\n" )
    
def split_by_length(s,block_size):
    w=[]
    n=len(s)
    for i in range(0,n,block_size):
        w.append(s[i:i+block_size])
    return w
            
def createGolbalFiles(outDir):
    commands.getoutput("cat "+outDir+"/* > "+outDir+"/all.fasta")
    for cur_record in SeqIO.parse(outDir+"/all.fasta", "fasta") :
        seq = str(cur_record.seq)
        name = str(cur_record.name)
        split_seq=split_by_length(seq,1020)
        for i in range(len(split_seq)) : 
            record = SeqRecord(Seq(split_seq[i]),name="",id=name+"-"+str(i),description="")
            output_handle = open(outDir+"/all_split.fasta", "a")
            SeqIO.write(record, output_handle, "fasta")
            output_handle.close()
        
def makeBlastDB(pathToBlast,outDir):
    cmd =pathToBlast+"/makeblastdb -dbtype nucl -in "+outDir+"/all.fasta -out "+outDir+"/all.fasta"  
    print cmd    
    p = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True)
    output, errors = p.communicate()
    if p.returncode or errors:
        print errors
        exit()
    
  
def blast(pathToBlast,outDir,thread):
    cmd = pathToBlast+"/blastn -db "+outDir+"/all.fasta -query "+outDir+"/all_split.fasta -evalue 1e-5 -perc_identity 30 -outfmt 6 -out "+outDir+"/result.txt -num_threads "+str(thread)
    print cmd    
    p = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True)
    output, errors = p.communicate()
    if errors:
        print errors


def blastModification(outDir) :
    blast = open(outDir+"/result.txt","r")
    out = open(outDir+"/modified_result1","w")
    line = blast.readline()
    while line :
        column = line.split("\t")
        if abs(float(column[6])-float(column[7]))/1020 > 0.7:
            out.write(line)
        line = blast.readline()
    out.close()
    blast.close()
    cmd1 = "sort -k 2d " +outDir+"/modified_result1 > "+outDir+"/modified_result2"
    cmd2 = "sort -u -k 1,1 -k 2,2 " +outDir+"/modified_result2 > "+outDir+"/modified_result"
    print cmd1 
    p = Popen(cmd1, stderr=PIPE, stdout=PIPE, shell=True)
    output, errors = p.communicate()
    p = Popen(cmd2, stderr=PIPE, stdout=PIPE, shell=True)
    output, errors = p.communicate()



    
def dict_blast_ident(outDir):
    dic ={}
    blast = open(outDir+"/modified_result","r")
    line = blast.readline()
    while line : 
        column = line.split("\t")
        nameG = column[0].split("-")[0]+"***"+column[1].split("-")[0]
        if nameG not in dic.keys() :
            dic[nameG] = [float(column[2]),1]
        else :
            dic[nameG] = [dic[nameG][0]+float(column[2]),dic[nameG][1]+1]
        line = blast.readline()
    blast.close() 
    for key in dic.keys() : 
        dic[key][0] = dic[key][0]/dic[key][1]
    return dic

def dict_blast_size(outDir):
    dic ={}
    blast = open(outDir+"/modified_result","r")
    line = blast.readline()
    while line : 
        column = line.split("\t")
        nameG = column[0].split("-")[0]+"***"+column[1].split("-")[0]
        if nameG not in dic.keys() :
            dic[nameG] = abs(int(column[6])-int(column[7]))
        else :
            dic[nameG] = dic[nameG]+abs(int(column[6])-int(column[7]))
        line = blast.readline()
    blast.close() 
    return dic   
 
def createTab1(list_files,outDir) :
    tab = open(outDir+"/tab_ident.txt","w")
    lis=[]
    for fasta in list_files : 
        lis.append(fasta.split(".")[0])
    matrix = initMatrix(lis)
    dic = dic_file(lis)
    dic_blast = dict_blast_ident(outDir)
    for key in dic_blast.keys():
        genome = key.split("***")
        matrix[ dic[genome[0]]+1 ][ dic[genome[1]]+1 ] = round(dic_blast[key][0],3)
    for line in matrix :
        fline = ""        
        for word in line : 
            fline = fline + "\t" + str(word)
        fline = fline[1:]+"\n"
        tab.write(fline)
    tab.close()
        
def createTab2(list_files,outDir) :
    tab = open(outDir+"/tab_size.txt","w")
    lis=[]
    for fasta in list_files : 
        lis.append(fasta.split(".")[0])
    matrix = initMatrix(lis)
    dic = dic_file(lis)
    dic_blast = dict_blast_size(outDir)
    for key in dic_blast.keys():
        genome = key.split("***")
        matrix[ dic[genome[0]]+1 ][ dic[genome[1]]+1 ] = dic_blast[key]
    for line in matrix :
        fline = ""        
        for word in line : 
            fline = fline + "\t" + str(word)
        fline = fline[1:]+"\n"
        tab.write(fline)
    tab.close()   

def pipe(inputFolder,outDir,pathToBlast,thread) : 
    list_files=read_file(inputFolder)
    message("Creating the folder "+outDir)
    createNewDir(outDir,inputFolder)
    size_table(outDir)
    message("Concatenation of your fasta files")
    createGolbalFiles(outDir)
    message("Creation of the blast database")
    makeBlastDB(pathToBlast,outDir)
    message("Running blastn")
    blast(pathToBlast,outDir,thread)
    message("modifying blast result")
    blastModification(outDir)
    message("Creating your result files")
    createTab1(list_files,outDir)
    createTab2(list_files,outDir)

def main() :
    parser = OptionParser(usage="usage: ./%prog -i your_folder_containing_your_fasta_files -p path_where_you_ant_to_create_your_folder -o the_name_of_your_result_folder -b path_where_blast_is_installed [-t number of threads]",
                          version="%prog 1.0")
    parser.add_option("-i", "--input",
                      action="store",
                      dest="input",
                      default=False,
                      help="path to a folder containing fasta files")
    parser.add_option("-p", "--path",
                      action="store",
                      dest="path",
                      default=False,
                      help="path to the directory where the result folder will be created")
    parser.add_option("-o", "--output",
                      action="store",
                      dest="output",
                      default=False,
                      help="the name of the result folder")
    parser.add_option("-b", "--blast",
                      action="store",                      
                      dest="blast",
                      default=False,
                      help="Path were blast is installed (the binary folder")
    parser.add_option("-t", "--thread",
                      type="int",
                      dest="thread",
                      default=1,
                      help="Number of thread you want to use")
                      
    (options, args) = parser.parse_args()
    
    if options.input==False or  options.path==False or options.output==False or options.blast==False :
        parser.error("You didn't put all the required arguments.\n")
    
    if os.path.isdir(options.input) == False : 
        parser.error("Your input directory is not a folder.\n")
        
    if os.path.isdir(options.path) == False : 
        parser.error("The path chosen to create the result directory is not a folder.\n")
    
    outDir = options.path 
    if outDir[len(outDir)-1]=="/":
        outDir=outDir[:len(outDir)-1]
    outDir = outDir + "/"+options.output    
    
    if os.path.isdir(outDir) == True : 
        parser.error("The output folder already exists.\n") 
    
    outDir = options.path 
    if outDir[len(outDir)-1]=="/":
        outDir=outDir[:len(outDir)-1]
    outDir = outDir + "/"+options.output
    
    pathToBlast = options.blast 
    if pathToBlast[len(pathToBlast)-1]=="/":
        pathToBlast=pathToBlast[:len(pathToBlast)-1]
        
    print pathToBlast+"/blastn"
    print pathToBlast+"/makeblastdb"
    
    if os.path.isfile(pathToBlast+"/blastn")==False or os.path.isfile(pathToBlast+"/makeblastdb")==False :         
        parser.error("Blast not found.\n")   
        
    message("Welcome to ANI calculator ! ")
    pipe(options.input,outDir,pathToBlast,options.thread)
    message("All done")
    
main()
    
    
    
        
        