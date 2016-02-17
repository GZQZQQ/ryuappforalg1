from mininet.topo import Topo


class MyTopo(Topo):
    "Simple loop topology example."
 
    def __init__(self):
        "Create custom loop topo."
 
        # Initialize topology
        Topo.__init__(self)
 
        # Add hosts 
        host1 = self.addHost('h1', ip='10.0.0.1')
        host2 = self.addHost('h2', ip='10.0.0.2')
        host3 = self.addHost('h3', ip='10.0.0.3')
        host4 = self.addHost('h4', ip='10.0.0.4')
        host5 = self.addHost('h5', ip='10.0.0.5')
        host6 = self.addHost('h6', ip='10.0.0.6')
        host7 = self.addHost('h7', ip='10.0.0.7')
        host8 = self.addHost('h8', ip='10.0.0.8')
        host9 = self.addHost('h9', ip='10.0.0.9')
        host10 = self.addHost('h10', ip='10.0.0.10')

        # Add switches
        switch1 = self.addSwitch("s1")
        switch2 = self.addSwitch("s2")
        switch3 = self.addSwitch("s3")
        switch4 = self.addSwitch("s4")
        switch5 = self.addSwitch("s5")
        switch6 = self.addSwitch("s6")
        switch7 = self.addSwitch("s7")
        switch8 = self.addSwitch("s8")

        # ======================= Add links
	## initialize some critical parameters
	Cap_links = 0;#expected style: {<link_leftNode, link_rightNode>:cap_val, ...}, but now(2016-01-23) we still read the uniform Cap_links.

	# --- read parameters from input_file
        InputFile_para_setting = open("A_manually_input_para_settings.txt",'r')
        str_para_setting = InputFile_para_setting.read()
        InputFile_para_setting.close()
        dict_para_setting = eval(str_para_setting)   
        #print 'dict_para_setting: %s '%dict_para_setting     
	for key,val in dict_para_setting.items():

            if str(key)=='linkCap':
            	Cap_links = int(val)# get the cap_links
            	#print 'Cap_links: %d '%Cap_links

	# ---------- add links for switch<-->switch
        self.addLink(switch1, switch2, 2, 2, bw=Cap_links)
        self.addLink(switch1, switch3, 3, 1, bw=Cap_links)
        self.addLink(switch2, switch3, 3, 2, bw=Cap_links)
        self.addLink(switch2, switch5, 4, 1, bw=Cap_links)
        self.addLink(switch3, switch4, 3, 3, bw=Cap_links)
        self.addLink(switch4, switch6, 4, 4, bw=Cap_links)
        self.addLink(switch4, switch8, 2, 3, bw=Cap_links)
        self.addLink(switch5, switch6, 2, 2, bw=Cap_links)
        self.addLink(switch6, switch7, 3, 3, bw=Cap_links)
        self.addLink(switch7, switch8, 2, 2, bw=Cap_links)
        
 
        
        # ---------- add links for switch<-->host
        self.addLink(switch1, host1, 1, bw=Cap_links)
        self.addLink(switch2, host2, 1, bw=Cap_links)
        self.addLink(switch7, host5, 1, bw=Cap_links)
        self.addLink(switch8, host6, 1, bw=Cap_links)
        self.addLink(switch3, host7, 4, bw=Cap_links)
        self.addLink(switch5, host8, 3, bw=Cap_links)
        self.addLink(switch7, host9, 4, bw=Cap_links)
        self.addLink(switch8, host10, 4, bw=Cap_links)
	
	# ---------- add links for switch <--> middlebox
        self.addLink(switch4, host3, 1, bw=Cap_links)
        self.addLink(switch6, host4, 1, bw=Cap_links)

 
topos = {'mytopo': (lambda: MyTopo())}
