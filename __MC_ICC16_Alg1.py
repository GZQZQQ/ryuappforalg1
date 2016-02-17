#coding=utf-8
##### 2015-09-13: Implement the Markov-Chain based approximated algorithm to solve MBSR problem.
##### 2016-01-20: Implement the thread-controlling alg1.(Huawei)
import random
import math
import time
import thread

class MC_ICC16_Alg:
    def __init__(self,*args):
        self.objNetworkMonitor = args[0]
    	### ==================== Given the Inputting paths between each Ctrler and SW-node.
        self.PathData_file = '_PathSet.txt';            # global file-var
        self.Traffic_file = '_TrafficDemands.txt';    # global file-var
        self.Cap_links_file = '_Cap_links.txt';            # global file-var
        self.Cap_MBoxes_file = '_Cap_MBoxes.txt';            # global file-var

        #self.f1 = open("mcicc16_dugflie.txt",'w')
 	
        #self.f1.write("get arg ok \n") 
        #self.f1.write("why show \n")    
        self.PathSet_cand = {}        ## {(Src,Dst):[path1_id, path2_id,...,path_|Js|_id]}, the candidate path-set for all pairs.
        #self.f1.write("21 \n")
        #self.f1.flush() 
        self.TDSet = {}                ## {(Src):Rate}, the Traffic-Demand set of all Client-Flow.
        self.Cap_MBoxes = {}            ## {MBox_id:CapVal}, the Capacity Middle-Boxes in Topology.
        #self.f1.write("31 \n")
        #self.f1.flush() 
        self.Cap_links = {}            ## {(u,v):CapVal}, the Capacity set of all links in Topology.
        #self.f1.write("41 \n")
        #self.f1.flush() 
        self.Nodes_set = [];            ## Record all nodes in topology graph.
        self.Edges_set = {};            ## {Edge_id:(u1,v1)}, Record all edges in topology.
        self.Paths_set = {};            ## { Path_id: [path_content:(path_src,next_node,...,path_dst)] }, Record all given paths in topology graph. 
        #self.f1.write("51 \n")
        #self.f1.flush()  
        self.list_MBoxDst_id  = [];        ## Middlebox-Connected-Switches. [10, 21, 33, 50]
        self.list_CFlowSrc_id = [];        ## Client-Flow-Src-switches.
 	
	##==============================================================
        self.PathSet_selected = {}    ## {(Src_CFlow,Dst_MBox):[path1_id,path2_id,...,[path_|Ds|]_id]}, the In-Use path for all CFs.
        self.MBoxSet_assigned = {}    ## {(MBox_id):[CFlow1_id,CFlow2_id,...]}, the holding ClientFlows of each MiddleBox.
        self.Timers = {}     ## {(Src):[ts_begin, timer_len, pathID_old, pathID_new, DstMBox_current,  DstMBox_new]}, the timer-set for each (Src)-CFlow. 
	##==============================================================

        self.LogRun = open('Log_Alg1_running.txt','w')
        #self.Log_final_result = open('Log_Alg1_final_throughput.tr','w');
        self.Log_debug = open('Log_Alg1_debug_1.txt','w');  
    
	self.TS_print = 0;## Time-stamp to be shown in log-files.
	##========================== !!! Critical Parameters Setting: ====================================   
	running_time_in_total = 120;	## 1200 seconds, this time can be changed.
	step_to_check_timer_expiration = 0.01;## unit of time is second.
	stepCount_to_print_throughput = 100;## unit: 10 steps of one-timer_checking.

	self.Style_of_throughput_by_simulation_or_Mininet = 1	## 1 indicates simulation; 0 represents mininet.

	thread.start_new_thread(self.Keep_running_alg1, (running_time_in_total,
				step_to_check_timer_expiration, stepCount_to_print_throughput))
	##========================== !!! Critical Parameters Setting:##End of __init__():~

###############################################################
    def get_pathSelected(self):
        return self.PathSet_selected;
    def get_pathSet(self):
        return self.Paths_set;
    def get_timeStamp(self):
	ts_cur = self.TS_print;
        return ts_cur;
#########################################################################################################################################
    def Keep_running_alg1(self, Total_running_time, Step_to_check_timer, StepCount_to_print_throughput ):   
        self.T = Total_running_time;    ## Alg-parameter: Set The total running period of alg1 as 1200 seconds. (This time can be changed.)
        self.STEP_TO_CHECK_TIMER = Step_to_check_timer;    ## Alg-parameter: The step (length of interval) of check timer-expiration.
        self.Ds = 1;         ## Alg-parameter: Must be larger than 1 and smaller than |Js|.
        self.Beta = 5;    	 ## Alg-parameter: The parameter in the theoretical derivation.
        self.Tau = 0;        ## Alg-parameter: The alpha regarding the Markov_Chain.

        self.Log = open('Log_Alg1_Cost_STEP'+str(self.STEP_TO_CHECK_TIMER)+'.tr','w');
	# ===================================== Begin to run =========================================    
       
    	## --- A. Read trace.
        self.FuncReadTrace(self.PathData_file, self.Traffic_file, self.Cap_links_file, self.Cap_MBoxes_file);

	## --- B.1 Stage 0: Initialization.
        self.Initialization();
    
        _timeStamp_Begin_to_run = time.time();	## Return the current-timeStamp, unit-time is second.
        self.LogRun.write(  '_timeStamp_Begin_to_run: %f \n'%(_timeStamp_Begin_to_run) )
        self.LogRun.flush()

	### --- B.2 Stage 1: Initialize self.Timers for all pairs.
        self.Set_timer_for_all_CFlows( _timeStamp_Begin_to_run );
    
	## --- C. Enter into time-slot Count-Down process.
        current_ts = _timeStamp_Begin_to_run;	### Initialize the current_ts.
        step_times = 0;
        last_ts_to_check_timer = _timeStamp_Begin_to_run;
        Cumulative_Notification_times = 0;
        Cumulative_TimerCountDown_times = 0;
        self.Call_and_record_system_performance(current_ts,step_times,
						Cumulative_Notification_times,
						Cumulative_TimerCountDown_times);

        _timeStamp_alg_should_terminate = _timeStamp_Begin_to_run + self.T;
        while ( current_ts <= _timeStamp_alg_should_terminate ):
            RESET_Msg = 0;

            ##### -- C.1 listen to the event of any timer's expiration.
            Length_to_check_timers_experiation = self.STEP_TO_CHECK_TIMER;
            if ((current_ts - last_ts_to_check_timer) >= Length_to_check_timers_experiation ):
                ### --- C.1.0 Update the timer-checking time-slot.
                last_ts_to_check_timer = current_ts;
			
                ### --- C.1.1 Check self.Timers, if any timer is out, swap its relavant SrcCFlow's hostMBox and path.
                ret_timer_check_result = self.Check_expiration_of_timers(current_ts);
                if len(ret_timer_check_result)>0:
			RESET_Msg = 1;
			for key,val in ret_timer_check_result.items():
				### ---- C.1.1.1 Read the MBox-CFlow holding information.
				Src_CFlow = key;
				pathID_old = val[0];## Get the returned pathID_old.
				pathID_new = val[1];## Get the returned pathID_new.
				Dst_MBox_cur = val[2];## Get the returned Dst_MBox_cur.
				Dst_MBox_new = val[3];## Get the returned Dst_MBox_new.
				### ---- And replace the old routing-path with the new selected routing-path for a Src_ClientFlow.
				self.Replace_the_selected_DstMBox_and_Path_for_a_SrcCFlow( Src_CFlow, Dst_MBox_cur, Dst_MBox_new,
										pathID_old, pathID_new );
			
				## --- C.1.1.2  !!!! Clear-the-timeouted-timer-items.
				self.Delete_expired_timer_items_after_replacement(Src_CFlow);
			
				### --- C.1.1.3 !!! Record the timer's time-out times.
				Cumulative_TimerCountDown_times += 1;
		
            ##### -- C.2 listen to the event of any Controller's RESET Msg.
            if 1==RESET_Msg:
            	#self.LogRun.write(  '\n  ================= RESET all self.Timers at ts [ %s ] :\n'%(current_ts) )
            	#self.LogRun.flush()

                self.RESET(current_ts);

                #self.LogRun.write(  '\n  ================= End of RESET all self.Timers at ts [ %s ] :~\n'%(current_ts) )
                #self.LogRun.flush()
                ## !!! Record the times of RESET-Event(In each RESET-Event, a notification-event need to do).
                Cumulative_Notification_times += 1;
		
            ##### -- C.4 time flies, increase time-slot
            ###current_ts += self.STEP_TO_RUN;## Simulation-style.
            time.sleep( self.STEP_TO_CHECK_TIMER );
            current_ts = time.time();### Update the current_ts with now-time. This is the real-time-experiment style.
            step_times +=1;
        
            ##### -- C.5 record performance of system periodically.
            if ( 0 == step_times%StepCount_to_print_throughput ):
                Throughput = self.Get_objVal_of_configurations_in_whole_system();
                self.TS_print = current_ts - _timeStamp_Begin_to_run;
                self.LogRun.write('-TimeStamp\t%f\t-Throughput\t%s\n'%(self.TS_print, Throughput));
                self.LogRun.flush()
            if ( 0 == step_times%StepCount_to_print_throughput ):
                self.Call_and_record_system_performance(self.TS_print,step_times,Cumulative_Notification_times,Cumulative_TimerCountDown_times);
	## ====== while :~
	self.Write_down_the_current_solution_MBox_Path_assignment(self.TS_print);
	self.Record_final_result(self.TS_print,step_times,Cumulative_Notification_times,Cumulative_TimerCountDown_times);
	self.Log.close();
	self.LogRun.close();
	#self.Log_final_result.close();
	self.Log_debug.close();
	##  ==== Finally, terminate this thread.
	thread.exit_thread()### End of this function :~


#########################################################################################################################################

    # ==========================================================================================
    def FuncReadTrace(self,CandPaths_file,TrafficDemand_file,CapLinks_file,CapMBoxes_file):
        # ---- 1 Read the Given path data :
        #global self.PathSet_cand;
        Global_path_id_idx = 0;        ### The path_id is labelled from 0.
        with open(CandPaths_file,'r') as f:
            for lines in f:
                line=lines.strip('\n')
                lineContent = line.split('\t')
                Dst_id = str(lineContent[1]);
                Src_id = str(lineContent[3]);
                path = str(lineContent[7]);
                One_path = [];
                pathContent = path.split(">")
                for i in range(len(pathContent)-1,-1,-1):## Reverse the content of this path.
                    One_path.append(str(pathContent[i]));
                #############################
                path_id = Global_path_id_idx;
                Global_path_id_idx += 1;
                ## -- 1.1 record this path into the self.Paths_set.
                if path_id not in self.Paths_set.keys():
                    self.Paths_set[path_id] = One_path;
                    
                ## -- 1.2 record this path into the self.PathSet_cand.
                if (Src_id,Dst_id) not in self.PathSet_cand.keys():
                    self.PathSet_cand[(Src_id,Dst_id)] = [];
                    self.PathSet_cand[(Src_id,Dst_id)].append(path_id);
                else:
                    self.PathSet_cand[(Src_id,Dst_id)].append(path_id);
        ### ---- 1 Read the Given path data :~
        
        # ---- 2 Read the Given self.TDSet data :
        #global self.TDSet, self.list_CFlowSrc_id;
        with open(TrafficDemand_file,'r') as f:
            for lines in f:
                line=lines.strip('\n')
                lineContent = line.split("\t")
                Src_id = str(lineContent[3]);
                Rate = str(lineContent[5]);
                ## --- record TD.
                if Src_id not in self.TDSet.keys():
                    self.TDSet[Src_id] = float(Rate);
                if Src_id not in self.list_CFlowSrc_id:
                    self.list_CFlowSrc_id.append(Src_id);
        ### ---- 2 Read the Given self.TDSet data :~
        
        # ---- 3 Read the Capacity of links and all nodes and all edges:
        #global self.Cap_links, self.Nodes_set, self.Edges_set;
        Global_edge_Idx = 0;    ## From 0 to label the id of an edge.
        with open(CapLinks_file,'r') as f:
            for lines in f:
                line=lines.strip('\n')
                lineContent = line.split("\t")
                u_id = str(lineContent[1]);
                v_id = str(lineContent[3]);
                CapVal = float(lineContent[5]);
                if (u_id,v_id) not in self.Cap_links.keys():
                    self.Cap_links[(u_id,v_id)] = CapVal;
                if (v_id,u_id) not in self.Cap_links.keys():
                    self.Cap_links[(v_id,u_id)] = CapVal;
                ## --- record the nodes from topology.
                if u_id not in self.Nodes_set:
                    self.Nodes_set.append(u_id);
                if v_id not in self.Nodes_set:
                    self.Nodes_set.append(v_id);
                ## --- record the edges from topology.
                edge_id = Global_edge_Idx;
                Global_edge_Idx += 1;
                if edge_id not in self.Edges_set.keys():
                    self.Edges_set[edge_id] = (u_id,v_id);
                else:
                    self.Edges_set[edge_id] = (u_id,v_id)### ---- 3 Read the Capacity of links:~    
            
        # ---- 4 Read the Capacity of Middle-Boxes:
        #global self.Cap_MBoxes;
        with open(CapMBoxes_file,'r') as f:
            for lines in f:
                line=lines.strip('\n')
                lineContent = line.split("\t")
                MBox_id = str(lineContent[1]);
                CapVal = float(lineContent[3]);
                ## --- 4.1 record Middlebox-Connected-Switches and Client-Flow-Src-switches.
                if MBox_id not in self.list_MBoxDst_id:
                    self.list_MBoxDst_id.append(MBox_id);
                ## --- 4.2 record the capacity of MBoxes.
                if MBox_id not in self.Cap_MBoxes.keys():
                    self.Cap_MBoxes[MBox_id] = CapVal# ---- 4 Read the Capacity of Middle-Boxes :~ ## --- End of this function :~
    # ==========================================================================================   
    def Initialization(self):
        ### ===== 1. Select target assigned MBox for each CFlow i.
        #self.Log_debug.write( "======= In Initialization, self.TDSet "+str(self.TDSet)+"\n" )
	#self.Log_debug.flush()
	#self.f1.write("91 \n")
        for id_CF in self.TDSet.keys():
            ## ===== 1.1 Rdmly select a target MBox j, then predict whether it is feasible.
            CNT_Mbox = len(self.list_MBoxDst_id);
            idx_MboxID_rdmlySelected = random.randint(0,CNT_Mbox-1);
            MboxID_rdmlySelected = self.list_MBoxDst_id[idx_MboxID_rdmlySelected];
            ## ===== 1.2 Check whether it is feasible to hold CFlow i.
	    #self.f1.write("92 \n")
            bool_whether_tarMBox_feasible = self.Check_whether_tarMBox_feasible_to_a_CFlow(id_CF, MboxID_rdmlySelected);
            #self.Log_debug.write( "\t bool_whether_tarMBox_feasible "+str(bool_whether_tarMBox_feasible)+"\n" )
            #self.Log_debug.flush()
	    #self.f1.write("93 \n")
            if (1==bool_whether_tarMBox_feasible):
                ### ---- 1.2.1 Update the MBox-CFlow holding information.
                self.MBox_trys_to_host_a_CFlow( MboxID_rdmlySelected, id_CF );
            	#self.f1.write("94\n")
                ### ===== 1.2.2 Randomly Select a path for CFlow i and its designated MBox j.
                #self.Log_debug.write( "\t self.PathSet_cand " +str(self.PathSet_cand)+" ============ End of checking Pathset_cand.\n" )
                #self.Log_debug.flush()

                for key,val in self.PathSet_cand.items():
                    Src = key[0];
                    Dst = key[1];
		    #self.f1.write("95 \n")
                    if (Src==id_CF and Dst==MboxID_rdmlySelected):
                        CNT_paths_cand = len(val);
                        ## -- 1.2.2.1. randomly select unique Ds(==1) paths for each pair (Src,Dst).
                        list_path_idxs = random.sample(xrange(0, CNT_paths_cand), self.Ds);
                        list_pathIDs_selected = [];
			#self.f1.write("96\n")
                        for idx in list_path_idxs:
                            idx_found = self.PathSet_cand[key][idx]
                            
                            #self.Log_debug.write("\t----idx_found "+str(idx_found)+"\n" )
                            #self.Log_debug.write("\t----list_path_idxs"+str(list_path_idxs)+"\n" )
                            
                            list_pathIDs_selected.append( idx_found );
                            
                        #self.f1.write("97 \n")    
                        ## -- 1.2.2.2. initialize the self.PathSet_selected by the selected Ds paths.
                        Path_ID_newly_adopted = -1;
                        #self.Log_debug.write("\t----list_path_idxs"+str(list_path_idxs)+"\n" )
                        #self.Log_debug.write("list_pathIDs_selected"+" "+str(list_pathIDs_selected)+"\n")

                        for path_id in list_pathIDs_selected: 
                            #self.f1.write("98 \n")
                            #self.Log_debug.write( Src+" -------> "+Dst+"\n")                  
                            if (Src,Dst) not in self.PathSet_selected.keys():
                                self.PathSet_selected[(Src,Dst)] = [];
                            #self.Log_debug.write("Path_ID_newly_adopted "+str(Path_ID_newly_adopted)+"\n" )
                            #self.Log_debug.write("path_id "+str(path_id)+"\n")
                            Path_ID_newly_adopted = path_id;

                            ### ---- !!! Before adopting this new path, judge whether it is feasible to this (s,d).
                            #### ----!! Before using the new-path, check whether it is still feasible to this Src_CFlow.
                            #self.Log_debug.write("Path_ID_newly_adopted " + str(Path_ID_newly_adopted)+"\n")
			    #self.f1.write("99 \n")
                            bool_whether_this_new_path_is_feasible = self.Check_whether_this_new_path_is_feasible_to_the_SrcCFlow(Src,Dst,Path_ID_newly_adopted);

			    #self.f1.write("100 \n")
                            #self.Log_debug.write( "\t====!!! bool_whether_this_new_path_is_feasible"+" "+str(bool_whether_this_new_path_is_feasible)+"\n" ) 
                                                
                            #print  self.PathSet_selected[(Src,Dst)]
                            #print  "\n"
                            #print "Path_ID_newly_adopted not in self.PathSet_selected[(Src,Dst)]:"
                            #print Path_ID_newly_adopted not in self.PathSet_selected[(Src,Dst)]
                            #print "\n"
                            if (1==bool_whether_this_new_path_is_feasible) and (Path_ID_newly_adopted not in self.PathSet_selected[(Src,Dst)]):
                                self.PathSet_selected[(Src,Dst)].append(Path_ID_newly_adopted)## --- End of this function :~	
	#self.LogRun.write("\t------- In the END of Initialization: PathSet_selected  "+ str(self.PathSet_selected)+"\n")
	#self.LogRun.flush()
    # ================================================ 
    def MBox_trys_to_host_a_CFlow(self, Mbox_ID, CFlow_ID ):
        #global self.Cap_MBoxes;
        
        ### ---- 0.0 Check Mbox_ID is regular.
        if -1==Mbox_ID:
            return
    
        ### ---- 0.1 Check feasible of MBox.
        second_check_feasible = self.Check_whether_tarMBox_feasible_to_a_CFlow(CFlow_ID, Mbox_ID);
        if (0==second_check_feasible):
            return
            
        ### ---- 1. Check Mbox_ID is regular.
        if Mbox_ID >= 0:
            if Mbox_ID not in self.MBoxSet_assigned.keys():
                self.MBoxSet_assigned[Mbox_ID] = [];
                
            ### ---- 1.1 Bind the host-MBox and CFlow.
            if CFlow_ID not in self.MBoxSet_assigned[Mbox_ID]:
                self.MBoxSet_assigned[Mbox_ID].append( CFlow_ID );
                pass##self.LogRun.write(  '\t\t-- Bind -- CFlow_ID[ %d ] <--> Mbox_ID[ %d ] \n'%(CFlow_ID, Mbox_ID) )
                pass##self.LogRun.write(  '\t\t  -- after Bind -- self.MBoxSet_assigned[ %d ]: %s \n'%(Mbox_ID, self.MBoxSet_assigned[Mbox_ID]) )
    
                ### ---- 1.1.1 Update the resouces information of host-MBox.
                current_Cap_MBox = self.Cap_MBoxes[Mbox_ID];
                consumed_Cap_by_CFlow = float(self.TDSet[CFlow_ID]);
                self.Cap_MBoxes[Mbox_ID] = current_Cap_MBox - consumed_Cap_by_CFlow;
                if self.Cap_MBoxes[Mbox_ID] < 0:
                    pass##self.LogRun.write( '\t\t==== WARN ==== self.Cap_MBoxes[ %d ] : %f\n'%(Mbox_ID, self.Cap_MBoxes[Mbox_ID]) )## --- End of this function :~
    # ================================================ 
    def MBox_removes_a_CFlow( self,Mbox_ID, CFlow_ID ):
        #global self.Cap_MBoxes;
        if Mbox_ID in self.MBoxSet_assigned.keys():
            ### ---- 1. Dis-Bind the host-MBox and CFlow.
            if CFlow_ID in self.MBoxSet_assigned[Mbox_ID]:
                self.MBoxSet_assigned[Mbox_ID].remove( CFlow_ID );
                pass##self.LogRun.write(  '\t\t~~ UnBind ~~ CFlow_ID[ %d ] --X-- Mbox_ID[ %d ] \n'%(CFlow_ID, Mbox_ID) )
                pass##self.LogRun.write(  '\t\t  ~~ after UnBind ~~ self.MBoxSet_assigned[ %d ]: %s \n'%(Mbox_ID, self.MBoxSet_assigned[Mbox_ID]) )
    
            ### ---- 2. Update the resouces information of host-MBox.
            current_Cap_MBox = self.Cap_MBoxes[Mbox_ID];
            consumed_Cap_by_CFlow = float(self.TDSet[CFlow_ID]);
            self.Cap_MBoxes[Mbox_ID] = current_Cap_MBox + consumed_Cap_by_CFlow## --- End of this function :~    
    # ================================================
    
    def Check_whether_tarMBox_feasible_to_a_CFlow(self,id_CFlow, id_tarMBox):
        #global self.Cap_MBoxes;
        ret_Status_feasible = 0## initialized to 0(false)
        TD_CFlow = float(self.TDSet[id_CFlow]);
        availabl_Cap_tarMBox = self.Cap_MBoxes[id_tarMBox];
        if (availabl_Cap_tarMBox > 0) and (availabl_Cap_tarMBox - TD_CFlow >= 0):
            ret_Status_feasible = 1##(1 represents true)
        return int(ret_Status_feasible)## --- End of this function :~
    # ================================================
    
    def Select_a_rdm_feasible_NIU_MBox_for_the_targetCFlow(self,Src_CFlow_ID):
        ret_MBoxID_NIU = -1;    ## If cannot find one, return a -1, which will incur a definite error.
        
        ## -- 1. get the list_NIU_MBoxes corresponding to this Src_CFlow.
        list_MBoxes_NIU = self.Get_list_of_NIU_MBoxes_corresponding_to_the_Src(Src_CFlow_ID);
        
        ## -- 2. rdmly pick up one from the list, until it is a feasible one.
        list_MBoxes_NIU_checked = [];
        while ( len(list_MBoxes_NIU_checked) < len(list_MBoxes_NIU) ):
            CNT_MBoxes_NIU = len(list_MBoxes_NIU);
            if CNT_MBoxes_NIU == 0:
                return -1### Not found even one MB_NIU.
            if CNT_MBoxes_NIU >= 1:
                idx_targetMBox = random.randint(0,CNT_MBoxes_NIU-1);
                rdm_MBoxID_NIU = list_MBoxes_NIU[idx_targetMBox];
                if ( rdm_MBoxID_NIU not in list_MBoxes_NIU_checked ):
                    bool_whether_tarMBox_feasible = self.Check_whether_tarMBox_feasible_to_a_CFlow(Src_CFlow_ID, rdm_MBoxID_NIU);
                    if (1==bool_whether_tarMBox_feasible):
                        ret_MBoxID_NIU = rdm_MBoxID_NIU
                        return ret_MBoxID_NIU### Return it directly.
                    else:### Not feasible
                        list_MBoxes_NIU_checked.append(rdm_MBoxID_NIU)### End of while :~
    
        # if (-1==ret_MBoxID_NIU):
            # print list_MBoxes_NIU_checked
            # print list_MBoxes_NIU
            
        return ret_MBoxID_NIU## --- End of this function :~
    # ================================================
    def Select_a_rdm_NIU_MBox_for_the_targetCFlow(self,Src_CFlow_ID):
        ret_MBoxID_NIU = -1;    ## If cannot find one, return a -1, which will incur a definite error.
        ## -- 1. get the list_NIU_MBoxes corresponding to this Src_CFlow.
        list_MBoxes_NIU = self.Get_list_of_NIU_MBoxes_corresponding_to_the_Src(Src_CFlow_ID);
        ## -- 2. pick up one rdmly from the list.
        CNT_MBoxes_NIU = len(list_MBoxes_NIU);
        if CNT_MBoxes_NIU >= 1:
            idx_targetMBox = random.randint(0,CNT_MBoxes_NIU-1);
            ret_MBoxID_NIU = list_MBoxes_NIU[idx_targetMBox];
        return ret_MBoxID_NIU## --- End of this function :~
        
    # ================================================
    def Get_list_of_NIU_MBoxes_corresponding_to_the_Src(self,Src_CFlow_ID):
        ## -- 1. get the holding MBox_ID corresponding to this Src_CFlow.
        Host_MBoxID_of_the_Src = self.find_holding_MBox_of_a_SrcCFlow(Src_CFlow_ID);
        ## -- 2. filter all the MBoxes.
        list_MBox_not_in_use = [MBox for MBox in self.list_MBoxDst_id if MBox != Host_MBoxID_of_the_Src ];
        return list_MBox_not_in_use## --- End of this function :~
    # ================================================
    def find_holding_MBox_of_a_SrcCFlow(self,Src_CFlow_ID):
        ret_holding_MB_id = -1;
        for key,val in self.MBoxSet_assigned.items():
            list_binded_SrcCF_IDs = val;
            if Src_CFlow_ID in list_binded_SrcCF_IDs:
                ret_holding_MB_id = key
        return ret_holding_MB_id## -- End of this function :~
    # ================================================
    def find_currently_selected_pathID_of_a_SrcCFlow(self,Src_CFlow_ID):
        ret_cur_selected_pathID_id = -1;
        #global self.PathSet_selected
        for key,val in self.PathSet_selected.items():
            if Src_CFlow_ID==key[0]:
                list_assigned_path_IDs = val;
                if len(list_assigned_path_IDs)>0:
                    ret_cur_selected_pathID_id = list_assigned_path_IDs[0];#### !!!! HERE: just take the first path.
        return ret_cur_selected_pathID_id## -- End of this function :~
    # ================================================
    
    def Get_the_current_selected_MBoxID_and_PathID_of_SrcCFlow(self,Src):
        retMBoxID = self.find_holding_MBox_of_a_SrcCFlow(Src);
        retPathID = self.find_currently_selected_pathID_of_a_SrcCFlow(Src);
        return retMBoxID,retPathID## -- End of this function :~
    # ================================================
    
    # ================================================
    def Get_max_value_of_a_dict(self, dict ):
        dictTemp={v:k for k,v in dict.items()}
        return dict[ dictTemp[max(dictTemp)] ]
    # ================================================
    def Get_min_value_of_a_dict(self, dict ):
        dictTemp={v:k for k,v in dict.items()}
        return dict[ dictTemp[min(dictTemp)] ]
    # ================================================
    
    # ==========================================================================================
    def get_size_of_Js(self, Src, Dst ):## { Get the Number_of_candidate_paths_for_this_pair(Src,Dst)}, the info of self.PathSet_cand.
        retNum_Paths_of_this_session = 0;
        for key,val in self.PathSet_cand.items():
            Src0 = key[0];
            Dst0 = key[1];
            if Src0==Src and Dst0==Dst:
                retNum_Paths_of_this_session = len(val);
        return retNum_Paths_of_this_session## --- End of this function :~
    # ==========================================================================================
    def get_size_of_Ds(self, Src, Dst ):## { Get the Number_of_In-Use_paths_for_this_pair(Src,Dst)}, the info of self.PathSet_selected.
        retNum_Paths_of_this_session = 0;
        #global self.PathSet_selected
        for key,val in self.PathSet_selected.items():
            Src0 = key[0];
            Dst0 = key[1];
            if Src0==Src and Dst0==Dst:
                retNum_Paths_of_this_session = len(val);
        return retNum_Paths_of_this_session## --- End of this function :~
    # ==========================================================================================
    def Check_expiration_of_timers(self, Current_ts ):## Returned value: 1: timer expires; 0: not.
        #global self.Timers;
        ret_timer_result = {}    ## {(SrcCFlow):[pathID_old, pathID_new, Dst_MBox_old, Dst_MBox_new]}
        # check each timer
        for Src,val in self.Timers.items():
            Ts_begin = val[0];
            Len_timer = val[1];
            pathID_old = val[2];
            pathID_new = val[3];
            Dst_MBox_old = val[4];
            Dst_MBox_new = val[5];
            if ( Current_ts >= Ts_begin+Len_timer ):
                if Src not in ret_timer_result.keys():
                    pass##self.LogRun.write( '\n======&&====== TimerOut: Src[ %d ] Ts_begin[ %s ] Len_timer[ %s ] DstMBox_old[ %s ] DstMBox_new[ %s ].'%(Src, Ts_begin, Len_timer, Dst_MBox_old, Dst_MBox_new) )
                    ret_timer_result[Src]=[-1,-1,-1,-1];
                    ret_timer_result[Src][0] = pathID_old;
                    ret_timer_result[Src][1] = pathID_new;
                    ret_timer_result[Src][2] = Dst_MBox_old;
                    ret_timer_result[Src][3] = Dst_MBox_new;
        return ret_timer_result## --- End of this function :~
    # ==========================================================================================
    def Get_a_rdm_pathID_NIU_from_CandidatePathSet(self,Src, Dst):    ## NIU: Not-In-Use.
        ret_pathID_NIU = 0;
        list_paths_NIU = self.Get_list_of_pathIDs_not_in_use(Src, Dst);
        CNT_paths_NIU = len(list_paths_NIU);
        if CNT_paths_NIU >= 1:
            idx_targetNewPath = random.randint(0,CNT_paths_NIU-1);
            ret_pathID_NIU = list_paths_NIU[idx_targetNewPath];
        return ret_pathID_NIU## --- End of this function :~
    def Get_list_of_pathIDs_not_in_use(self,Src, Dst):    ## pair of (Src, Dst).
        #global self.PathSet_cand, self.PathSet_selected;
        list_paths_not_in_use = [];
        listPaths_cand = self.PathSet_cand[(Src,Dst)];
        list_paths_in_use = [];
        if (Src,Dst) in self.PathSet_selected.keys():#### !!!! Check whether this s-d exists in the Path_assigned.
            list_paths_in_use = self.PathSet_selected[(Src,Dst)];
        for path_cand in listPaths_cand:
            if path_cand not in list_paths_in_use:
                list_paths_not_in_use.append( path_cand );
        return list_paths_not_in_use## --- End of this function :~
    def Get_a_rdm_pathID_IU_from_SeletedPathSet(self,Src, Dst):    ## IU: In-Use.
        #global self.PathSet_selected;
        ret_pathID_IU = 0;
        CNT_paths_of_this_pair = len(self.PathSet_selected[(Src,Dst)]);
        if CNT_paths_of_this_pair >= 1:
            idx_Path_IU = random.randint(0,CNT_paths_of_this_pair-1);
            ret_pathID_IU = self.PathSet_selected[(Src,Dst)][idx_Path_IU];
        return ret_pathID_IU## --- End of this function :~
    def Get_num_of_IU_paths_of_a_session(self,Src, Dst):    ## IU: In-Use.
        #global self.PathSet_selected;
        ret_num_IU = 0;
        ret_num_IU = len(self.PathSet_selected[(Src,Dst)]);
        return ret_num_IU## --- End of this function :~
    # ==========================================================================================
    def Get_objVal_of_configurations_in_whole_system(self):
        #global self.PathSet_selected;
        ret_system_throughput = 0
        dict_all_satisfied_CF = {}
        for SrcCF,DstMB in self.PathSet_selected.keys():
            if (len(self.PathSet_selected[(SrcCF,DstMB)])==1) and (SrcCF not in dict_all_satisfied_CF.keys()):
                dict_all_satisfied_CF[SrcCF] = 1##(1 is not important)
        for key in dict_all_satisfied_CF.keys():
            ret_system_throughput += self.TDSet[key]    
        return ret_system_throughput## --- End of this function :~
    # ==========================================================================================
    def Get_largest_utility_of_both_links_and_nodes(self):
        #global self.PathSet_selected;
        #### ------ 0. Define necessary dicts.
        dict_LinkLoad = {};    ## {(u,v):loadVal}, a dict which records the sum-traffic-load in each arc.
        for (u,v) in self.Cap_links.keys():
            if (u,v) not in dict_LinkLoad.keys():
                dict_LinkLoad[(u,v)] = 0.0;### -- !!! Initialization, otherwise, the total-link-cost will be smaller.
        dict_NodeLoad = {};    ## {(u):loadVal}, a dict which records the sum-num-rules-load in each node.
        for u in self.Nodes_set:
            if u not in dict_NodeLoad.keys():
                dict_NodeLoad[u] = 0;### -- !!! Initialization is necessary.
                
        ## -- 1. Analyse each selected-path in val, get and record all arc-links and nodes in this path.
        
        for key,val in self.PathSet_selected.items():
            for idx_pathID in range(0, len(val)):
                path_id = val[idx_pathID];
                listPath_i = self.Paths_set[path_id];
                for node_idx in range(len(listPath_i)):
                    if (node_idx+1) < len(listPath_i):
                        u = listPath_i[node_idx];
                        v = listPath_i[node_idx+1];
                        ## -- 1.1 record links travelled.
                        if (u,v) not in dict_LinkLoad.keys():
                            dict_LinkLoad[(u,v)] = self.TDSet[key[0]];
                        else:
                            dict_LinkLoad[(u,v)] += self.TDSet[key[0]];
                        ## -- 1.2 record all the nodes in the links travelled.
                        if u not in dict_NodeLoad.keys():
                            dict_NodeLoad[u] = 0;
                        else:
                            dict_NodeLoad[u] += 1;
                        if v not in dict_NodeLoad.keys():
                            dict_NodeLoad[v] = 0;
                        else:
                            dict_NodeLoad[v] += 1;
                            
        ## -- 2. Calculate the ObjVal based on LinkLoad.
        Ret_largest_linkCost = self.Get_max_value_of_a_dict(dict_LinkLoad);
        
        ## -- 3. Find the node which owns the largest holding rules based on dict_NodeLoad.
        Ret_largest_ruleCost = self.Get_max_value_of_a_dict(dict_NodeLoad);
                
        ### -- 3. Return them.
        return Ret_largest_linkCost,Ret_largest_ruleCost### --- End of this function :~    
    # ==========================================================================================
    # ==========================================================================================
    def Set_timer_for_one_CFlow(self,Src, Current_ts):
    
        pass##self.LogRun.write(  '\n  ####### Try to set timer for Src-CFlow[ %d ], at ts [ %s ]:'%(Src, Current_ts) )
        
        ### ===== A. rdmly select a NIU MBox for this traget-ClientFlow.
        feasible_DstMBox_rdm = self.Select_a_rdm_feasible_NIU_MBox_for_the_targetCFlow(Src);
        if (-1==feasible_DstMBox_rdm):
            return#### If -1 is returned: cannot find a feasible MBox for this Src, so, do nothing for it.
    
        ### ===== B. if the feasible Dst_MBox-sw is found, pick one path for this pair(Src, Dst).
        pass##self.LogRun.write(  '\n\t---- Src-CFlow[ %d ] finds out a feasible DstMBox[ %d ]\n'%(Src,feasible_DstMBox_rdm) )
    
        ### ===== (Rdmly/Greedly) Find a routing path for this SD-pair.
        Dst_new = feasible_DstMBox_rdm;
        # -- 1. Get the_current_selected_MBoxID_and_pathID_of_SrcCFlow, denoted as DstMBox_old and PathID_old;
        DstMBox_old,PathID_old = self.Get_the_current_selected_MBoxID_and_PathID_of_SrcCFlow(Src);
        
        # -- 2. Select one from |Js|-Ds its Not-in-Use paths, denoted as l_new;
        PathID_new = self.Get_a_rdm_pathID_NIU_from_CandidatePathSet(Src, Dst_new);
        
        # -- 3. Get the current Throughput before swapping the host-MBox and path;
        Throughput = self.Get_objVal_of_configurations_in_whole_system();
        
        # -- 4. Fake-Replace the host-MBox and Path, only for estimating the next-config-objVal.
        pass##self.LogRun.write( '\n\t  ####$$-- Fake_Replace, begin: Src[ %d ] - DstMBox_new[ %d ]\n'%(Src, Dst_new) )
        Throughput_predicted = self.Fake_Replace_DstMBox_and_Path_for_a_SrcCFlow_to_return_estimated_sysObj(Src, DstMBox_old, Dst_new, PathID_old, PathID_new);
        
        
        ## -- 5. generate an exponentially distributed random timer-value with
        ##       mean that is equal to (1/lambda_exp_random_number_seed), and record it into self.Timers.    
        # print 'Throughput: %f\tThroughput_predicted: %f'%(Throughput, Throughput_predicted)
        exp_item = math.exp(self.Tau - 0.5*self.Beta*(Throughput_predicted-Throughput));
        mean_timer_exp = 1.0*exp_item/(len(self.list_MBoxDst_id)-1);
        lambda_exp_random_number_seed = 1.0/mean_timer_exp;
        Timer_val_exp = random.expovariate( lambda_exp_random_number_seed );#### Generate a random exponentially-distibuted timer for the current Client-Flow.
        # print 'exp_item: %f\t lambda_exp: %f\t Timer_val_exp: %f'%(exp_item, lambda_exp_random_number_seed, Timer_val_exp)
        
        ### For debuging :
        # if DstMBox_old < 0:
            # pass##self.LogRun.write(  '\n\t\t--NOTE-- when DstMBox_old =-1:\n\t\t\tSrc-CFlow[ %d ] -Throughput[ %s ] -Throughput_predicted[ %s ] -lambda_exp_random_number_seed[ %s ] -Timer_val_exp[ %s ]\n'%(Src,Throughput,Throughput_predicted,lambda_exp_random_number_seed,Timer_val_exp) )
        ### For debuging :~
        
        ## -- 6. Record the necessary information into self.Timers.
        DstMBox_current = DstMBox_old;
        if (Src) not in self.Timers.keys():    ### --- Record 6-items information for this Src.
            self.Timers[Src] = [0,0,-1,-1,-1,-1];### Initialization
            self.Timers[Src][0] = Current_ts;
            self.Timers[Src][1] = Timer_val_exp
            self.Timers[Src][2] = PathID_old
            self.Timers[Src][3] = PathID_new
            self.Timers[Src][4] = DstMBox_current
            self.Timers[Src][5] = Dst_new
        else:    ### !!!! Do not forget updating the relevant paths-info when this Src has already been exiting.
            self.Timers[Src][0] = Current_ts;
            self.Timers[Src][1] = Timer_val_exp
            self.Timers[Src][2] = PathID_old
            self.Timers[Src][3] = PathID_new
            self.Timers[Src][4] = DstMBox_current
            self.Timers[Src][5] = Dst_new# --- End of this function :~
    # ==========================================================================================
    def Set_timer_for_all_CFlows(self,Current_ts):
        for Src in self.list_CFlowSrc_id:
            self.Set_timer_for_one_CFlow(Src, Current_ts)# --- End of this function :~
    # ==========================================================================================
    def RESET(self,Current_ts):
        self.Set_timer_for_all_CFlows(Current_ts)# --- End of this function :~
    # ==========================================================================================
    # ==========================================================================================
    def Replace_the_selected_DstMBox_and_Path_for_a_SrcCFlow(self,Src, Dst_old, Dst_new, PathID_old, PathID_new):
        #global self.PathSet_selected
        #### !!!!! ===== 1. Swap the Dst_MBoxes for CFlow: Remove the OLD MBox, Add the NEW.
        self.MBox_removes_a_CFlow( Dst_old, Src );
        self.MBox_trys_to_host_a_CFlow( Dst_new, Src );
        
        #### !!!!! ===== 2. Adopt the NEW path for Src.
        #### !!!!! ===== 2.1 Remove all the OLD paths for Src.
        for (SrcCF,DstMB) in self.PathSet_selected.keys():
            if SrcCF == Src:
                del self.PathSet_selected[(SrcCF,DstMB)];        ##此处为什么要删除
        
        #### !!!!! ===== 2.2 Adopt the NEW path for Src.
        #### -------- !! Before using the new-path, check whether it is feasible to this Src_CFlow.
        #### ---- if it is not feasible: this SrcCFlow will not have a routing-path!!
        bool_whether_this_new_path_is_feasible = self.Check_whether_this_new_path_is_feasible_to_the_SrcCFlow(Src,Dst_new,PathID_new);
        if 1==bool_whether_this_new_path_is_feasible:
            ### !!!! --- 2.2.1 Check whether this key exists.
            if (Src,Dst_new) not in self.PathSet_selected.keys():
                self.PathSet_selected[(Src,Dst_new)] = [];                ##self.PathSet_selected???????
            ### !!!! --- 2.2.2 Adopt this one.
            #print "test begin4"
            #print "PathID_new"+"  "+PathID_new+"\n"
            #print "PathID_new not in self.PathSet_selected[(Src,Dst_new)]"+"  "+PathID_new not in self.PathSet_selected[(Src,Dst_new)]
            if PathID_new>=0 and (PathID_new not in self.PathSet_selected[(Src,Dst_new)]):
                #print "test bedin3"
                self.PathSet_selected[(Src,Dst_new)].append(PathID_new)
                #print "test end3"
            #print "test end4"
        #### !!!!! ===== 2.3 Filter and Delete irregular path-items.
        for (SrcCF,DstMB) in self.PathSet_selected.keys():
            Host_DstMB_of_this_SrcCF = self.find_holding_MBox_of_a_SrcCFlow(SrcCF);
            if (DstMB != Host_DstMB_of_this_SrcCF):
                del self.PathSet_selected[(SrcCF,DstMB)]### --- End of this function :~
        
    # ==========================================================================================
                
    # ==========================================================================================
    def Delete_expired_timer_items_after_replacement(self,Src_CFlow):
        #global self.Timers;
        if Src_CFlow in self.Timers.keys():
            del self.Timers[Src_CFlow]### --- End of this function :~
    # ==========================================================================================
    # ==========================================================================================
    ##### In this function, I only check the link bandwidth is feasible or not.

    def Check_whether_this_new_path_is_feasible_to_the_SrcCFlow(self,Src,Dst_new,Path_ID_new):
        ##(0 is false, 1 is true)
        #self.Log_debug.write("\n\t ============ !!! In Check_whether_this_new_path Function, ---- Path_ID_new"+" "+str(Path_ID_new))

        if Path_ID_new<0:
            return 0

    	#self.f1.write("\n Location 333333333333333 \n")
        ## --- 1. get all the traversing arcs in the new path.
        list_arcs_in_this_path = self.Get_all_arcs_in_a_specified_path( Path_ID_new );    
        #self.Log_debug.write("\n\tlist_arcs_in_this_path"+" "+str(list_arcs_in_this_path)+"\n" )

        ## --- 2. calculate all the currently-accumulative-assigned TrafficRate(TR) in each traversed arc.
	#self.Log_debug.write("\n\t ----- location 0 \n" )
    	#self.f1.write("\n Location 6666666666666 \n")

	## --- 2.1 Check the traffic-rate in each arc of this path.
	for (u,v) in list_arcs_in_this_path:
		available_TR_in_uv = 0.0
		summed_TR_in_uv = 0.0###Initialized to 0.
	   	## -- 2.1.1 Get the available-tr-in-uv in the simulation-manner.(2016-01-27)
        	if (1 == self.Style_of_throughput_by_simulation_or_Mininet):
		   	## 2.1.1.1 summate all the traffic-rate in (u,v).			
			#self.f1.write("\n Location 77777777777 \n")
			for key,val in self.PathSet_selected.items():
				#self.f1.write("\n Location 77777777777-2222 \n")
				src = key[0]
				if (len(val)>0):
					for idx_pathID in range(0, len(val)):
						path_IU_sdi = val[idx_pathID];
						#self.Log_debug.write("\n\t ----- location 1 \n" )
						list_arcs_in_path_sdi = self.Get_all_arcs_in_a_specified_path( path_IU_sdi );
						#self.Log_debug.write("\n\t ----- location 2 \n" )
						if (u,v) in list_arcs_in_path_sdi:
							summed_TR_in_uv += self.TDSet[src];

		   	## 2.1.1.2 get the available_TR_in_uv.
            		available_TR_in_uv = self.Cap_links[(u,v)] - summed_TR_in_uv;## This is the simulation-style.
            		self.Log_debug.write("\t------------- 2.1.1.2 summed_TR_in_uv_estimated_in_simulation: "
					+ str(summed_TR_in_uv)+"\n")
            		self.Log_debug.flush()

        	## -- 2.1.1-ver2: Get the available-tr-in-uv in the emulation(mininet-running)-manner.(2016-01-27)
        	elif (0 == self.Style_of_throughput_by_simulation_or_Mininet):
			summed_TR_in_uv = self.objNetworkMonitor.get_used_bw(u,v);
			available_TR_in_uv = self.Cap_links[(u,v)] - summed_TR_in_uv;
			self.Log_debug.write("\t------------- 2.1.1-ver2 summed_TR_in_uv_measured_in_mininet: "
						+ str(summed_TR_in_uv)+"\n")
			self.Log_debug.flush()
		## -- 2.1.2 Compare the available TR bandwidth in each arc with the demanding TR of this Src_CFlow.
		demanding_TR_of_SrcCFlow = self.TDSet[Src];
		if ( demanding_TR_of_SrcCFlow > available_TR_in_uv ):
			return 0### Cannot statisfy this SrcCFlow, return false.

        ## --- 3. If all arcs in this path can satisfy this SrcCFlow, return 1(Yes).
    	#self.f1.write("\n Location 8888888888888 \n")
	return 1
    ### --- End of this function :~
    # ==========================================================================================
    
    # ==========================================================================================
    ## This function is for estimating the throughput-performance of the "next" state, if swap a pair of paths(one In-Use(IU) path and one Not-In-Use(NIU) path).
    def Fake_Replace_DstMBox_and_Path_for_a_SrcCFlow_to_return_estimated_sysObj(self,Src, DstMBox_old, Dst_new, PathID_old, PathID_new):    
        # -- 1. Fake-Replace the host-MBox and Path, only for estimating the next-config-objVal.
        self.Replace_the_selected_DstMBox_and_Path_for_a_SrcCFlow(Src, DstMBox_old, Dst_new, PathID_old, PathID_new);
        # -- 2. ESTIMATE the Throughput' after swapping the host-MBox and path;
        estimated_sysObj = self.Get_objVal_of_configurations_in_whole_system();    
        # -- 3. Swap-BACK of the host-MBox and Path, after estimating the next-config-objVal.
        self.Replace_the_selected_DstMBox_and_Path_for_a_SrcCFlow(Src, Dst_new, DstMBox_old, PathID_new, PathID_old);
        return estimated_sysObj# --- End of this function :~
    # ==========================================================================================
    
    # ==========================================================================================
    def Get_all_arcs_in_a_specified_path(self, path_id ):
        retlist_Arcs = [];    ## [ arcs_(u,v) in this path]
        
        ## -- 1. Analyse and record all arc-links in this path.
        if path_id in self.Paths_set.keys():
            list_path_content = self.Paths_set[path_id];            
            ## -- 1.1 ## Analyze all arcs in this path.    
            for node_idx in range(len(list_path_content)):
                if (node_idx+1) < len(list_path_content):
                    u = list_path_content[node_idx];
                    v = list_path_content[node_idx+1];        
                    ## -- 1.2 ## Record this arcs_list into retList.
                    if (u,v) not in retlist_Arcs:
                        retlist_Arcs.append((u,v));
        ## -- 2. Return the obtained linksSet in this path.
        return retlist_Arcs## --- End of this function :~    
    # ==========================================================================================
        
    # ==========================================================================================
    def Get_all_arcs_in_each_path_from_given_pathSet(self, dictPathSet ):
        #### ------ Get all the arcs in given dictPathSet.
        retDict_Arcs_in_each_Path = {};    ## {(Src,Dst, path_id):[ arcs_(u,v) in this path] }, the arcs in path-set for all pairs.    
        ## -- 1. Analyse each selected-path in val, get and record all arc-links in this path.
        for key,val in dictPathSet.items():
            Src = key[0]
            Dst = key[1]
            for idx_pathID in range(0, len(val)):
                path_id = val[idx_pathID];
                listPath_i = self.Paths_set[path_id];
                
                ## -- 1.1 ## Record all arcs in this path.    
                for node_idx in range(len(listPath_i)):
                    if (node_idx+1) < len(listPath_i):
                        u = listPath_i[node_idx];
                        v = listPath_i[node_idx+1];        
                        ## -- 1.1.2 ## Record this arcs_list into retDict.
                        if (Src,Dst,path_id) not in retDict_Arcs_in_each_Path.keys():
                            retDict_Arcs_in_each_Path[(Src,Dst,path_id)] = [];
                            retDict_Arcs_in_each_Path[(Src,Dst,path_id)].append((u,v));
                        else:
                            retDict_Arcs_in_each_Path[(Src,Dst,path_id)].append((u,v));
        ## -- 2. Return the obtained linksSet in each path.
        return retDict_Arcs_in_each_Path## --- End of this function :~            
    # ==========================================================================================
    def Whether_the_given_arc_in_this_ArcSetOfAPath(self, pairGivenArc, listArcs_in_a_path ):
        ret_status = 0;    ## 0: no; 1:yes.
        for arc in listArcs_in_a_path:
            if arc[0]==pairGivenArc[0] and arc[1]==pairGivenArc[1]:    ## (u,v) == (u,v)
                return 1;
        return ret_status## --- End of this function :~    
    # ==========================================================================================
    def Remove_a_path_from_pathSet(self, path_id, pathSet, key_in_pathSet ):
        pathSet[key_in_pathSet].remove(path_id)## --- End of this function :~    
    # ==========================================================================================
    
    # ==========================================================================================
    def Call_and_record_system_performance(self, current_ts, step_times, Cumulative_RESET_times, Cumulative_TimerExpiration_times):
        #### --- 1. Get the global system utility.
        Throughput = self.Get_objVal_of_configurations_in_whole_system();
        
        #### --- 2. Get the largest link utility.
        Largest_link_utility = 0;
        Largest_node_utility = 0;
        Largest_link_utility,Largest_node_utility = self.Get_largest_utility_of_both_links_and_nodes();
        
        #### --- 3. Get the largest node utility.
        #### --- Last. Record them together.
        self.Log.write('-ts\t%f\t-steps\t%d\t-Throughput\t%f\t-CNT_reset\t%d\t-CNT_TimerExpiration\t%d\t-MaxLinkCost\t%f\t-MaxNodeCost\t%f\t-self.Beta\t%s\n'%(current_ts, step_times, Throughput, Cumulative_RESET_times, Cumulative_TimerExpiration_times, Largest_link_utility, Largest_node_utility,self.Beta ))# --- End of this function :~
    # ==========================================================================================
    
    # ==========================================================================================
    def Write_down_the_current_solution_MBox_Path_assignment(self, Current_ts ):
    
        Throughput = self.Get_objVal_of_configurations_in_whole_system();
                
        self.LogRun.write(  '\n\t ==================== Solutions at -current-TS[ %s ] -Throughput[ %s ] ==================== \n'%(Current_ts,Throughput))
        ### ---- 1. Solution of Middle-box
        self.LogRun.write('#### MiddleBox-id : [list of the assigned Src-ClientFlow-id]\n')
        for Mbox_ID in self.MBoxSet_assigned.keys():
            self.LogRun.write(  '\t\t  ~~~~ self.MBoxSet_assigned[ %s ]: %s \n'%(Mbox_ID, self.MBoxSet_assigned[Mbox_ID]) )
        
        ### ---- 2. Solution of Path selection
        self.LogRun.write('\n#### Src-ClientFlow-id, DstMiddleBox-id : selected-path-id\n')
        #print self.PathSet_selected.keys    ##by gzq
        #print self.PathSet_selected.items ##by gzq
        #print self.PathSet_selected.values ##by gzq
        for key,val in self.PathSet_selected.items():
            SrcCF = key[0]
            DstMB = key[1]
            listPath = val
            self.LogRun.write(  '\t\t  ~~~~ SrcCF[ %s ] DstMB[ %s ]: %s \n'%(SrcCF,DstMB,listPath ) )
    # ==========================================================================================
    def Record_final_result(self,current_ts, step_times, Cumulative_RESET_times, Cumulative_TimerExpiration_times):
        #global  self.PathSet_selected
        #### --- 1. Get the global system utility.
        Throughput = self.Get_objVal_of_configurations_in_whole_system();
        
        #### --- 2. Get the largest link/node utility.
        Largest_link_utility = 0;
        Largest_node_utility = 0;
        Largest_link_utility,Largest_node_utility = self.Get_largest_utility_of_both_links_and_nodes();
        
        #### --- 3. Record them together.
        ###### ---- 3.1 calculate the Qos-Satisfication-Ratio (QSR) over all ClientFlows (TDs)
        TotalNum_TDs = len(self.TDSet);
        Num_satisfied_TDs = 0;
        for val in self.PathSet_selected.values():
            if len(val) > 0 and val[0] >= 0:
                Num_satisfied_TDs += 1;
        QSR = (1.0*Num_satisfied_TDs)/TotalNum_TDs;
        ###### ---- 3.2 record them all
        #self.Log_final_result.write('-ts\t%f\t-steps\t%d\t-Throughput\t%f\t-CNT_reset\t%d\t-CNT_TimerExpiration\t%d\t-MaxLinkCost\t%f\t-MaxNodeCost\t%f\t-self.Beta\t%s\t-QSR\t%f\t-CapLink\t%f\n'%(current_ts, step_times, Throughput, Cumulative_RESET_times, Cumulative_TimerExpiration_times, Largest_link_utility, Largest_node_utility,self.Beta,QSR,self.Cap_links["0000000000000003","0000000000000002"] ))# --- End of this function :~    
    # ==========================================================================================
    
    ##############################################################################################
    # ========================================= USE-CASE =========================================
     
