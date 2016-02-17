'''
Created on 2016-1-3

@author: Administator
'''
from __MC_ICC16_Alg1 import  MC_ICC16_Alg

class Run___MC_ICC16_Alg:
   def __init__(self,*args):
        self.arg = args[0]
	self.debugfile = open("Log_run_MC_ICC16_Alg1.txt",'w')  	
	self.debugfile.write("========= Run___MC_ICC16_Alg start :\n")
	self.debugfile.flush()

    	self.__mc_icc16_alg = MC_ICC16_Alg(self.arg)     
	self.debugfile.write("--------- Instance MC_ICC16_Alg has been completed.\n")
	self.debugfile.flush()
	self.debugfile.write("--------- Initilization of MC_ICC16_Alg is done :~\n")
	self.debugfile.flush()

    
   def get_pathSelected(self):
 	self.debugfile.write("=========== Request PathSet_selected :\n")
	self.debugfile.flush()

        retDict = self.__mc_icc16_alg.get_pathSelected();
	#self.debugfile.write("\t --Show the str_PathSet_selected: "+str(retDict)+"\n")
	#self.debugfile.flush()

 	self.debugfile.write("--------- PathSet_selected was requested :~\n")
	self.debugfile.flush()
        return retDict
    
   def get_pathSet(self):
 	self.debugfile.write("=========== Request PathSet :\n")
	self.debugfile.flush()

    	retDict = self.__mc_icc16_alg.get_pathSet();
	#self.debugfile.write("\t --Show the str_PathSet: "+str(retDict)+"\n")
	#self.debugfile.flush()

 	self.debugfile.write("--------- Paths_set was requested :~\n")
	self.debugfile.flush()
        return retDict

   def get_timeStamp(self):
 	self.debugfile.write("=========== Request TimeStamp :\n")
	self.debugfile.flush()

        TimeStamp = self.__mc_icc16_alg.get_timeStamp();
	self.debugfile.write("\t --Show the str_TimeStamp: "+str(TimeStamp)+"\n")
	self.debugfile.flush()
 	self.debugfile.write("--------- TimeStamp was requested :~\n")
	self.debugfile.flush()
        return TimeStamp
