#coding=utf-8
'''
Created on 2015-12-21

@author: Guo Zhiqiang
'''

class NodeGraph ():
    nodegraph = {}
    nodes = []
    def __init__(self,nodes):
        self.nodes=nodes
        for k in self.nodes:
            self.nodegraph[k.id]=k   
    
        
class Node ():# host and switch node struct

  def __init__ (self,linkList=[],id=0):
    self.linkList = linkList[:]# nodes that linked with this node but not just Dpid or MAC
    self.id = id
    

  def deleteLink(self,id):
      self.Link.remove(id)
  def getid(self):
      return self.id
  def getalllink(self):
      print len(self.linkList)
      for k in self.linkList:
          print k

class Path ():#the path from src to dst 

  def __init__ (self):
    self.NodeList = []

  def addNode (self, node):
    self.NodeList.append(node)
  def getpathlen(self):
      return len(self.NodeList)
  def printpath(self):
      nodelist = []
      str = ""
      for k in self.NodeList:
        nodelist.append(k.getid())
        nodelist.append(">")
      nodelist.pop()
      nodelist.reverse()
      
      for j in nodelist:
          str = str + j
      #print str
      return str
      
  #def setSrcAndDst(self,sourceId,destId):
  #    self.sourceId = sourceId
  #    self.destId = destId
def getAllPath(sourceId,destId,nodes,graph):
  nodeStack = []
  pathes = []  
  nodeStack.append(graph.nodegraph[sourceId])
  pathes = findPath(nodeStack,graph.nodegraph[sourceId],destId,nodes,graph)
  #print pathes
  return pathes


  
def findPath(nodeStack,sourceNode,destId,nodes,graph):
  pathes = []
  path = Path()
  
  for l in sourceNode.linkList:
      if l == destId:
          for n in nodeStack:
              path.addNode(n)
          path.addNode(graph.nodegraph[l])
          pathes.append(path)
          ##nodeStack.pop()
          #return pathes
      elif not graph.nodegraph[l] in nodeStack:
          nodeStack.append(graph.nodegraph[l])
          pathes = pathes+findPath(nodeStack,graph.nodegraph[l],destId,nodes,graph)
      else: 
          pass
          
  if len(nodeStack):
    nodeStack.pop()        
  return pathes


 



