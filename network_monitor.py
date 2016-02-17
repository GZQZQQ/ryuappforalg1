from __future__ import division
from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet
import types
import threading
SLEEP_PERIOD = 10


class Network_Monitor(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _NAME = 'Network_Monitor'

    def __init__(self, *args, **kwargs):
        super(Network_Monitor, self).__init__(*args, **kwargs)
        
        self.datapaths = {}
        self.port_stats = {}
        self.port_speed = {}
        self.flow_stats = {}
        self.flow_speed = {}
        # {"port":{dpid:{port:body,..},..},"flow":{dpid:body,..}
        self.stats = {}
        self.port_link = {}  # {dpid:{port_no:(config,state,cur),..},..}
        self._linkinfodict = {}
        self.linkcurrentcapacity = {}
        self.myflow_stats = {}
        self.myflow_speed = {}
        self.monitor_thread = hub.spawn(self._monitor)
	#th1 = threading.Thread(target = self._monitor) 
	#th1.start() 
        
        self.dbugfile = open("monitordebug.txt",'w')
	self.dbugfile1 = open("network_monitor_debugflie.txt",'w')
    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
	i = 0
	isfirsttimecreate = True
        while True:
            self.stats['flow'] = {}
            self.stats['port'] = {}
            for dp in self.datapaths.values():
                self.port_link.setdefault(dp.id, {})
                self._request_stats(dp)
            hub.sleep(SLEEP_PERIOD)
	    self.dbugfile1.write("hub sleep 10s end\n")
	    self.dbugfile1.flush()
	    if self.stats['flow'] or self.stats['port']:
		self.dbugfile1.write("self.stats['flow'] and self.stats['port'] is not null \n")
		#self.dbugfile1.write("self.stats['flow']"+str(self.stats['flow'])+"\n")
		#self.dbugfile1.flush()		
		self.dbugfile1.write("flowspeed"+str(self.flow_speed)+"\n")
		self.dbugfile1.flush()
		self.dbugfile1.write("myflowspeed"+str(self.myflow_speed)+"\n")
		self.dbugfile1.flush()
                self.show_stat('flow', self.stats['flow'])
		self.dbugfile1.write("flow stat is show\n")
		self.dbugfile1.flush()	
                self.show_stat('port', self.stats['port'])
		self.dbugfile1.write("port stat is show\n")
		self.dbugfile1.flush()		
		hub.sleep(1)
	    else:
		self.dbugfile1.write("self.stats['flow'] and self.stats['port'] is  null \n")
		self.dbugfile1.flush()
	    
               

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        req = parser.OFPPortDescStatsRequest(datapath, 0)
        datapath.send_msg(req)

    def _save_stats(self, dist, key, value, length):
        if key not in dist:
            dist[key] = []
        dist[key].append(value)

        if len(dist[key]) > length:
            dist[key].pop(0)

    def _get_speed(self, now, pre, period):
        if period:
            return (now - pre) / (period)
        else:
            return 0

    def _get_time(self, sec, nsec):
        return sec + nsec / (10 ** 9)

    def _get_period(self, n_sec, n_nsec, p_sec, p_nsec):
        return self._get_time(n_sec, n_nsec) - self._get_time(p_sec, p_nsec)

    def show_stat(self, type, bodys):
        '''
            type: 'port' 'flow'
            bodys: port or flow `s information :{dpid:body}
        '''
        if(type == 'flow'):

            print('datapath         ''   in-port        ip-dst      '
                  'out-port packets  bytes  flow-speed(B/s)')
            print('---------------- ''  -------- ----------------- '
                  '-------- -------- -------- -----------')
            for dpid in bodys.keys():
                for stat in sorted([flow for flow in bodys[dpid]
                                    if flow.priority == 1],
                                   key=lambda flow: (flow.match['in_port'],
						     flow.match.get('ipv4_src'),
                                                     flow.match.get('ipv4_dst'))):
		    self.dbugfile1.write("location 6\n")
		    self.dbugfile1.flush()	
                    print('%016x %8x %17s %8x %8d %8d %8.1f' % (
                        dpid,
                        stat.match['in_port'], stat.match.get('ipv4_dst'),
                        stat.instructions[0].actions[0].port,
                        stat.packet_count, stat.byte_count,
                        abs(self.flow_speed[dpid][
                            (stat.match['in_port'],
			     stat.match.get('ipv4_src'),
                            stat.match.get('ipv4_dst'),
                            stat.instructions[0].actions[0].port)][-1])))
                    
            print '\n'
	    self.dbugfile1.write("flow stat han shu is end\n")
	    self.dbugfile1.flush()	
        if(type == 'port'):
            print('datapath             port   ''rx-pkts  rx-bytes rx-error '
                  'tx-pkts  tx-bytes tx-error  port-speed(B/s)'
                  ' current-capacity(Kbps)  '
                  'port-stat   link-stat')
            print('----------------   -------- ''-------- -------- -------- '
                  '-------- -------- -------- '
                  '----------------  ----------------   '
                  '   -----------    -----------')
            format = '%016x %8x %8d %8d %8d %8d %8d %8d %8.1f %16d %16s %16s'
            for dpid in bodys.keys():
                for stat in sorted(bodys[dpid], key=attrgetter('port_no')):
                    if stat.port_no != ofproto_v1_3.OFPP_LOCAL:
                        print(format % (
                            dpid, stat.port_no,
                            stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                            stat.tx_packets, stat.tx_bytes, stat.tx_errors,
                            abs(self.port_speed[(dpid, stat.port_no)][-1]),
                            self.port_link[dpid][stat.port_no][2],
                            self.port_link[dpid][stat.port_no][0],
                            self.port_link[dpid][stat.port_no][1]))
		    
                        
    def get_used_bw(self,u,v):		
	f1 = open("_linkinfodict.txt",'r')
        str_linkinfodict = f1.read()
        self._linkinfodict =eval(str_linkinfodict)
		
	u = str(u)
	v = str(v)
	
	for key in self._linkinfodict.keys():
	    if(u==key[0] and v==key[1]):
	       port = self._linkinfodict[(u,v)][0]
	port = int(port)
			
	
	truedpid = 0
	try:
	    truedpid = int(u)
	except Exception , e:
	    truedpid = int(v)
	    try:
	       truedpid = int(v)
	    except Exception , e:
	       truedpid = int(v)
	portSpeed = abs(self.port_speed[(truedpid, port)][-1]);
	Speed_in_Mbit_per_second = float(portSpeed*8) / (1048576);## bytes/s -> Mbits/s.
	return Speed_in_Mbit_per_second## End of function :~

    def caltotalthroughput(self,pathselected,pathset):   ##pathselected/pathset are  the pathselected/pathset of alg1
	f2 = open("_linkinfodict.txt",'r')
        str_linkinfodict = f2.read()
        self._linkinfodict =eval(str_linkinfodict)
	caltotalthroughput = float(0)
	for key in pathselected.keys():
	    path_list = []
	    path_list = pathset[int(pathselected[key][0])]
	    i = 0
	    ## --- a. get the maxflowrate over the current pathlist
	    maxflowrate = float(0)
	    while(i<len(path)-1):
                inport = int(self._linkinfodict[path[i],path[i+1]][1])
                outport = int(self._linkinfodict[path[i+1],path[i+2]][0])
                if (inport,key[0],key[1],outport) in self.myflow_speed.keys():
                    flowrate = abs(self.myflow_speed[int(path[i+1])][(inport,key[0],key[1],outport)][-1])
                    if(flowrate > maxflowrate):
                        maxflowrate = flowrate

	    ## --- b. sum this maxflowrate
	    caltotalthroughput = caltotalthroughput + maxflowrate
		
	throughput_in_Mbit_per_second = float(caltotalthroughput*8) / (1048576);## bytes/s -> Mbits/s.
	return throughput_in_Mbit_per_second## End of function :~


    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        #self.stats['flow'][ev.msg.datapath.id] = body
	dpid = ev.msg.datapath.id
        self.stats['flow'][dpid] = body
        self.flow_stats.setdefault(dpid, {})
        self.flow_speed.setdefault(dpid, {})
	self.dbugfile1.write("body  "+str(body)+"\n")
        self.dbugfile1.flush()
	    
        for stat in sorted(
			   [flow for flow in body if flow.priority == 1 or  flow.priority == 10 ],
                           key=lambda flow: (flow.match['in_port'],
					     flow.match.get('ipv4_src'),
                                             flow.match.get('ipv4_dst'))):
	    self.dbugfile1.write("stat:"+str(stat)+"\n")
	    self.dbugfile1.flush()
	    
            key = (stat.match['in_port'],stat.match.get('ipv4_src'),stat.match.get('ipv4_dst'),
                   stat.instructions[0].actions[0].port)
            value = (stat.packet_count, stat.byte_count,
                    stat.duration_sec, stat.duration_nsec)
            self._save_stats(self.flow_stats[dpid], key, value, 5)
            # Get flow's speed.
            pre = 0
            period = SLEEP_PERIOD
            tmp = self.flow_stats[dpid][key]
            if len(tmp) > 1:
                pre = tmp[-2][1]
                period = self._get_period(tmp[-1][2], tmp[-1][3],
                                         tmp[-2][2], tmp[-2][3])
            speed = self._get_speed(

                self.flow_stats[dpid][key][-1][1], pre, period)

            self._save_stats(self.flow_speed[dpid], key, speed, 5)
	self.dbugfile1.write("PFlowStatsReply not end\n")
        self.dbugfile1.flush()	
##############################################################################################################################################
	
	for mystat in sorted([flow for flow in body if flow.priority == 10],
                           key=lambda flow: (flow.match['in_port'],
					     flow.match.get('ipv4_src'),
                                             flow.match.get('ipv4_dst'))):
 	    self.dbugfile1.write("location 1\n")
            self.dbugfile1.flush()
            mykey = (
                mystat.match['in_port'], mystat.match.get('ipv4_src'),  mystat.match.get('ipv4_dst'),
                mystat.instructions[0].actions[0].port)
	    self.dbugfile1.write("locaton 2\n")
            self.dbugfile1.flush()
            myvalue = (
                mystat.packet_count, mystat.byte_count,
                mystat.duration_sec, mystat.duration_nsec)
	    self.dbugfile1.write("location 3\n")
            self.dbugfile1.flush()
            self._save_stats(self.myflow_stats[dpid], mykey, myvalue, 5)
	    self.dbugfile1.write("location 4 \n")
            self.dbugfile1.flush()
	    mypre = 0
            myperiod = SLEEP_PERIOD
            mytmp = self.myflow_stats[dpid][mykey]
            if len(tmp) > 1:
                  mypre = mytmp[-2][1]
                  myperiod = self._get_period(
                       mytmp[-1][2], mytmp[-1][3],
                       mytmp[-2][2], mytmp[-2][3])
	    self.dbugfile1.write("location 5\n")
            self.dbugfile1.flush()
            myspeed = self._get_speed(
                    self.myflow_stats[key][-1][1], mypre, myperiod)
	    self.dbugfile1.write("location 5\n")
            self.dbugfile1.flush()
            self._save_stats(self.myflow_speed[dpid], mykey, myspeed, 5)
	self.dbugfile1.write("PFlowStatsReply end\n")
        self.dbugfile1.flush()	   
###############################################################################################################################################
####test self.myflowspeed
	"""
	for mystat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
					     
                                             flow.match.get('ipv4_dst'))):
            mykey = (
                mystat.match.get['in_port'],  mystat.match.get('ipv4_dst'),
                mystat.instructions[0].actions[0].port)
            myvalue = (
                mystat.packet_count, mystat.byte_count,
                mystat.duration_sec, mystat.duration_nsec)
            self._save_stats(self.myflow_stats[dpid], mykey, myvalue, 5)

	    mypre = 0
            myperiod = SLEEP_PERIOD
            mytmp = self.myflow_stats[dpid][mykey]
            if len(tmp) > 1:
                  mypre = mytmp[-2][1]
                  myperiod = self._get_period(
                       mytmp[-1][2], mytmp[-1][3],
                       mytmp[-2][2], mytmp[-2][3])

            myspeed = self._get_speed(
                    self.myflow_stats[dpid][key][-1][1], mypre, myperiod)

            self._save_stats(self.myflow_speed[dpid], mykey, myspeed, 5)	
	    """
###############################################################################################################################################


    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        self.stats['port'][ev.msg.datapath.id] = body
	#self.dbugfile1.write("self.stats['port'] is got vaule"+"\n") 
        for stat in sorted(body, key=attrgetter('port_no')):
            if stat.port_no != ofproto_v1_3.OFPP_LOCAL:
                key = (ev.msg.datapath.id, stat.port_no)
                value = (stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                         stat.duration_sec, stat.duration_nsec)
                self._save_stats(self.port_stats, key, value, 5)

                # Get port speed.
                pre = 0
                period = SLEEP_PERIOD
                tmp = self.port_stats[key]
                if len(tmp) > 1:
                    pre = tmp[-2][0] + tmp[-2][1]
                    period = self._get_period(tmp[-1][3], tmp[-1][4],
                                             tmp[-2][3], tmp[-2][4])
                speed = self._get_speed(
                    self.port_stats[key][-1][0] + self.port_stats[key][-1][1],
                    pre, period)

                self._save_stats(self.port_speed, key, speed, 5)

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        msg = ev.msg
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        config_dist = {ofproto.OFPPC_PORT_DOWN: "Down",
                       ofproto.OFPPC_NO_RECV: "No Recv",
                       ofproto.OFPPC_NO_FWD: "No Farward",
                       ofproto.OFPPC_NO_PACKET_IN: "No Packet-in"}

        state_dist = {ofproto.OFPPS_LINK_DOWN: "Down",
                      ofproto.OFPPS_BLOCKED: "Blocked",
                      ofproto.OFPPS_LIVE: "Live"}

        ports = []
        for p in ev.msg.body:
            ports.append('port_no=%d hw_addr=%s name=%s config=0x%08x '
                         'state=0x%08x curr=0x%08x advertised=0x%08x '
                         'supported=0x%08x peer=0x%08x curr_speed=%d '
                         'max_speed=%d' %
                         (p.port_no, p.hw_addr,
                          p.name, p.config,
                          p.state, p.curr, p.advertised,
                          p.supported, p.peer, p.curr_speed,
                          p.max_speed))

            if p.config in config_dist:
                config = config_dist[p.config]
            else:
                config = "up"

            if p.state in state_dist:
                state = state_dist[p.state]
            else:
                state = "up"

            port_feature = (config, state, p.curr_speed)
            self.port_link[dpid][p.port_no] = port_feature

        #self.logger.debug('OFPPortDescStatsReply received: %s', ports)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        reason_dict = {ofproto.OFPPR_ADD: "added",
                       ofproto.OFPPR_DELETE: "deleted",
                       ofproto.OFPPR_MODIFY: "modified", }

        if reason in reason_dict:
            print "switch%d: port %s %s" % (dpid, reason_dict[reason], port_no)
        else:
            print "switch%d: Illeagal port state %s %s" % (port_no, reason)
